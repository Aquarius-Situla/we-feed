import os
from core.ver import *

# 默认最新版本与当前版本保持一致，彻底杜绝服务启动时无感外发请求泄露主机 IP
LATEST_VERSION = VERSION

# API接口前缀
API_BASE = "/api/v1/wx"

# 工作目录
WORK_DIR = "./work"

# 静态文件目录
STATIC_DIR = "./static"