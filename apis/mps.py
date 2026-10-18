from logging import info
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File, Request
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from typing import Optional
from core.auth import get_current_user_or_ak
from core.db import DB
from core.wx import search_Biz
from driver.wx import Wx
from .base import success_response, error_response
from datetime import datetime
from core.config import cfg
from core.res import save_avatar_locally
from core.models.feed import FEATURED_MP_ID, FEATURED_MP_NAME, FEATURED_MP_INTRO
from core.models.base import DATA_STATUS
from core.cache import clear_cache_pattern
import io
import os
from jobs.article import UpdateArticle
from driver.wxarticle import WXArticleFetcher
import threading
from uuid import uuid4
router = APIRouter(prefix=f"/mps", tags=["公众号管理"])
# import core.db as db
# UPDB=db.Db("数据抓取")
# def UpdateArticle(art:dict):
#             return UPDB.add_article(art)


def build_featured_mp_item():
    now = datetime.now().isoformat()
    return {
        "id": FEATURED_MP_ID,
        "mp_name": FEATURED_MP_NAME,
        "mp_cover": "/static/logo.svg",
        "mp_intro": FEATURED_MP_INTRO,
        "status": 1,
        "created_at": now,
        "is_system": True
    }


_featured_article_tasks = {}
_featured_article_tasks_lock = threading.Lock()


def _set_featured_article_task(task_id: str, data: dict):
    with _featured_article_tasks_lock:
        _featured_article_tasks[task_id] = data


def _ensure_featured_feed(session):
    from core.models.feed import Feed

    featured_feed = session.query(Feed).filter(Feed.id == FEATURED_MP_ID).first()
    if featured_feed:
        return featured_feed

    now = datetime.now()
    featured_feed = Feed(
        id=FEATURED_MP_ID,
        mp_name=FEATURED_MP_NAME,
        mp_cover="",
        mp_intro=FEATURED_MP_INTRO,
        status=1,
        sync_time=0,
        update_time=0,
        created_at=now,
        updated_at=now,
        faker_id=FEATURED_MP_ID
    )
    session.add(featured_feed)
    return featured_feed


def _run_add_featured_article_task_wrapper(task_id: str, url: str):
    """包装器:在线程中运行 async 函数"""
    import asyncio
    asyncio.run(_run_add_featured_article_task(task_id, url))

async def _run_add_featured_article_task(task_id: str, url: str):
    session = DB.get_session()
    fetcher = None
    try:
        _set_featured_article_task(task_id, {
            "task_id": task_id,
            "url": url,
            "status": "running",
            "message": "任务执行中"
        })

        from core.models.article import Article

        target_url = str(url or "").strip()
        if not target_url:
            raise ValueError("请输入文章链接")

        fetcher = WXArticleFetcher()
        info = await fetcher.get_article_content(target_url)
        if not info or info.get("fetch_error"):
            raise ValueError(info.get("fetch_error") or "文章抓取失败，请检查链接或登录状态")

        if info.get("content") == "DELETED":
            raise ValueError("该文章暂不可访问或已删除")

        raw_article_id = info.get("id") or fetcher.extract_id_from_url(target_url)
        if not raw_article_id:
            raise ValueError("无法解析文章ID，请确认链接格式")

        _ensure_featured_feed(session)

        article_id = f"{FEATURED_MP_ID}-{raw_article_id}".replace("MP_WXS_", "")
        now = datetime.now()
        publish_time = info.get("publish_time")
        if not isinstance(publish_time, int):
            try:
                publish_time = int(publish_time)
            except Exception:
                publish_time = int(now.timestamp())

        article_data = {
            "title": info.get("title") or target_url,
            "description": info.get("description") or fetcher.get_description(info.get("content") or ""),
            "content": info.get("content") or "",
            "publish_time": publish_time,
            "url": target_url,
            "pic_url": info.get("topic_image") or info.get("pic_url") or "",
        }

        existing = session.query(Article).filter(Article.id == article_id).first()
        if existing:
            existing.mp_id = FEATURED_MP_ID
            existing.title = article_data["title"]
            existing.description = article_data["description"]
            existing.content = article_data["content"]
            existing.publish_time = article_data["publish_time"]
            existing.url = article_data["url"]
            existing.pic_url = article_data["pic_url"]
            existing.status = DATA_STATUS.ACTIVE
            existing.updated_at = int(now.timestamp())
            existing.updated_at_millis = int(now.timestamp() * 1000)
            created = False
        else:
            session.add(Article(
                id=article_id,
                mp_id=FEATURED_MP_ID,
                title=article_data["title"],
                description=article_data["description"],
                content=article_data["content"],
                publish_time=article_data["publish_time"],
                url=article_data["url"],
                pic_url=article_data["pic_url"],
                status=DATA_STATUS.ACTIVE,
                created_at=now,
                updated_at=int(now.timestamp()),
                updated_at_millis=int(now.timestamp() * 1000),
                is_read=0,
                is_favorite=0
            ))
            created = True

        session.commit()
        clear_cache_pattern("articles_list")
        clear_cache_pattern("article_detail")
        clear_cache_pattern("home_page")
        clear_cache_pattern("tag_detail")

        _set_featured_article_task(task_id, {
            "task_id": task_id,
            "url": target_url,
            "status": "success",
            "message": "精选文章添加成功" if created else "精选文章更新成功",
            "id": article_id,
            "mp_id": FEATURED_MP_ID,
            "mp_name": FEATURED_MP_NAME,
            "title": article_data["title"],
            "created": created
        })
    except Exception as e:
        session.rollback()
        _set_featured_article_task(task_id, {
            "task_id": task_id,
            "url": url,
            "status": "failed",
            "message": str(e)
        })
    finally:
        if fetcher is not None:
            try:
                await fetcher.Close()
            except Exception:
                pass
        session.close()


@router.get("/search/{kw}", summary="搜索公众号")
async def search_mp(
    kw: str = "",
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user_or_ak)
):
    try:
        result = search_Biz(kw,limit=limit,offset=offset)
        data={
            'list':result.get('list') if result is not None else [],
            'page':{
                'limit':limit,
                'offset':offset
            },
            'total':result.get('total') if result is not None else 0
        }
        return success_response(data)
    except Exception as e:
        print(f"搜索公众号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message=f"搜索公众号失败,请重新扫码授权！",
            )
        )

@router.get("", summary="获取公众号列表")
async def get_mps(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    status: int = Query(None, description="状态筛选: 1=启用, 0=停用, 不传=全部"),
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        query = session.query(Feed).filter(Feed.id != FEATURED_MP_ID)
        if kw:
            query = query.filter(Feed.mp_name.ilike(f"%{kw}%"))
        if status is not None:
            query = query.filter(Feed.status == status)
        total = query.count()
        mps = query.order_by(Feed.created_at.desc()).limit(limit).offset(offset).all()

        # 查询公众号对应的有效文章数
        mp_ids = [mp.id for mp in mps if mp.id]
        article_counts = {}
        if mp_ids:
            from sqlalchemy import func
            from core.models.article import ArticleBase
            counts = (
                session.query(ArticleBase.mp_id, func.count(ArticleBase.id))
                .filter(ArticleBase.mp_id.in_(mp_ids), ArticleBase.status != DATA_STATUS.DELETED)
                .group_by(ArticleBase.mp_id)
                .all()
            )
            article_counts = {item[0]: item[1] for item in counts}

        mps_list = [{
                "id": mp.id,
                "mp_name": mp.mp_name,
                "mp_cover": mp.mp_cover,
                "mp_intro": mp.mp_intro,
                "status": mp.status,
                "article_count": article_counts.get(mp.id, 0),
                "created_at": mp.created_at.isoformat() if mp.created_at else ""
            } for mp in mps]
        return success_response({
            "list": mps_list,
            "page": {
                "limit": limit,
                "offset": offset,
                "total": total
            },
            "total": total
        })
    except Exception as e:
        print(f"获取公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="获取公众号列表失败"
            )
        )
    finally:
        session.close()


@router.post("/featured/article", summary="添加精选文章")
async def add_featured_article(
    url: str = Body(..., embed=True, min_length=1),
    current_user: dict = Depends(get_current_user_or_ak)
):
    try:
        target_url = str(url or "").strip()
        if not target_url:
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail=error_response(
                    code=40001,
                    message="请输入文章链接"
                )
            )
        if "mp.weixin.qq.com/s/" not in target_url:
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail=error_response(
                    code=40002,
                    message="请输入有效的公众号文章链接"
                )
            )

        task_id = str(uuid4())
        _set_featured_article_task(task_id, {
            "task_id": task_id,
            "url": target_url,
            "status": "pending",
            "message": "任务已创建"
        })
        threading.Thread(
            target=_run_add_featured_article_task_wrapper,
            args=(task_id, target_url),
            daemon=True
        ).start()

        return success_response({
            "task_id": task_id,
            "url": target_url,
            "status": "pending"
        }, message="已开始添加/抓取，请稍后刷新查看结果")
    except HTTPException:
        raise
    except Exception as e:
        print(f"添加精选文章任务启动失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="添加精选文章失败"
            )
        )


@router.get("/featured/article/tasks/{task_id}", summary="查询精选文章添加任务状态")
async def get_featured_article_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    with _featured_article_tasks_lock:
        task = _featured_article_tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code=40404,
                message="任务不存在"
            )
        )
    return success_response(task)

@router.get("/update/{mp_id}", summary="更新公众号文章")
async def update_mps(
     mp_id: str,
     start_page: int = 0,
     end_page: int = 1,
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        mp = session.query(Feed).filter(Feed.id == mp_id).first()
        if not mp:
           return error_response(
                    code=40401,
                    message="请选择一个公众号"
                )
        import time
        sync_interval=cfg.get("sync_interval",60)
        if mp.update_time is None:
            mp.update_time=int(time.time())-sync_interval
        time_span=int(time.time())-int(mp.update_time)
        if time_span<sync_interval:
           return error_response(
                    code=40402,
                    message="请不要频繁更新操作",
                    data={"time_span":time_span}
                )
        # 同步采集，等待结果返回；失败时把真实原因透出给前端，
        # 避免「异步线程 + 异常被吞」导致前端只看到“刷新成功”但实际 0 篇入库。
        from core.wx import WxGather
        wx = WxGather().Model()
        try:
            wx.get_Articles(
                mp.faker_id,
                Mps_id=mp.id,
                Mps_title=mp.mp_name,
                CallBack=UpdateArticle,
                start_page=start_page,
                MaxPage=end_page,
            )
        except Exception as e:
            err = str(e)
            # 微信读书登录态失效等，给出可操作的明确提示
            hint = ""
            if any(k in err for k in ("401", "鉴权", "-2013", "-2012", "登录超时", "登录态")):
                hint = " 微信读书 Cookie 已失效，请到「微信读书管理」页重新扫码授权或更新 Cookie。"
            print(f"更新公众号文章失败 [{mp.mp_name}]: {err}")
            return error_response(
                code=50002,
                message=f"更新「{mp.mp_name}」失败: {err}{hint}",
                data={"mp_id": mp_id},
            )
        return success_response({
            "time_span":time_span,
            "list":wx.articles,
            "total":len(wx.articles),
            "mps":mp
        })
    except Exception as e:
        print(f"更新公众号文章: {str(e)}",e)
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message=f"更新公众号文章{str(e)}"
            )
        )
    finally:
        session.close()

@router.get("/{mp_id}", summary="获取公众号详情")
async def get_mp(
    mp_id: str,
    # current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        mp = session.query(Feed).filter(Feed.id == mp_id).first()
        if not mp:
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail=error_response(
                    code=40401,
                    message="公众号不存在"
                )
            )
        return success_response(mp)
    except Exception as e:
        print(f"获取公众号详情错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="获取公众号详情失败"
            )
        )
    finally:
        session.close()
async def _extract_mp_info_from_article_url(url: str) -> dict:
    """
    通过文章 URL 提取公众号信息：
    优先使用轻量高效的 HTTP GET 提取（秒级返回），提取不完整时降级到 WXArticleFetcher (Playwright)。
    """
    import httpx
    import re
    import html
    from urllib.parse import urlparse

    clean_url = (url or "").strip()
    if not clean_url:
        return {}

    # SSRF 防御与协议/域名白名单检查
    parsed = urlparse(clean_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not (
        hostname == "mp.weixin.qq.com" or hostname == "weixin.qq.com" or hostname.endswith(".weixin.qq.com")
    ):
        return {"fetch_error": "链接无效，必须为微信公众号文章链接 (以 https://mp.weixin.qq.com 开头)"}

    mp_info = {
        "mp_name": "",
        "biz": "",
        "logo": "",
        "title": ""
    }

    # 1. 优先尝试轻量 HTTP GET 解析元数据
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        # 代理空串保护：避免配置为空字符串时 httpx 抛出 Unknown scheme
        raw_proxy = cfg.get("proxy.http_url", "") if cfg.get("proxy.enabled", False) else None
        proxy_url = raw_proxy.strip() if (raw_proxy and isinstance(raw_proxy, str) and raw_proxy.strip()) else None

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, proxy=proxy_url) as client:
            resp = await client.get(clean_url, headers=headers)
            if resp.status_code == 200:
                resp_text = resp.text
                biz_m = (re.search(r'var\s+biz\s*=\s*["\']([^"\']+)["\']', resp_text) or
                         re.search(r'__biz=([^&"\'\s]+)', resp_text) or
                         re.search(r'data-biz=["\']([^"\']+)["\']', resp_text))
                if biz_m:
                    mp_info["biz"] = biz_m.group(1).strip()

                nick_m = (
                    re.search(r'var\s+nickname\s*=\s*(?:htmlDecode\s*\(\s*)?["\']([^"\']+)["\']', resp_text) or
                    re.search(r'nick_name\s*:\s*["\']([^"\']+)["\']', resp_text) or
                    re.search(r'id=["\']js_name["\'][^>]*>\s*([^<\s][^<]*?)\s*<', resp_text) or
                    re.search(r'id=["\']js_wx_follow_nickname[^"\']*["\'][^>]*>\s*([^<\s][^<]*?)\s*<', resp_text) or
                    re.search(r'class=["\'](?:[^"\']*\s+)?profile_nickname(?:\s+[^"\']*)?["\'][^>]*>\s*([^<\s][^<]*?)\s*<', resp_text) or
                    re.search(r'data-nickname=["\']([^"\']+)["\']', resp_text)
                )
                if nick_m:
                    # HTML 实体反转义保护（如 &amp; / &quot;）
                    mp_info["mp_name"] = html.unescape(nick_m.group(1).strip())
                else:
                    author_m = re.search(r'property=["\']og:article:author["\']\s+content=["\']([^"\']+)["\']', resp_text)
                    if author_m:
                        raw_author = html.unescape(author_m.group(1).strip())
                        blacklist = ["关注", "点击", "蓝字", "扫码", "订阅", "分享", "阅读", "原创", "微信", "公众号"]
                        if not any(k in raw_author for k in blacklist):
                            mp_info["mp_name"] = raw_author

                logo_m = (re.search(r'var\s+round_head_img\s*=\s*["\']([^"\']+)["\']', resp_text) or
                          re.search(r'class="wx_follow_avatar_pic"[^>]*src="([^"]+)"', resp_text) or
                          re.search(r'property="og:image"\s+content="([^"]+)"', resp_text))
                if logo_m:
                    mp_info["logo"] = logo_m.group(1).strip()

                title_m = (re.search(r'property="og:title"\s+content="([^"]+)"', resp_text) or
                           re.search(r'<title>([^<]+)</title>', resp_text))
                if title_m:
                    mp_info["title"] = html.unescape(title_m.group(1).strip())
    except Exception as e:
        print(f"[by_article] 轻量解析文章出错，准备降级到 Playwright: {e}")

    # 若轻量解析已经完整获取了 mp_name 和 biz，直接返回
    if mp_info["mp_name"] and mp_info["biz"]:
        return {
            "title": mp_info.get("title", ""),
            "mp_info": {
                "mp_name": mp_info["mp_name"],
                "logo": mp_info.get("logo", ""),
                "biz": mp_info["biz"]
            }
        }

    # 2. 降级到 WXArticleFetcher (Playwright)
    fetcher = None
    try:
        fetcher = WXArticleFetcher()
        info = await fetcher.get_article_content(clean_url)
        return info or {}
    except Exception as e:
        print(f"[by_article] Playwright 解析文章失败: {e}")
        return {}
    finally:
        if fetcher is not None:
            try:
                await fetcher.Close()
            except Exception:
                pass


@router.post("/by_article", summary="通过文章链接识别公众号并自动完成订阅")
async def get_mp_by_article(
    request: Request,
    url: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_or_ak)
):
    target_url = (url or "").strip()
    if not target_url:
        try:
            body = await request.json()
            if isinstance(body, dict):
                target_url = (body.get("url") or "").strip()
        except Exception:
            pass

    if not target_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code=40001,
                message="请输入公众号文章链接"
            )
        )

    # SSRF 防御与协议/域名白名单检查
    from urllib.parse import urlparse
    parsed = urlparse(target_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not (
        hostname == "mp.weixin.qq.com" or hostname == "weixin.qq.com" or hostname.endswith(".weixin.qq.com")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code=40001,
                message="请输入有效的微信公众号文章链接 (需以 https://mp.weixin.qq.com 开头)"
            )
        )

    session = DB.get_session()
    try:
        from core.models.feed import Feed
        import html

        info = await _extract_mp_info_from_article_url(target_url)
        if not info or info.get("fetch_error"):
            err_msg = info.get("fetch_error") if info else "文章抓取失败，请检查链接有效性"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40002,
                    message=f"文章识别失败: {err_msg}"
                )
            )

        mp_info = info.get("mp_info") or {}
        mp_name = html.unescape((mp_info.get("mp_name") or "").strip())
        biz = (mp_info.get("biz") or "").strip()
        logo = (mp_info.get("logo") or "").strip()

        if not mp_name or not biz:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40003,
                    message="未能在该文章页面中提取到公众号标识(biz)或名称"
                )
            )

        try:
            import base64
            mpx_id = base64.b64decode(biz).decode("utf-8")
        except Exception:
            mpx_id = biz

        feed_id = f"MP_WXS_{mpx_id}"
        local_avatar_path = f"{save_avatar_locally(logo)}" if logo else ""
        now = datetime.now()

        # 检查是否已订阅
        existing_feed = session.query(Feed).filter(
            (Feed.faker_id == biz) | (Feed.id == feed_id)
        ).first()

        created = False
        if existing_feed:
            feed = existing_feed
            feed.mp_name = mp_name
            if local_avatar_path:
                feed.mp_cover = local_avatar_path
            feed.status = 1  # 确保重新启用
            feed.updated_at = now
        else:
            new_feed = Feed(
                id=feed_id,
                mp_name=mp_name,
                mp_cover=local_avatar_path,
                mp_intro=mp_name,
                status=1,
                created_at=now,
                updated_at=now,
                faker_id=biz,
                update_time=0,
                sync_time=0
            )
            session.add(new_feed)
            feed = new_feed
            created = True

        session.commit()

        # 首次订阅触发增量抓取任务
        if created:
            try:
                from core.queue import TaskQueue
                from core.wx import WxGather
                Max_page = int(cfg.get("max_page", "2"))
                TaskQueue.add_task(
                    WxGather().Model().get_Articles,
                    faker_id=feed.faker_id,
                    Mps_id=feed.id,
                    CallBack=UpdateArticle,
                    MaxPage=Max_page,
                    Mps_title=mp_name,
                    task_name=mp_name
                )
            except Exception as task_err:
                print(f"触发初始文章同步任务失败: {task_err}")

        # 组合返回数据：既兼容旧版前端需要的 mp_info 结构，也提供创建好的 feed 信息
        resp_data = {
            **info,
            "id": feed.id,
            "mp_name": feed.mp_name,
            "mp_cover": feed.mp_cover,
            "mp_intro": feed.mp_intro,
            "status": feed.status,
            "faker_id": feed.faker_id,
            "created": created
        }
        return success_response(
            resp_data,
            message="订阅添加成功！" if created else "订阅信息已更新！"
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"通过文章链接添加订阅失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"添加订阅失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.post("", summary="添加公众号")
async def add_mp(
    mp_name: str = Body(None, max_length=255),
    name: str = Body(None, max_length=255),
    mp_cover: str = Body(None, max_length=255),
    mp_id: str = Body(None, max_length=255),
    avatar: str = Body(None, max_length=500),
    mp_intro: str = Body(None, max_length=255),
    current_user: dict = Depends(get_current_user_or_ak)
):
    final_mp_name = (mp_name or name or "").strip()
    if not final_mp_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40001, message="请输入公众号名称")
        )

    if not mp_id:
        try:
            res = search_Biz(final_mp_name, limit=1)
            if res and res.get("list"):
                first = res["list"][0]
                mp_id = first.get("fakeid")
                if not avatar:
                    avatar = first.get("round_head_img")
                if not mp_intro:
                    mp_intro = first.get("signature")
        except Exception:
            pass

    if not mp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code=40002,
                message="未提供公众号唯一标识(mp_id)，请先在管理端扫码登录，或使用「文章链接识别」直接粘贴推文添加订阅"
            )
        )

    session = DB.get_session()
    try:
        from core.models.feed import Feed
        now = datetime.now()

        try:
            import base64
            mpx_id = base64.b64decode(mp_id).decode("utf-8")
        except Exception:
            mpx_id = mp_id

        local_avatar_path = f"{save_avatar_locally(avatar)}" if avatar else (mp_cover or "")

        existing_feed = session.query(Feed).filter(Feed.faker_id == mp_id).first()

        if existing_feed:
            existing_feed.mp_name = final_mp_name
            if local_avatar_path:
                existing_feed.mp_cover = local_avatar_path
            if mp_intro:
                existing_feed.mp_intro = mp_intro
            existing_feed.status = 1
            existing_feed.updated_at = now
            feed = existing_feed
            created = False
        else:
            new_feed = Feed(
                id=f"MP_WXS_{mpx_id}",
                mp_name=final_mp_name,
                mp_cover=local_avatar_path,
                mp_intro=mp_intro or final_mp_name,
                status=1,
                created_at=now,
                updated_at=now,
                faker_id=mp_id,
                update_time=0,
                sync_time=0,
            )
            session.add(new_feed)
            feed = new_feed
            created = True

        session.commit()

        if created:
            try:
                from core.queue import TaskQueue
                from core.wx import WxGather
                Max_page = int(cfg.get("max_page", "2"))
                TaskQueue.add_task(
                    WxGather().Model().get_Articles,
                    faker_id=feed.faker_id,
                    Mps_id=feed.id,
                    CallBack=UpdateArticle,
                    MaxPage=Max_page,
                    Mps_title=final_mp_name,
                    task_name=final_mp_name
                )
            except Exception as task_err:
                print(f"触发初始文章同步任务失败: {task_err}")

        return success_response({
            "id": feed.id,
            "mp_name": feed.mp_name,
            "mp_cover": feed.mp_cover,
            "mp_intro": feed.mp_intro,
            "status": feed.status,
            "faker_id": mp_id,
            "created_at": feed.created_at.isoformat() if feed.created_at else ""
        })
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"添加公众号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"添加公众号失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.delete("/{mp_id}", summary="删除订阅号")
async def delete_mp(
    mp_id: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        mp = session.query(Feed).filter(Feed.id == mp_id).first()
        if not mp:
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail=error_response(
                    code=40401,
                    message="订阅号不存在"
                )
            )
        
        session.delete(mp)
        session.commit()
        return success_response({
            "message": "订阅号删除成功",
            "id": mp_id
        })
    except Exception as e:
        session.rollback()
        print(f"删除订阅号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="删除订阅号失败"
            )
        )
    finally:
        session.close()

@router.put("/{mp_id}", summary="更新订阅号状态与信息")
async def update_mp_status(
    mp_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user_or_ak)
):
    from starlette import status as http_status
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        mp = session.query(Feed).filter(Feed.id == mp_id).first()
        if not mp:
            raise HTTPException(
                status_code=http_status.HTTP_201_CREATED,
                detail=error_response(
                    code=40401,
                    message="订阅号不存在"
                )
            )

        req_data = {}
        try:
            body_json = await request.json()
            if isinstance(body_json, dict):
                req_data = body_json
        except Exception:
            pass

        # 优先读取 body 中的 mp_name / name，其次读取 query_params
        new_name = req_data.get("mp_name") or req_data.get("name") or request.query_params.get("mp_name") or request.query_params.get("name")
        new_cover = req_data.get("mp_cover") or req_data.get("avatar") or request.query_params.get("mp_cover") or request.query_params.get("avatar")
        new_intro = req_data.get("mp_intro") or req_data.get("intro") or request.query_params.get("mp_intro") or request.query_params.get("intro")
        
        new_status = req_data.get("status")
        if new_status is None and "status" in request.query_params:
            try:
                new_status = int(request.query_params.get("status"))
            except Exception:
                pass

        if new_name is not None and str(new_name).strip():
            mp.mp_name = str(new_name).strip()
        if new_cover is not None:
            mp.mp_cover = str(new_cover).strip()
        if new_intro is not None:
            mp.mp_intro = str(new_intro).strip()
        if new_status is not None:
            try:
                mp.status = int(new_status)
            except Exception:
                pass

        mp.updated_at = datetime.now()
        session.commit()

        return success_response({
            "message": "更新成功",
            "id": mp_id,
            "mp_name": mp.mp_name,
            "mp_intro": mp.mp_intro,
            "status": mp.status
        })
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"更新订阅号错误: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="更新订阅号失败"
            )
        )
    finally:
        session.close()
