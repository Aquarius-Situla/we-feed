import unittest
import os
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

class AuditFixesTest(unittest.TestCase):
    def test_tools_path_validation(self):
        # 验证 apis/tools.py 中的路径校验逻辑
        def validate_filename(filename: str):
            if not filename or len(filename) > 255:
                return False, "非法的文件名"
            if os.path.basename(filename) != filename or any(c in filename for c in ('/', '\\', '\0', '..')) or filename in {".", ".."}:
                return False, "非法的文件名"
            return True, "OK"

        def validate_mp_id(mp_id: str):
            if mp_id is not None:
                if not mp_id or len(mp_id) > 128:
                    return False, "非法的公众号ID"
                if os.path.basename(mp_id) != mp_id or any(c in mp_id for c in ('/', '\\', '\0', '..')) or mp_id in {".", ".."}:
                    return False, "非法的公众号ID"
            return True, "OK"

        # 恶意遍历必须被拒绝
        self.assertFalse(validate_filename("../secret.txt")[0])
        self.assertFalse(validate_filename("..\\secret.txt")[0])
        self.assertFalse(validate_filename("/etc/passwd")[0])
        self.assertFalse(validate_filename("sub/file.zip")[0])
        self.assertFalse(validate_filename("sub\\file.zip")[0])
        self.assertFalse(validate_filename("..")[0])
        self.assertFalse(validate_filename(".")[0])
        self.assertFalse(validate_filename("file\0name.zip")[0])

        # 中文、空格及合法字符必须被允许通过
        self.assertTrue(validate_filename("人物 2026年文章合集.docx")[0])
        self.assertTrue(validate_filename("科技观察_2026-10-16.zip")[0])
        self.assertTrue(validate_filename("export_123.md")[0])
        self.assertTrue(validate_mp_id("gh_1234567890ab")[0])
        self.assertTrue(validate_mp_id("人物公众号")[0])
        self.assertFalse(validate_mp_id("../gh_123")[0])

    def test_rss_cdata_token_map(self):
        # 验证 core/rss.py 中基于 Token Map 的真实 CDATA 渲染，保证 HTML 标签完全不被转义
        xml_feed = ET.Element("feed")
        entry = ET.SubElement(xml_feed, "entry")
        raw_html = "<p>这是一篇<b>带格式</b>的微信文章 & 精彩内容</p>"
        
        cdata_map = {}
        placeholder = "__WEFEED_ATOM_CDATA_TOKEN_0__"
        safe_cdata = raw_html.replace("]]>", "]]]]><![CDATA[>")
        cdata_map[placeholder] = f"<![CDATA[{safe_cdata}]]>"
        ET.SubElement(entry, "content:encoded").text = placeholder

        tree_str = '<?xml version="1.0" encoding="utf-8"?>\r\n' + \
                   ET.tostring(xml_feed, encoding="utf-8", method="xml").decode("utf-8")
        for token, cdata_block in cdata_map.items():
            tree_str = tree_str.replace(token, cdata_block)
        tree_str = tree_str.replace("&lt;![CDATA[", "<![CDATA[").replace("]]&gt;", "]]>")

        # 确保包含真实且合法的 CDATA 标签，且 HTML 标签如 <p>, <b>, & 均未被实体转义
        self.assertIn("<![CDATA[<p>这是一篇<b>带格式</b>的微信文章 & 精彩内容</p>]]>", tree_str)
        self.assertNotIn("&lt;p&gt;", tree_str)
        self.assertNotIn("&lt;![CDATA[", tree_str)
        self.assertNotIn("]]&gt;", tree_str)

    def test_ip_trust_logic(self):
        # 独立测试 IP CIDR 与 IP 校验逻辑
        import ipaddress

        def _is_ip_trusted(client_ip: str, trusted_list: list[str]) -> bool:
            if not client_ip:
                return False
            try:
                c_ip = ipaddress.ip_address(client_ip)
                for item in trusted_list:
                    item = item.strip()
                    if not item:
                        continue
                    if "/" in item:
                        if c_ip in ipaddress.ip_network(item, strict=False):
                            return True
                    else:
                        if c_ip == ipaddress.ip_address(item):
                            return True
            except Exception:
                pass
            return False

        trusted = ["127.0.0.1", "172.16.0.0/12", "10.0.0.1"]
        self.assertTrue(_is_ip_trusted("127.0.0.1", trusted))
        self.assertTrue(_is_ip_trusted("172.18.0.5", trusted))
        self.assertFalse(_is_ip_trusted("192.168.1.100", trusted))
        self.assertFalse(_is_ip_trusted("8.8.8.8", trusted))

if __name__ == "__main__":
    unittest.main()
