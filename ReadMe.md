<div align="center">

<img src="static/logo.svg?v=2" alt="WeFeed Logo" width="96" height="96">

# WeFeed

A lightweight, tracker-free, and out-of-the-box RSS aggregator for WeChat Official Accounts & WeRead.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3%20or%20later-blue.svg)](LICENSE)
[![Docker Image](https://img.shields.io/badge/Docker-ghcr.io-blue?logo=docker)](https://github.com/Aquarius-Situla/we-feed/pkgs/container/we-feed)
[![Multi-Arch](https://img.shields.io/badge/Platform-linux%2Famd64%20%7C%20linux%2Farm64-success)](#)
[![Python Version](https://img.shields.io/badge/Python-3.13+-brightgreen.svg)]()

[English](ReadMe.md) | [简体中文](README.zh-CN.md)

</div>

---

## 📌 Why WeFeed? (Project Origins)

**WeFeed** is a modernized, privacy-focused self-hosted service designed to generate RSS feeds and archive articles from WeChat Official Accounts.

This project is forked from the open-source project [rachelos/we-mp-rss](https://github.com/rachelos/we-mp-rss). While the upstream project pioneered an effective approach to scraping WeChat feeds, practical self-hosting revealed several critical issues that motivated us to maintain and rebuild WeFeed independently:

### 1. Completely Tracker-Free: Zero Leaks of Server IP and Domains
Upstream code had hardcoded third-party analytics scripts (such as Baidu Tongji) injected into the frontend and backend. For users self-hosting on a VPS or home server, this silently reported their server's public IP address, private domain, and access paths to external analytics providers.
> **WeFeed completely purges all telemetry, trackers, and external analytics scripts**, ensuring 100% local self-containment and privacy with zero metadata leakage.

### 2. Stripped Bloat & Refactored Modern Web UI
Over time, upstream accumulated numerous features unrelated to core RSS aggregation—such as an integrated web novel reader and host CPU/memory monitoring dashboards. These non-essential features caused bloated bundle sizes, clunky UI interactions, and unnecessary complexity.
> **WeFeed stripped away the novel reader, system monitoring panels, and redundant modules**, refactoring the management console into a lightweight, responsive, and distraction-free interface dedicated purely to feed subscriptions and clean article reading.

### 3. Hardened Long-term Self-Hosting Reliability
To address frequent challenges in real-world self-hosting—such as WeChat rate limits, expiring cookies, and daily reading quotas—WeFeed integrates **multi-account quota failover**, **native in-container browser keepalive**, and **anti-hotlinking protection**, ensuring rock-solid automated operation without requiring complex external host cron scripts.

---

## ✨ Key Features

- **🛡️ 100% Private & Tracker-Free**: Zero telemetry or third-party tracking scripts; your server IP, domain, and reading habits remain strictly confidential.
- **🎨 Modern, Lightweight UI**: Free of bloated novel readers or system monitors; focused purely on feed subscriptions, feed streams, and comfortable reading.
- **👥 Multi-Account Quota Failover**: Link multiple WeRead accounts; when one account exhausts its daily reading quota, WeFeed seamlessly rotates to backup accounts to guarantee continuous fetching.
- **⏰ Native In-Container Keepalive**: Built-in background daemon simulates realistic human browsing schedules to keep WeRead cookies active, eliminating manual cookie maintenance.
- **📡 Universal Feed Formats**: Generates standard RSS 2.0, Atom, and JSON feeds fully compatible with FreshRSS, Miniflux, Feedly, NetNewsWire, Follow, and Inoreader.
- **🖼️ Anti-Hotlinking Defense**: Built-in Referrer isolation policy ensures article covers and in-line images display cleanly without broken images in external RSS readers.
- **🐳 Multi-Architecture Docker Images**: GitHub Actions automatically builds native `linux/amd64` and `linux/arm64` images for x86 servers, ARM NAS devices, and Raspberry Pi.

---

## 🖥️ UI Preview

WeFeed features a clean and modern web dashboard, completely stripped of bloated novel readers and hardware monitoring panels:

<div align="center">

### Feeds Management
Intuitive feed cards with one-click RSS/Atom links, OPML export, tag classification, and status filters.

![Feeds Management](docs/images/feeds_view.png)

### Article Stream
A clean card-based article waterfall with feed filtering, read-status tracking, and drawer-style full article reading.

![Article Stream](docs/images/articles_view.png)

</div>

---

### Method 1: Docker Compose (Recommended)

Create a `docker-compose.yml` file:

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
      - RSS_BASE_URL=http://localhost:8001  # External URL (e.g. https://rss.example.com)
      - RSS_FULL_CONTEXT=True               # Include full HTML article content in feed
      - GATHER.CONTENT=True                 # Download and clean full article body
      - GATHER.MODEL=weread_mp              # Recommended collection engine
      - SPAN_INTERVAL=15                    # Periodic sync interval in minutes
    volumes:
      - ./data:/app/data
```

Start the container:

```bash
docker compose up -d
```

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

## 🔑 Default Credentials

- **Web Dashboard**: `http://<your-server-ip>:8001`
- **Default Username**: `admin`
- **Default Password**: `admin@123`

> [!TIP]
> - WeFeed is designed as a **self-hosted personal feed aggregator**. To protect privacy and prevent abuse of WeChat scraping quotas, public sign-ups are disabled by default.
> - You can override the default administrator credentials anytime via the `USERNAME` and `PASSWORD` environment variables in your `docker-compose.yml`.

---

## 📖 Usage Guide

### 1. Authorize WeRead (Recommended Engine)
1. Log into the WeFeed dashboard and navigate to **WeRead Management** in the sidebar.
2. Click **Scan QR Code** and scan with WeChat to link your primary account.
3. *(Optional)* Click **Scan QR Code (Add Account)** to link backup accounts. When the primary account reaches its daily quota, WeFeed rotates automatically to ensure uninterrupted updates.

### 2. Add and Subscribe to Official Accounts
1. Navigate to the **Feeds Management** page.
2. Search by account name to add feeds, or directly paste a WeChat article link for one-click resolution.
3. Newly added feeds will automatically queue for background synchronization.

### 3. Copy Feed URLs to Your RSS Reader
1. In the feed list or overview page, click the **Copy RSS / Atom** button on any feed card.
2. Copy the generated feed link (e.g., `http://<your-domain>:8001/feed/<MP_ID>.xml`).
3. Add the URL to your favorite reader (FreshRSS, Miniflux, Feedly, etc.) to enjoy clean WeChat updates.

---

## ⚙️ Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `USERNAME` | `admin` | Initial administrator username |
| `PASSWORD` | `admin@123` | Initial administrator password |
| `RSS_BASE_URL` | `http://localhost:8001` | Public base URL used for prefixing generated RSS feed links |
| `RSS_FULL_CONTEXT` | `True` | Whether to include full article content and images in feeds |
| `GATHER.MODEL` | `weread_mp` | Primary collection engine: `weread_mp` (recommended), `web`, or `app` |
| `GATHER.CONTENT` | `True` | Whether to fetch full article body during synchronization |
| `SPAN_INTERVAL` | `15` | Polling interval for automated scheduled synchronization (minutes) |
| `MAX_PAGE` | `1` | Maximum pagination depth per account run |
| `PROXY_URL` | *(empty)* | Optional outbound HTTP/SOCKS proxy when datacenter IPs are blocked |
| `SSO_TRUST_PROXY` | `False` | Trust upstream reverse proxy SSO authentication (e.g. Authelia / Nginx-UI) |
| `WEREAD_AUTO_KEEPALIVE` | `True` | Native in-container WeRead Cookie auto-keepalive via headless Chromium |

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
> *The original code from we-mp-rss is licensed under the MIT License. See [LICENSE](LICENSE) for details.*
