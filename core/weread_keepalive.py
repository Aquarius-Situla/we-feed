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
import random
import datetime
import threading
import yaml
import requests
import tempfile
from typing import Optional

logger = logging.getLogger("weread_keepalive")

DEFAULT_LIC_PATH = os.environ.get("WEREAD_LIC_PATH", "/app/data/wx.lic" if os.path.exists("/app/data") else "./data/wx.lic")
DEFAULT_PROFILE_DIR = os.environ.get("WEREAD_PROFILE_DIR", "/app/data/weread_browser_profile" if os.path.exists("/app/data") else "./data/weread_browser_profile")
TARGET_URL = "https://weread.qq.com/web/shelf"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def log(msg: str):
    logger.info(f"[keepalive] {msg}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [weread_keepalive] {msg}")


def _refresh_account_cookie(cookie_str: str, current_vid: str, target_url: str, profile_dir: str) -> tuple[Optional[str], Optional[str]]:
    """
    针对单个微信读书账号执行 Playwright 无头浏览器 Cookie 保活刷新
    返回: (new_cookie_str, new_vid) 或 (None, None)
    """
    if not cookie_str:
        return None, None

    os.makedirs(profile_dir, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("警告: 未安装 playwright，无法执行自动保活")
        return None, None

    captured_cookies = {}
    cookie_dict = {}

    try:
        with sync_playwright() as p:
            args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ]
            context = p.chromium.launch_persistent_context(
                profile_dir,
                headless=True,
                args=args,
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            try:
                # 注入现有 Cookie
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
                if cookies_to_add:
                    try:
                        context.add_cookies(cookies_to_add)
                    except Exception as e:
                        log(f"注入 Cookie 警告: {e}")

                page = context.pages[0] if context.pages else context.new_page()

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
                    # 随机停留 5 ~ 9 秒模拟人类正常停留浏览
                    time.sleep(random.uniform(5.0, 9.0))
                    log(f"页面加载完成: '{page.title()}'")
                except Exception as e:
                    log(f"页面跳转警告: {e}")

                ctx_cookies = context.cookies("https://weread.qq.com")
                for c in ctx_cookies:
                    cookie_dict[c["name"]] = c["value"]

                cookie_dict.update(captured_cookies)
            finally:
                context.close()

    except Exception as e:
        log(f"执行 Playwright 浏览器操作异常: {e}")
        return None, None

    wr_skey = cookie_dict.get("wr_skey")
    wr_vid = cookie_dict.get("wr_vid") or current_vid
    wr_rt = cookie_dict.get("wr_rt")

    if not wr_skey:
        log(f"Cookie 保活提示 (VID: {current_vid or '未知'}): 未从浏览器会话提取到 wr_skey（Cookie 可能已彻底过期需重新扫码）")
        return None, None

    log(f"成功提取活跃 Cookie (VID: {wr_vid}): wr_skey={wr_skey[:8]}..., wr_rt={wr_rt[:10] if wr_rt else 'None'}...")

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
            log(f"API 连通性测试通过！微信读书账号 (VID: {wr_vid}) Cookie 处于激活状态。")
        else:
            log(f"API 测试返回: status={r.status_code}, body={r.text[:100]}")
    except Exception as e:
        log(f"API 校验请求异常: {e}")

    return new_cookie_str, str(wr_vid) if wr_vid else None


def run_keepalive(lic_path: str = None) -> bool:
    """
    执行微信读书 Cookie 保活刷新（支持单账号及多账号列表全部保活）
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
    target_url = weread_data.get("cookie_refresh_url") or TARGET_URL
    accounts = weread_data.get("accounts")

    success_count = 0

    if isinstance(accounts, list) and accounts:
        # 多账号模式：遍历 accounts 列表中所有账号
        log(f"检测到 {len(accounts)} 个微信读书配置账号，开始逐一保活...")
        for idx, acc in enumerate(accounts):
            acc_cookie = acc.get("cookie", "")
            acc_vid = str(acc.get("vid", "") or "")
            if not acc_cookie:
                log(f"账号 [{idx+1}/{len(accounts)}] 未配置 cookie，跳过")
                continue

            log(f"正在保活账号 [{idx+1}/{len(accounts)}] (VID: {acc_vid or '未知'})...")
            acc_profile = os.path.join(DEFAULT_PROFILE_DIR, f"acc_{acc_vid or idx}")
            new_cookie, new_vid = _refresh_account_cookie(acc_cookie, acc_vid, target_url, acc_profile)
            if new_cookie:
                acc["cookie"] = new_cookie
                if new_vid:
                    acc["vid"] = new_vid
                success_count += 1
                # 若是第 1 个账号或与顶层 vid 匹配，同步更新顶层字段
                if idx == 0 or (weread_data.get("vid") and str(weread_data.get("vid")) == acc_vid):
                    weread_data["cookie"] = new_cookie
                    if new_vid:
                        weread_data["vid"] = new_vid

            if idx < len(accounts) - 1:
                wait_sec = random.uniform(8.0, 15.0)
                log(f"账号间隔防风控休眠 {wait_sec:.1f} 秒...")
                time.sleep(wait_sec)

    else:
        # 单账号模式
        cookie_str = weread_data.get("cookie", "")
        current_vid = weread_data.get("vid", "")
        if not cookie_str:
            log("跳过保活: weread_data 中未配置 cookie")
            return False

        log(f"开始微信读书 Cookie 保活 (VID: {current_vid or '未知'})...")
        new_cookie, new_vid = _refresh_account_cookie(cookie_str, str(current_vid or ""), target_url, DEFAULT_PROFILE_DIR)
        if new_cookie:
            weread_data["cookie"] = new_cookie
            if new_vid:
                weread_data["vid"] = new_vid
            success_count += 1

    if success_count == 0:
        log("本次保活未成功刷新任何有效 Cookie")
        return False

    weread_data["last_keepalive_ts"] = time.time()
    lic["weread_data"] = weread_data

    try:
        dir_name = os.path.dirname(os.path.abspath(lic_path))
        os.makedirs(dir_name, exist_ok=True)
        fd, temp_file = tempfile.mkstemp(dir=dir_name, prefix=".wx_lic_", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(lic, f, allow_unicode=True, sort_keys=False)
        os.replace(temp_file, lic_path)
        log(f"最新 Cookie 已原子持久化保存至 {lic_path} (成功更新 {success_count} 个账号)")
        return True
    except Exception as e:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        log(f"写回 {lic_path} 失败: {e}")
        return False


def calculate_next_sleep_seconds(base_interval_hours: float = 3.0) -> float:
    """
    计算下一次保活休眠时长，模拟正常人类作息并添加随机盐值（jitter）：

    1. 深夜睡眠休眠 (01:00 ~ 07:00 本地时间)：
       正常人深夜处于睡眠状态，不会每小时频繁打开微信读书。
       若当前进入深夜时间，或计算出的下次执行时间落在 01:00 ~ 07:00：
       系统将休眠直至早晨唤醒（07:15 ~ 08:00，包含随机盐值），避免深夜机械式刷新触发风控。

    2. 白天正常活跃时间 (07:00 ~ 01:00)：
       基础周期拉长至 2.5 ~ 3.5 小时（默认基准 3 小时，远非固定的 1 小时）。
       并叠加 ±25 ~ 40 分钟的大幅度随机盐值 (jitter)，
       真实模拟人类不规律打开阅读器的生活习惯。
    """
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute

    # 如果当前时间已在深夜 01:00 ~ 06:59
    if 1 <= hour < 7:
        minutes_to_7am = (6 - hour) * 60 + (60 - minute)
        wake_jitter_minutes = random.randint(15, 45)
        sleep_seconds = float((minutes_to_7am + wake_jitter_minutes) * 60)
        wake_time = now + datetime.timedelta(seconds=sleep_seconds)
        log(f"当前为深夜作息时间 ({now.strftime('%H:%M')})，模拟人类作息睡眠中... 将休眠至早晨 {wake_time.strftime('%H:%M:%S')} (约 {sleep_seconds/3600:.2f} 小时)")
        return sleep_seconds

    # 白天：基准时长浮动 ±0.5 小时
    fluctuated_hours = base_interval_hours + random.uniform(-0.5, 0.5)
    # 额外附加 ±1500 秒 (±25 分钟) 随机盐
    jitter_seconds = random.uniform(-1500, 1500)
    sleep_seconds = max(1800.0, fluctuated_hours * 3600.0 + jitter_seconds)

    # 预测下次唤醒时间
    wake_time = now + datetime.timedelta(seconds=sleep_seconds)
    # 若下次唤醒时间落在深夜 01:00 ~ 06:59，则自动顺延至早晨唤醒
    if 1 <= wake_time.hour < 7:
        wake_day = wake_time.date()
        target_morning = datetime.datetime(
            wake_day.year, wake_day.month, wake_day.day,
            7, random.randint(15, 45), random.randint(0, 59)
        )
        if target_morning > now:
            sleep_seconds = float((target_morning - now).total_seconds())
            wake_time = now + datetime.timedelta(seconds=sleep_seconds)

    log(f"模拟人类作息调度：下次保活休眠 {sleep_seconds/3600:.2f} 小时（加盐后预计于 {wake_time.strftime('%Y-%m-%d %H:%M:%S')} 唤醒）")
    return sleep_seconds


def _keepalive_loop(base_interval_hours: float = 3.0):
    """后台常驻保活守护循环（智能加盐与作息模拟）"""
    # 启动后随机等待 45 ~ 90 秒，避免容器刚启动时 CPU 竞争
    init_delay = random.uniform(45.0, 90.0)
    time.sleep(init_delay)

    while True:
        try:
            run_keepalive()
        except Exception as e:
            log(f"保活执行异常: {e}")

        # 计算下一次休眠时间（包含作息判断与加盐）
        sleep_sec = calculate_next_sleep_seconds(base_interval_hours)
        time.sleep(sleep_sec)


def start_weread_keepalive_service(interval_hours: float = 3.0):
    """启动容器内置后台保活守护线程"""
    t = threading.Thread(target=_keepalive_loop, args=(interval_hours,), daemon=True, name="WeReadKeepAliveThread")
    t.start()
    log(f"微信读书原生 Cookie 保活守护服务已启动（基准周期: {interval_hours} 小时，模拟人类作息与随机加盐）")

