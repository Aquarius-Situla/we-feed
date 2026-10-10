<div align="center">

<img src="static/logo.svg" alt="WeFeed Logo" width="120" height="120">

# WeFeed

**优雅、稳定、纯净的微信公众号与微信读书 RSS 聚合订阅助手**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3%20or%20later-blue.svg)](LICENSE)
[![Docker Image](https://img.shields.io/badge/Docker-ghcr.io-blue?logo=docker)](https://github.com/Aquarius-Situla/we-feed/pkgs/container/we-feed)
[![Multi-Arch](https://img.shields.io/badge/Platform-linux%2Famd64%20%7C%20linux%2Farm64-success)](#)
[![Python Version](https://img.shields.io/badge/Python-3.13+-brightgreen.svg)]()

[简体中文](README.zh-CN.md) | [English](ReadMe.md)

</div>

---

## 🌟 为什么选择 WeFeed？

**WeFeed** 是专为自托管用户打造的微信公众号内容归档与 RSS 生成工具。旨在解决传统微信公众号采集工具中普遍存在的**风控报错频繁、强绑第三方统计、短链失效、长正文误充当标题**等长期痛点，提供真正开箱即用、高可用、保护隐私的订阅体验。

### 核心亮点

- 🛡️ **100% 纯净无追踪**：彻底剔除原项目中硬编码注入的第三方数据统计代码（如百度统计等），绝不上报任何私有域名、路径或元数据，保护内网与私有部署隐私。
- ⚡ **智能风控平滑降级**：修复微信公众平台接口遭遇 `ret=200013` 限频时提前中断的缺陷，打通「后台端点 ➔ `free_publish` ➔ 微信读书 (`weread_mp`) ➔ Playwright」的多级深度自动容灾降级。
- 👥 **多账号配额自动轮换**：支持添加多个微信读书 Cookie，当单账号遇到配额耗尽（`-2014` / `499` / `-2041`）时，系统自动无缝切号并接续抓取，杜绝任务中断与文章漏采。
- 🔗 **短链 Token 修复（零“参数错误”）**：还原微信短链中被 WeRead 转义的波浪号 `~` 为合法的下划线 `_`，彻底解决用户点击原文提示“参数错误”及后台正文抓取死锁的问题。
- 📝 **智能短图文标题清洗**：自动识别微信“短图文”无标题动态，智能提取首行有效摘要并优雅截断，避免 500+ 字长篇多行正文充当标题污染 RSS 阅读器。
- 🐳 **官方跨架构 Docker 镜像**：提供 GitHub Actions 自动构建的原生 `linux/amd64` 与 `linux/arm64` 镜像（直接适配 x86 服务器、树莓派及各类 ARM NAS），无需在宿主机额外挂载补丁文件。
- 📡 **全平台阅读器完美兼容**：输出标准 RSS / Atom / JSON Feed，已完美适配 FreshRSS、Miniflux、Feedly、NetNewsWire、Inoreader 等主流阅读器。

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: "3.8"

services:
  we-feed:
    image: ghcr.io/aquarius-situla/we-feed:latest
    container_name: we-feed
    restart: always
    ports:
      - "8001:8001"
    environment:
      - TZ=Asia/Shanghai
      - RSS_BASE_URL=http://localhost:8001  # 外部访问地址（例如 https://feed.example.com）
      - RSS_FULL_CONTEXT=True               # RSS 输出是否包含完整正文 HTML
      - GATHER.CONTENT=True                 # 是否自动抓取文章正文
      - GATHER.MODEL=weread_mp              # 采集模式：推荐 weread_mp
      - SPAN_INTERVAL=15                    # 定时同步周期（分钟）
    volumes:
      - ./data:/app/data
```

启动服务：

```bash
docker compose up -d
```

访问 `http://<服务器IP>:8001` 即可进入 WeFeed Web 管理界面。

---

### 方式二：Docker CLI 单行启动

```bash
docker run -d \
  --name we-feed \
  --restart always \
  -p 8001:8001 \
  -e TZ=Asia/Shanghai \
  -e RSS_BASE_URL=http://localhost:8001 \
  -e GATHER.MODEL=weread_mp \
  -v $(pwd)/data:/app/data \
  ghcr.io/aquarius-situla/we-feed:latest
```

---

## ⚙️ 核心环境变量配置

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `RSS_BASE_URL` | `http://localhost:8001` | 服务外部访问根域名（决定生成订阅链接的前缀） |
| `RSS_FULL_CONTEXT` | `True` | 是否在 RSS / Atom 源中包含完整正文与配图 |
| `GATHER.MODEL` | `weread_mp` | 核心采集通道：`weread_mp`（微信读书通道，推荐）、`web` 或 `app` |
| `GATHER.CONTENT` | `True` | 是否在入库时自动下载并清洗文章全文 |
| `SPAN_INTERVAL` | `15` | 定时全量同步轮询间隔（分钟） |
| `MAX_PAGE` | `1` | 微信读书单次抓取最大翻页数 |
| `PROXY_URL` | *(空)* | HTTP/SOCKS 出口代理（如微信封锁数据中心 IP 时使用） |

---

## 📖 微信读书多账号配置说明

1. 部署启动后，在浏览器中打开管理面板并登录。
2. 进入 **微信读书管理** 页面。
3. 点击 **扫码授权** 即可绑定首个微信号凭据。
4. 后续可继续点击 **扫码授权（添加账号）** 添加备用微信号。
5. 当主账号每日配额耗尽时，WeFeed 将自动触发 Round-Robin 算法切换到备用账号继续抓取，保障订阅源持续更新不漏采。

---

## 📜 开源许可与致谢 (License & Acknowledgements)

本项目采用 **[GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)](LICENSE)** 协议开源。

### 原项目致谢
WeFeed 是基于原开源项目 **[rachelos/we-mp-rss](https://github.com/rachelos/we-mp-rss)** 派生与重构的社区维护版本。根据原项目的 **MIT License** 要求，我们在此完整保留并声明原作者的版权信息：

> **MIT License**  
> Copyright (c) 2025 RACHEL  
> Mail: rachelos@qq.com  
> 
> *The original code from we-mp-rss is licensed under the MIT License. See [LICENSE](LICENSE) for the complete original license notice.*
