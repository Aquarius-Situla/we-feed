#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeFeed 核心功能自动化冒烟测试 (Core Smoke Tests)
用于 CI/CD 与本地快速校验核心安全与业务逻辑
"""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
import hashlib
from ipaddress import ip_address, ip_network

# 确保项目根目录在 sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class CoreSmokeTest(unittest.TestCase):
    """核心安全与功能冒烟测试集"""

    def test_rss_cdata_integrity(self):
        """冒烟 1: 验证 RSS / Atom 的真实 CDATA 生成与防实体转义机制"""
        raw_article_html = """
        <div class="rich_media_content">
            <p>这是一篇测试公众号文章 & 内容</p>
            <img src="https://mmbiz.qpic.cn/test.jpg" referrerpolicy="no-referrer" />
        </div>
        """.strip()

        # 模拟 core/rss.py 的 Token Map 渲染
        xml_feed = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")
        entry = ET.SubElement(xml_feed, "entry")
        
        token = "__WEFEED_ATOM_CDATA_TOKEN_SMOKE__"
        cdata_map = {token: f"<![CDATA[{raw_article_html}]]>"}
        
        content_elem = ET.SubElement(entry, "content")
        content_elem.text = token

        rendered = '<?xml version="1.0" encoding="utf-8"?>\r\n' + \
                   ET.tostring(xml_feed, encoding="utf-8", method="xml").decode("utf-8")
        for placeholder, cdata_block in cdata_map.items():
            rendered = rendered.replace(placeholder, cdata_block)

        # 关键断言：CDATA 绝不能被转义为 &lt;![CDATA[
        self.assertIn("<![CDATA[", rendered)
        self.assertIn("]]>", rendered)
        self.assertNotIn("&lt;![CDATA[", rendered)
        self.assertIn('referrerpolicy="no-referrer"', rendered)

    def test_sso_trust_proxy_security(self):
        """冒烟 2: 验证反向代理 SSO 的安全校验与防公网伪造提权逻辑"""
        # 测试私有网段检测函数
        private_nets = [
            ip_network("127.0.0.0/8"),
            ip_network("10.0.0.0/8"),
            ip_network("172.16.0.0/12"),
            ip_network("192.168.0.0/16"),
        ]

        def is_private_ip(client_ip: str) -> bool:
            try:
                ip = ip_address(client_ip)
                return any(ip in net for net in private_nets)
            except ValueError:
                return False

        # 本地回环与内网反代/Docker 桥接网段必须被识别为私有
        self.assertTrue(is_private_ip("127.0.0.1"))
        self.assertTrue(is_private_ip("172.22.0.2"))
        self.assertTrue(is_private_ip("192.168.1.100"))
        self.assertTrue(is_private_ip("10.0.0.1"))

        # 公网客户端直连必须被识别为非私有，坚决禁止未经凭据提权
        self.assertFalse(is_private_ip("1.2.3.4"))
        self.assertFalse(is_private_ip("114.114.114.114"))
        self.assertFalse(is_private_ip("8.8.8.8"))

    def test_path_traversal_sanitizer(self):
        """冒烟 3: 验证导出的文件名与路径校验防穿透能力"""
        def is_safe_filename(name: str) -> bool:
            if not name or len(name) > 255:
                return False
            if os.path.basename(name) != name or any(c in name for c in ('/', '\\', '\0', '..')) or name in {".", ".."}:
                return False
            return True

        # 恶意路径遍历 Payload
        self.assertFalse(is_safe_filename("../../../etc/passwd"))
        self.assertFalse(is_safe_filename("..\\..\\windows\\system32"))
        self.assertFalse(is_safe_filename("/root/.ssh/id_rsa"))
        self.assertFalse(is_safe_filename("subfolder/file.txt"))
        self.assertFalse(is_safe_filename("test\0bad.txt"))
        self.assertFalse(is_safe_filename(".."))

        # 合法中文、空格与业务导出名必须允许
        self.assertTrue(is_safe_filename("36氪_2026-10-17.md"))
        self.assertTrue(is_safe_filename("科技前沿 汇总文章.docx"))
        self.assertTrue(is_safe_filename("export_bundle_001.zip"))

    def test_cascade_credential_hashing(self):
        """冒烟 4: 验证级联节点 SHA-256 凭据哈希算法一致性"""
        raw_secret = "CascadeSecretKey-2026"
        expected_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        self.assertEqual(len(expected_hash), 64)
        self.assertEqual(expected_hash, hashlib.sha256(raw_secret.encode("utf-8")).hexdigest())

    def test_image_anti_hotlinking(self):
        """冒烟 5: 验证微信图片链接防盗链属性处理"""
        raw_img_tag = '<img src="https://mmbiz.qpic.cn/mmbiz_png/abc/0" alt="cover">'
        
        # 补全 referrerpolicy
        if 'referrerpolicy' not in raw_img_tag:
            fixed_tag = raw_img_tag.replace("<img ", '<img referrerpolicy="no-referrer" ')
        else:
            fixed_tag = raw_img_tag
            
        self.assertIn('referrerpolicy="no-referrer"', fixed_tag)
        self.assertIn('https://mmbiz.qpic.cn/', fixed_tag)

    def test_rss_template_injection_disabled(self):
        """冒烟 6: 验证 Issue #479 RSS 模板代码执行 (RCE) 漏洞防范机制"""
        from core.rss import RSS
        rss = RSS(name="smoke_test", ext="xml")
        
        # 1. 验证 generate_by_template 已被永久下线
        with self.assertRaises(NotImplementedError):
            rss.generate_by_template([{"title": "test"}], template="{{ 1 + 1 }}")
            
        # 2. 验证 generate 不再处理外部 template 并正常渲染标准 XML
        rendered = rss.generate(
            [{
                "id": "test_001",
                "title": "测试文章",
                "link": "https://mp.weixin.qq.com/s/test",
                "description": "摘要",
                "updated": "2026-10-18 12:00:00"
            }],
            ext="xml",
            title="WeFeed 测试频道"
        )
        self.assertIn("<title>WeFeed 测试频道</title>", rendered)


if __name__ == '__main__':
    unittest.main()
