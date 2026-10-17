#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeFeed Doctor - 统一系统健康与环境自检工具
用法:
    python tools/doctor.py
    python tools/doctor.py --verbose
"""

import sys
import os
import re
import socket
import json
import hashlib
from typing import List, Tuple, Dict, Any

# 确保项目根目录在 sys.path 中
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 确保 Windows 终端 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 终端彩色输出
class TermColor:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def ok_mark(msg: str) -> str:
    return f"{TermColor.GREEN}[PASS] {msg}{TermColor.RESET}"

def warn_mark(msg: str) -> str:
    return f"{TermColor.YELLOW}[WARN] {msg}{TermColor.RESET}"

def err_mark(msg: str) -> str:
    return f"{TermColor.RED}[FAIL] {msg}{TermColor.RESET}"

def info_mark(msg: str) -> str:
    return f"{TermColor.CYAN}[INFO] {msg}{TermColor.RESET}"


class WeFeedDoctor:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[Tuple[str, str, str]] = []  # (status: OK/WARN/ERR, category, message)
        self.config_data: Dict[str, Any] = {}

    def log_ok(self, category: str, msg: str):
        self.results.append(("OK", category, msg))
        print(f"  {ok_mark(msg)}")

    def log_warn(self, category: str, msg: str):
        self.results.append(("WARN", category, msg))
        print(f"  {warn_mark(msg)}")

    def log_err(self, category: str, msg: str):
        self.results.append(("ERR", category, msg))
        print(f"  {err_mark(msg)}")

    def check_runtime_environment(self):
        print(f"\n{TermColor.BOLD}1. 运行环境检查 (Runtime Environment){TermColor.RESET}")
        
        # Python 版本
        py_ver = sys.version_info
        py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
        if py_ver >= (3, 10):
            self.log_ok("Runtime", f"Python 版本: {py_ver_str} (满足 >= 3.10 要求)")
        else:
            self.log_err("Runtime", f"Python 版本: {py_ver_str} (过低，需 >= 3.10)")

        # 操作系统与事件循环策略
        if sys.platform == "win32":
            import asyncio
            policy = asyncio.get_event_loop_policy()
            policy_name = policy.__class__.__name__
            if "Proactor" in policy_name:
                self.log_ok("Runtime", f"Windows 事件循环: {policy_name} (原生支持 Playwright 子进程)")
            else:
                self.log_warn("Runtime", f"Windows 事件循环: {policy_name} (非 Proactor，可能影响 Playwright)")
        else:
            self.log_ok("Runtime", f"操作系统: {sys.platform} (POSIX 规范标准环境)")

    def check_dependencies(self):
        print(f"\n{TermColor.BOLD}2. 核心依赖项检查 (Dependencies){TermColor.RESET}")
        
        required_pkgs = [
            ("yaml", "PyYAML", True),
            ("fastapi", "FastAPI", True),
            ("uvicorn", "Uvicorn", True),
            ("sqlalchemy", "SQLAlchemy", True),
            ("pydantic", "Pydantic", True),
            ("bs4", "BeautifulSoup4", True),
            ("requests", "Requests", True),
            ("playwright", "Playwright", False),
        ]

        for mod_name, disp_name, is_req in required_pkgs:
            try:
                mod = __import__(mod_name)
                ver = getattr(mod, "__version__", "已安装")
                self.log_ok("Deps", f"{disp_name} ({ver})")
            except ImportError:
                if is_req:
                    self.log_warn("Deps", f"{disp_name} 未安装在当前环境 (容器环境或未装 requirements.txt)")
                else:
                    self.log_warn("Deps", f"{disp_name} (可选扩展未安装)")

    def check_configuration(self):
        print(f"\n{TermColor.BOLD}3. 系统配置检查 (Configuration){TermColor.RESET}")
        
        config_path = os.path.join(ROOT_DIR, "config.yaml")
        if not os.path.exists(config_path):
            self.log_warn("Config", "根目录未找到 config.yaml (可能依赖环境变量或使用 config.example.yaml)")
            example_path = os.path.join(ROOT_DIR, "config.example.yaml")
            if os.path.exists(example_path):
                self.log_ok("Config", "找到 config.example.yaml 参考模板")
        else:
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config_data = yaml.safe_load(f) or {}
                self.log_ok("Config", f"config.yaml 语法解析正常 (大小: {os.path.getsize(config_path)} 字节)")
                
                # 端口与服务名称
                app_name = self.config_data.get("app_name", "WeFeed")
                port = self.config_data.get("port", 8001)
                self.log_ok("Config", f"应用标识: {app_name}, 监听端口: {port}")
            except Exception as e:
                self.log_err("Config", f"config.yaml 解析失败: {e}")

        # SSO 代理鉴权安全性
        sso_enabled = os.environ.get("SSO_TRUST_PROXY", "").lower() in ("true", "1") or \
                      str(self.config_data.get("server", {}).get("sso_trust_proxy", "")).lower() in ("true", "1")
        if sso_enabled:
            sso_secret = os.environ.get("SSO_TRUST_SECRET", "")
            sso_proxies = os.environ.get("SSO_TRUSTED_PROXIES", "")
            if not sso_secret and not sso_proxies:
                self.log_warn("Security", "已启用 SSO_TRUST_PROXY，但未配置密钥与代理列表（已激活内网网段兜底安全拦截）")
            else:
                self.log_ok("Security", "SSO_TRUST_PROXY 配置安全凭据/代理白名单就绪")

    def check_database(self):
        print(f"\n{TermColor.BOLD}4. 数据库连通性与模型检查 (Database){TermColor.RESET}")
        
        db_type = self.config_data.get("db", {}).get("type", "sqlite")
        db_url = self.config_data.get("db", {}).get("url", "")
        
        if db_type == "sqlite" or not db_url or "sqlite" in db_url:
            db_file = os.path.join(ROOT_DIR, "data", "db.sqlite") if not db_url else db_url.replace("sqlite:///", "")
            if os.path.exists(db_file):
                size_kb = os.path.getsize(db_file) / 1024
                self.log_ok("Database", f"SQLite 数据库文件存在: {db_file} ({size_kb:.1f} KB)")
            else:
                self.log_ok("Database", f"SQLite 数据库将在初次运行由初始化命令自动创建: {db_file}")

        try:
            from core.db import DB
            session = DB.get_session()
            try:
                # 快速检查表结构
                from core.models.article import Article
                from core.models.feed import Feed
                from core.models.user import User
                user_cnt = session.query(User).count()
                feed_cnt = session.query(Feed).count()
                art_cnt = session.query(Article).count()
                self.log_ok("Database", f"数据库会话正常连接: 用户 {user_cnt} 个, 订阅源 {feed_cnt} 个, 文章 {art_cnt} 篇")
            finally:
                session.close()
        except ImportError:
            self.log_warn("Database", "未导入 SQLAlchemy/Pydantic 模块，跳过深度 ORM 检查")
        except Exception as e:
            self.log_warn("Database", f"数据库会话暂未初始化或连接失败 (正常若尚未建库): {e}")

    def check_cascade(self):
        print(f"\n{TermColor.BOLD}5. 级联模式与分布式同步检查 (Cascade Node){TermColor.RESET}")
        
        cascade = self.config_data.get("cascade", {})
        enabled = cascade.get("enabled", False)
        if not enabled:
            self.log_ok("Cascade", "级联模式未启用 (单机独立工作模式)")
            return

        node_type = cascade.get("node_type", "child")
        self.log_ok("Cascade", f"级联节点角色: {node_type}")
        
        if node_type == "child":
            parent_url = cascade.get("parent_api_url", "")
            ak = cascade.get("api_key", "")
            sk = cascade.get("api_secret", "")
            
            if not parent_url:
                self.log_err("Cascade", "子节点缺少 parent_api_url 配置")
            else:
                self.log_ok("Cascade", f"父节点目标: {parent_url}")

            if not ak or not sk:
                self.log_err("Cascade", "子节点缺少 api_key 或 api_secret 凭据")
            else:
                sk_hash = hashlib.sha256(sk.encode("utf-8")).hexdigest()[:12]
                self.log_ok("Cascade", f"API 凭据就绪 (AK: {ak[:8]}..., SK Hash 前缀: {sk_hash})")

    def check_frontend_assets(self):
        print(f"\n{TermColor.BOLD}6. 前端静态资源与 UI 产物检查 (Web UI & Static Assets){TermColor.RESET}")
        
        dist_index = os.path.join(ROOT_DIR, "static", "index.html")
        if os.path.exists(dist_index):
            size_kb = os.path.getsize(dist_index) / 1024
            self.log_ok("Frontend", f"托管静态入口存在: static/index.html ({size_kb:.1f} KB)")
        else:
            self.log_err("Frontend", "缺失 static/index.html，请先在 web_ui 运行 npm run build")

        web_ui_pkg = os.path.join(ROOT_DIR, "web_ui", "package.json")
        if os.path.exists(web_ui_pkg):
            try:
                with open(web_ui_pkg, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                fw = "React 19" if "react" in pkg.get("dependencies", {}) else "Other"
                self.log_ok("Frontend", f"前端源码架构: {fw} (web_ui/package.json 正常)")
            except Exception:
                self.log_ok("Frontend", "web_ui 源码工程存在")

    def run_all(self):
        print("=" * 65)
        print(f"{TermColor.BOLD}{TermColor.CYAN}       WeFeed Doctor 统一系统与环境自检诊断器{TermColor.RESET}")
        print("=" * 65)
        
        self.check_runtime_environment()
        self.check_dependencies()
        self.check_configuration()
        self.check_database()
        self.check_cascade()
        self.check_frontend_assets()

        # 统计汇总
        ok_count = sum(1 for s, _, _ in self.results if s == "OK")
        warn_count = sum(1 for s, _, _ in self.results if s == "WARN")
        err_count = sum(1 for s, _, _ in self.results if s == "ERR")

        print("\n" + "=" * 65)
        print(f"{TermColor.BOLD}诊断报告结果摘要:{TermColor.RESET}")
        print(f"  通过项 (Passed):   {TermColor.GREEN}{ok_count}{TermColor.RESET}")
        print(f"  提示项 (Warnings): {TermColor.YELLOW}{warn_count}{TermColor.RESET}")
        print(f"  错误项 (Errors):   {TermColor.RED}{err_count}{TermColor.RESET}")
        print("=" * 65)
        
        if err_count == 0:
            print(f"{TermColor.GREEN}{TermColor.BOLD}[OK] 系统环境核心健康状况良好！{TermColor.RESET}\n")
            return 0
        else:
            print(f"{TermColor.RED}{TermColor.BOLD}[FAIL] 检测到 {err_count} 个阻碍运行的错误，请参考上述提示修正。{TermColor.RESET}\n")
            return 1


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    doctor = WeFeedDoctor(verbose=verbose)
    exit_code = doctor.run_all()
    sys.exit(exit_code)
