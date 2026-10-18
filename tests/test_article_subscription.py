import unittest
import re
import html
from urllib.parse import urlparse

def validate_wechat_article_url(clean_url: str):
    parsed = urlparse((clean_url or "").strip())
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not (
        hostname == "mp.weixin.qq.com" or hostname == "weixin.qq.com" or hostname.endswith(".weixin.qq.com")
    ):
        return False, "链接无效，必须为微信公众号文章链接 (以 https://mp.weixin.qq.com 开头)"
    return True, "OK"


def extract_mp_info_from_html(resp_text: str) -> dict:
    mp_info = {
        "mp_name": "",
        "biz": "",
        "logo": "",
        "title": ""
    }
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

    return mp_info


def sanitize_proxy_url(proxy_setting: str, enabled: bool) -> str:
    raw_proxy = proxy_setting if enabled else None
    return raw_proxy.strip() if (raw_proxy and isinstance(raw_proxy, str) and raw_proxy.strip()) else None


class TestArticleSubscription(unittest.TestCase):
    def test_extract_mp_info_standard_wechat(self):
        sample_html = """
        <html>
        <head>
            <meta property="og:title" content="测试微信文章" />
            <meta property="og:article:author" content="科技探索" />
            <meta property="og:image" content="https://mmbiz.qpic.cn/avatar.png" />
            <script>
                var biz = "MjM5ODUxOTQ2NA==";
                var nickname = "科技探索";
                var round_head_img = "https://mmbiz.qpic.cn/avatar.png";
            </script>
        </head>
        <body>
            <div id="js_wx_follow_nickname">科技探索</div>
        </body>
        </html>
        """
        info = extract_mp_info_from_html(sample_html)
        self.assertEqual(info.get("mp_name"), "科技探索")
        self.assertEqual(info.get("biz"), "MjM5ODUxOTQ2NA==")
        self.assertEqual(info.get("logo"), "https://mmbiz.qpic.cn/avatar.png")
        self.assertEqual(info.get("title"), "测试微信文章")

    def test_extract_mp_info_html_entities(self):
        sample_html = """
        <html>
        <head>
            <meta property="og:title" content="AI &amp; &quot;大模型&quot; 前沿" />
            <meta property="og:article:author" content="Tom &amp; Jerry 探索室" />
            <script>
                var biz = "MzA4MzA2ODQ4MQ==";
                var nickname = "Tom &amp; Jerry 探索室";
            </script>
        </head>
        <body></body>
        </html>
        """
        info = extract_mp_info_from_html(sample_html)
        self.assertEqual(info.get("mp_name"), "Tom & Jerry 探索室")
        self.assertEqual(info.get("title"), 'AI & "大模型" 前沿')

    def test_ssrf_and_domain_validation(self):
        # 恶意的 SSRF / 内网或非法域名必须被拦截
        self.assertFalse(validate_wechat_article_url("http://192.168.1.1/admin")[0])
        self.assertFalse(validate_wechat_article_url("http://169.254.169.254/latest/meta-data/")[0])
        self.assertFalse(validate_wechat_article_url("http://localhost:8001/")[0])
        self.assertFalse(validate_wechat_article_url("https://evil.com/s/fake_article")[0])
        self.assertFalse(validate_wechat_article_url("ftp://mp.weixin.qq.com/s/123")[0])

        # 合法微信链接放行
        self.assertTrue(validate_wechat_article_url("https://mp.weixin.qq.com/s/3u8o_hh88fJwiPn_WH_B2g")[0])
        self.assertTrue(validate_wechat_article_url("http://weixin.qq.com/r/abcdef")[0])

    def test_extract_mp_info_htmldecode_and_junk_author(self):
        # 针对微信最新文章页结构：var nickname = htmlDecode("清华大学附属中学")
        # 且作者字段被编辑填写为 "点击蓝字关注"，应准确提取出公众号名称而非噪音词
        sample_html = """
        <html>
        <head>
            <meta name="author" content="点击蓝字关注" />
            <meta property="og:article:author" content="点击蓝字关注" />
            <meta property="og:title" content="清华附中百年校庆" />
            <meta property="og:image" content="https://mmbiz.qpic.cn/tsinghua.png" />
            <script>
                var biz = "MjM5ODUwMTk0Nw==";
                var nickname = htmlDecode("清华大学附属中学");
                var round_head_img = "https://mmbiz.qpic.cn/tsinghua.png";
            </script>
        </head>
        <body>
            <span id="js_author_name_text">点击蓝字关注</span>
            <a class="wx_tap_link" id="js_name">
                清华大学附属中学
            </a>
        </body>
        </html>
        """
        info = extract_mp_info_from_html(sample_html)
        self.assertEqual(info.get("mp_name"), "清华大学附属中学")
        self.assertEqual(info.get("biz"), "MjM5ODUwMTk0Nw==")
        self.assertEqual(info.get("logo"), "https://mmbiz.qpic.cn/tsinghua.png")

    def test_extract_mp_info_js_name_fallback_with_junk_author(self):
        # 当缺少 JS 变量时，根据 DOM #js_name 准确提取，并跳过含“蓝字关注”的 og:article:author
        sample_html = """
        <html>
        <head>
            <meta property="og:article:author" content="请点击蓝字关注我们" />
            <meta property="og:title" content="每日精选" />
            <script>
                var biz = "MjM5ODUwMTk0Nw==";
            </script>
        </head>
        <body>
            <a id="js_name">
                北京大学招生办
            </a>
        </body>
        </html>
        """
        info = extract_mp_info_from_html(sample_html)
        self.assertEqual(info.get("mp_name"), "北京大学招生办")


if __name__ == '__main__':
    unittest.main()
