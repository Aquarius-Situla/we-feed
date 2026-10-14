#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeFeed 微信读书 Cookie 自动保活服务
容器原生运行：通过 Playwright 无头 Chromium 访问微信读书书架，监听并捕获更新的登录态 Cookie，写回 wx.lic。
无需宿主机外部脚本与 crontab，全平台（Linux/Docker/macOS/Windows）自包含。
"""

import os
import sys
import time
import json
import logging
import threading
import yaml
import requests

logger = logging.getLogger("weread_keepalive")

DEFAULT_LIC_PATH = os.environ.get("WEREAD_LIC_PATH", "/app/data/wx.lic" if os.path.exists("/app/data") else "./data/wx.lic")
DEFAULT_PROFILE_DIR = os.environ.get("WEREAD_PROFILE_DIR", "/app/data/weread_browser_profile" if os.path.exists("/app/data") else "./data/weread_browser_profile")
TARGET_URL = "https://weread.qq.com/web/shelf"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def log(msg: str):
    logger.info(f"[keepalive] {msg}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [weread_keepalive] {msg}")


def run_keepalive(lic_path: str = None) -> bool:
    """
    执行单次微信读书 Cookie 保活刷新
    """
    lic_path = lic_path or DEFAULT_LIC_PATH
    if not os.path.exists(lic_path):
        # 兼容相对路径 ./data/wx.lic
        alt_path = "./data/wx.lic" if lic_path != "./data/wx.lic" else "/app/data/wx.lic"
        if os.path.exists(alt_path):
            lic_path = alt_path
        else:
            log(f"跳过保活: 凭据文件未找到 ({lic_path})")
            return False

    try:
        with open(lic_path, "r", encoding="utf-8") as f:
            lic = yaml.safe_load(f) or {}
    except Exception as e:
        log(f"读取 {lic_path} 失败: {e}")
        return False

    weread_data = lic.get("weread_data", {})
    cookie_str = weread_data.get("cookie", "")
    current_vid = weread_data.get("vid", "")

    if not cookie_str:
        log("跳过保活: weread_data 中未配置 cookie")
        return False

    log(f"开始微信读书 Cookie 保活 (VID: {current_vid})...")
    os.makedirs(DEFAULT_PROFILE_DIR, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("警告: 未安装 playwright，无法执行自动保活")
        return False

    captured_cookies = {}

    try:
        with sync_playwright() as p:
            args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ]
            context = p.chromium.launch_persistent_context(
                DEFAULT_PROFILE_DIR,
                headless=True,
                args=args,
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )

            # 注入现有 Cookie
            if cookie_str:
                cookies_to_add = []
                for item in cookie_str.split(";"):
                    if "=" in item:
                        k, _, v = item.strip().partition("=")
                        cookies_to_add.append({
                            "name": k.strip(),
                            "value": v.strip(),
                            "domain": ".weread.qq.com",
                            "path": "/"
                        })
                try:
                    context.add_cookies(cookies_to_add)
                except Exception as e:
                    log(f"注入 Cookie 警告: {e}")

            target_url = weread_data.get("cookie_refresh_url") or TARGET_URL

            def on_request(request):
                if "web/mp/articles" in request.url:
                    req_cookie = request.headers.get("cookie", "")
                    for item in req_cookie.split(";"):
                        if "=" in item:
                            k, _, v = item.strip().partition("=")
                            captured_cookies[k.strip()] = v.strip()

            def on_response(response):
                if "weread.qq.com" in response.url:
                    for header_name, header_val in response.headers.items():
                        if header_name.lower() == "set-cookie":
                            for part in header_val.split("\n"):
                                for subpart in part.split(";"):
                                    if "=" in subpart:
                                        k, _, v = subpart.strip().partition("=")
                                        if k.strip().startswith("wr_"):
                                            captured_cookies[k.strip()] = v.strip()

            page.on("request", on_request)
            page.on("response", on_response)

            log(f"正在加载微信读书页面以触发生命周期保活: {target_url}...")
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(6)
                log(f"页面加载完成: '{page.title()}'")
            except Exception as e:
                log(f"页面跳转警告: {e}")

            ctx_cookies = context.cookies("https://weread.qq.com")
            cookie_dict = {}
            for c in ctx_cookies:
                cookie_dict[c["name"]] = c["value"]

            cookie_dict.update(captured_cookies)
            context.close()

    except Exception as e:
        log(f"执行 Playwright 浏览器操作异常: {e}")
        return False

    wr_skey = cookie_dict.get("wr_skey")
    wr_vid = cookie_dict.get("wr_vid") or current_vid
    wr_rt = cookie_dict.get("wr_rt")

    if not wr_skey:
        log("Cookie 保活提示: 未从浏览器会话提取到 wr_skey（Cookie 可能已彻底过期需重新扫码）")
        return False

    log(f"成功提取活跃 Cookie: wr_vid={wr_vid}, wr_skey={wr_skey[:8]}..., wr_rt={wr_rt[:10] if wr_rt else 'None'}...")

    cookie_parts = []
    for k, v in cookie_dict.items():
        if k.startswith("wr_"):
            cookie_parts.append(f"{k}={v}")
    new_cookie_str = "; ".join(cookie_parts)

    # 验证新 Cookie
    test_headers = {
        "Cookie": new_cookie_str,
        "User-Agent": USER_AGENT,
        "Origin": "https://weread.qq.com",
        "Referer": "https://weread.qq.com/",
    }
    try:
        r = requests.get(
            "https://weread.qq.com/web/mp/cover",
            params={"bookId": "MP_WXS_2103095721"},
            headers=test_headers,
            timeout=10
        )
        if r.status_code == 200 and "title" in r.text:
            log("API 连通性测试通过！微信读书 Cookie 处于激活状态。")
        else:
            log(f"API 测试返回: status={r.status_code}, body={r.text[:100]}")
    except Exception as e:
        log(f"API 校验请求异常: {e}")

    # 写回 wx.lic
    weread_data["cookie"] = new_cookie_str
    if wr_vid:
        weread_data["vid"] = str(wr_vid)
    weread_data["last_keepalive_ts"] = time.time()
    lic["weread_data"] = weread_data

    try:
        with open(lic_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(lic, f, allow_unicode=True, sort_keys=False)
        log(f"最新 Cookie 已持久化保存至 {lic_path}")
        return True
    except Exception as e:
        log(f"写回 {lic_path} 失败: {e}")
        return False


def _keepalive_loop(interval_hours: int = 1):
    """后台常驻定时保活循环"""
    # 启动 30 秒后先执行一次初始保活
    time.sleep(30)
    while True:
        try:
            run_keepalive()
        except Exception as e:
            log(f"定时保活异常: {e}")
        time.sleep(interval_hours * 3600)


def start_weread_keepalive_service(interval_hours: int = 1):
    """启动容器内置后台保活守护线程"""
    t = threading.Thread(target=_keepalive_loop, args=(interval_hours,), daemon=True, name="WeReadKeepAliveThread")
    t.start()
    log(f"微信读书原生 Cookie 保活守护服务已启动（周期: {interval_hours} 小时）")
