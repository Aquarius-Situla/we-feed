<div align="center">

<img src="static/logo.svg" alt="WeFeed Logo" width="100" height="100">

# WeFeed

**An elegant, reliable, and privacy-first WeChat Official Account & WeRead RSS aggregator.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3%20or%20later-blue.svg)](LICENSE)
[![Docker Image](https://img.shields.io/badge/Docker-ghcr.io-blue?logo=docker)](https://github.com/Aquarius-Situla/we-feed/pkgs/container/we-feed)
[![Multi-Arch](https://img.shields.io/badge/Platform-linux%2Famd64%20%7C%20linux%2Farm64-success)](#)
[![Python Version](https://img.shields.io/badge/Python-3.13+-brightgreen.svg)]()

[English](ReadMe.md) | [简体中文](README.zh-CN.md)

</div>

---

## 🌟 Why WeFeed?

**WeFeed** is a modernized, self-hosted RSS generation and content archiving assistant for WeChat Official Accounts. It is engineered to solve widespread challenges found in existing WeChat scrapers—such as **frequent anti-scraping blocks, embedded third-party tracking scripts, broken shortlinks, and noisy long-text titles**—offering a truly out-of-the-box, resilient, and privacy-respecting RSS subscription feed.

### Key Highlights

- 🛡️ **100% Tracker-Free & Privacy-Focused**: Completely removed all hardcoded third-party tracking/analytics scripts (e.g. Baidu Tongji) present in upstream, ensuring zero metadata or domain leaks for self-hosted instances.
- ⚡ **Multi-Tier Automated Failover**: Fixed premature exit loops on `ret=200013` rate limits, establishing a seamless automated fallback chain: `API Endpoints` ➔ `free_publish` ➔ `WeRead (weread_mp)` ➔ `Playwright`.
- 👥 **Multi-Account Quota Failover**: Supports configuring multiple WeRead accounts. When one account exhausts its daily reading quota (`-2014` / `499` / `-2041`), WeFeed automatically rotates to standby accounts without interrupting subscriptions.
- 🔗 **Zero Parameter Errors (URL Token Fix)**: Automatically restores tildes (`~`) in WeRead review IDs back to standard URL-safe Base64 underscores (`_`), eliminating WeChat "Parameter Error" pages and content extraction deadlocks.
- 📝 **Smart Short Image-Text Title Sanitization**: Detects titleless short image-text dynamic posts and smartly extracts the first sentence as a clean title, preventing 500+ character body texts from polluting feed readers.
- 🐳 **Official Multi-Arch Docker Images**: Built directly via GitHub Actions supporting native `linux/amd64` and `linux/arm64` (Raspberry Pi, ARM NAS, Apple Silicon servers), eliminating the need for complex host patch mounts.
- 📡 **Universal Reader Compatibility**: Generates standard RSS 2.0, Atom, and JSON feeds fully tested with FreshRSS, Miniflux, Feedly, NetNewsWire, and Inoreader.

---

## 🚀 Quick Start

### Method 1: Docker Compose (Recommended)

Create `docker-compose.yml`:

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
      - RSS_BASE_URL=http://localhost:8001  # External URL (e.g. https://feed.example.com)
      - RSS_FULL_CONTEXT=True               # Include full HTML article content in feed
      - GATHER.CONTENT=True                 # Download and clean full article body
      - GATHER.MODEL=weread_mp              # Recommended collection model
      - SPAN_INTERVAL=15                    # Periodic sync interval in minutes
    volumes:
      - ./data:/app/data
```

Start the service:

```bash
docker compose up -d
```

Open `http://<your-server-ip>:8001` in your browser to access the WeFeed web console.

---

### Method 2: Docker CLI

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

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `RSS_BASE_URL` | `http://localhost:8001` | Public base URL used for prefixing generated RSS feed links |
| `RSS_FULL_CONTEXT` | `True` | Whether to include full article content and images in feeds |
| `GATHER.MODEL` | `weread_mp` | Primary collection engine: `weread_mp` (recommended), `web`, or `app` |
| `GATHER.CONTENT` | `True` | Whether to fetch full article body during synchronization |
| `SPAN_INTERVAL` | `15` | Polling interval for automated scheduled synchronization (minutes) |
| `MAX_PAGE` | `1` | Maximum pagination depth per account run |
| `PROXY_URL` | *(empty)* | Optional outbound HTTP/SOCKS proxy when datacenter IPs are blocked |
| `SSO_TRUST_PROXY` | `False` | Trust upstream reverse proxy SSO authentication (e.g. Nginx Authenticator / Authelia) |
| `WEREAD_AUTO_KEEPALIVE` | `True` | Native in-container WeRead Cookie auto-keepalive via headless Chromium |

---

## 📖 WeRead Multi-Account Setup

1. Open the WeFeed admin dashboard in your browser.
2. Navigate to **WeRead Management**.
3. Click **Scan QR Code** to authorize your primary WeChat account.
4. Optionally click **Scan QR Code (Add Account)** to link additional backup accounts.
5. When the primary account exhausts its daily quota, WeFeed automatically rotates requests to backup accounts, guaranteeing uninterrupted feeds.

---

## 📜 License & Acknowledgements

This project is licensed under the **[GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)](LICENSE)**.

```text
Copyright (C) 2026 Situla <https://github.com/Aquarius-Situla/we-feed>
Copyright (C) 2024-2026 rachelos <https://github.com/rachelos/we-mp-rss>
```

### Upstream Attribution
WeFeed is a community-maintained fork and enhancement of **[rachelos/we-mp-rss](https://github.com/rachelos/we-mp-rss)**. In accordance with the original **MIT License** terms, we gratefully acknowledge and preserve the original copyright notice below:

> **MIT License**  
> Copyright (c) 2025 RACHEL  
> Mail: rachelos@qq.com  
> 
> *The original code from we-mp-rss is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.*
