#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeFeed 微信读书 Cookie 保活入口脚本
支持独立命令行执行或外部定时调度。
"""
import sys
import os

# 将项目根目录加入模块路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.weread_keepalive import run_keepalive

if __name__ == "__main__":
    ok = run_keepalive()
    sys.exit(0 if ok else 1)
