# -*- coding: utf-8 -*-
"""
WeRead 凭据状态与有效性校验模块
统一管理微信读书 Cookie 有效性检测、过期标记、配额状态更新与缓存。
"""

import os
import time
import json
import logging
from typing import Optional, Tuple, Dict, Any
import requests

logger = logging.getLogger("weread_status")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def get_lic_path() -> str:
    """获取 wx.lic 路径，适配 Docker 与宿主机开发环境"""
    lic = os.environ.get("WEREAD_LIC_PATH")
    if lic and os.path.exists(os.path.dirname(lic)):
        return lic
    if os.path.exists("/app/data"):
        return "/app/data/wx.lic"
    return "./data/wx.lic"


def verify_weread_cookie_quick(
    cookie: str,
    vid: str = "",
    timeout: int = 5,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    轻量快速验证微信读书 Cookie 是否处于有效登录态。
    请求 https://weread.qq.com/web/user
    
    返回: (is_valid: bool, error_msg: str, user_info: dict)
    """
    if not cookie:
        return False, "未配置 Cookie", {}

    headers = {
        "Cookie": cookie,
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://weread.qq.com",
        "Referer": "https://weread.qq.com/",
    }

    try:
        r = requests.get(
            "https://weread.qq.com/web/user",
            headers=headers,
            timeout=timeout,
        )
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception:
                return False, "响应不是有效 JSON", {}

            code = data.get("errCode", data.get("errcode", 0))
            if code == 0 and not data.get("errMsg"):
                return True, "", data

            if code in (-2012, -2010):
                return False, data.get("errMsg") or "登录超时，请重新扫码", data
            elif code in (-2014, -2041):
                return False, data.get("errMsg") or "阅读配额已耗尽", data
            else:
                msg = data.get("errMsg") or f"接口返回错误码: {code}"
                return False, msg, data
        elif r.status_code in (401, 403):
            return False, f"未授权 (HTTP {r.status_code})", {}
        else:
            return False, f"HTTP {r.status_code}", {}
    except requests.exceptions.Timeout:
        return False, "请求微信读书接口超时", {}
    except Exception as exc:
        return False, f"网络异常: {exc}", {}


def update_weread_account_status(
    vid: str = "",
    expired: Optional[bool] = None,
    quota_exhausted: Optional[bool] = None,
    error_msg: Optional[str] = None,
) -> None:
    """
    更新 wx.lic 中指定账号（或全部/主账号）的凭据状态。
    当抓取或定时保活探测到失效/配额耗尽时实时调用。
    """
    from core.config import Config

    lic_path = get_lic_path()
    os.makedirs(os.path.dirname(lic_path), exist_ok=True)
    if not os.path.exists(lic_path):
        return

    try:
        cfg = Config(lic_path)
        data = cfg.get("weread_data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        changed = False
        accounts = data.get("accounts")
        vid_str = str(vid) if vid else ""

        if isinstance(accounts, list) and accounts:
            for acc in accounts:
                if not vid_str or str(acc.get("vid", "")) == vid_str:
                    if expired is not None:
                        acc["expired"] = expired
                    if quota_exhausted is not None:
                        acc["quota_exhausted"] = quota_exhausted
                    if error_msg is not None:
                        acc["error_msg"] = error_msg
                    acc["last_checked_ts"] = time.time()
                    changed = True
        else:
            if expired is not None:
                data["expired"] = expired
            if quota_exhausted is not None:
                data["quota_exhausted"] = quota_exhausted
            if error_msg is not None:
                data["error_msg"] = error_msg
            data["last_checked_ts"] = time.time()
            changed = True

        if changed:
            cfg.set("weread_data", data)
            cfg.save_config()
            cfg.reload()
            logger.info(f"已更新微信读书账号状态 [vid={vid_str}]: expired={expired}, error_msg={error_msg}")
    except Exception as exc:
        logger.warning(f"更新微信读书账号状态失败: {exc}")


def check_and_update_status(
    force: bool = False,
    cache_ttl: int = 300,
) -> Dict[str, Any]:
    """
    检查并刷新微信读书账号有效性。
    若未超过 cache_ttl 且未强制刷新，直接返回本地缓存状态。
    """
    from core.config import Config

    lic_path = get_lic_path()
    if not os.path.exists(lic_path):
        return {}

    try:
        cfg = Config(lic_path)
        data = cfg.get("weread_data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        accounts = data.get("accounts")
        need_save = False

        if isinstance(accounts, list) and accounts:
            for acc in accounts:
                cookie = acc.get("cookie", "")
                vid = str(acc.get("vid", ""))
                last_ts = acc.get("last_checked_ts", 0)
                if force or (time.time() - last_ts > cache_ttl):
                    if cookie:
                        is_valid, err, user_info = verify_weread_cookie_quick(cookie, vid)
                        acc["expired"] = not is_valid
                        acc["error_msg"] = err
                        acc["last_checked_ts"] = time.time()
                        if is_valid and user_info:
                            if user_info.get("name") and not acc.get("name"):
                                acc["name"] = user_info["name"]
                            if user_info.get("avatar"):
                                acc["avatar"] = user_info["avatar"]
                        need_save = True
        else:
            cookie = data.get("cookie", "")
            vid = str(data.get("vid", ""))
            last_ts = data.get("last_checked_ts", 0)
            if force or (time.time() - last_ts > cache_ttl):
                if cookie:
                    is_valid, err, user_info = verify_weread_cookie_quick(cookie, vid)
                    data["expired"] = not is_valid
                    data["error_msg"] = err
                    data["last_checked_ts"] = time.time()
                    need_save = True

        if need_save:
            cfg.set("weread_data", data)
            cfg.save_config()
            cfg.reload()

        return data
    except Exception as exc:
        logger.warning(f"校验微信读书状态异常: {exc}")
        return {}
