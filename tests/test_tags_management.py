import unittest
import json
from core.tag_util import parse_mps_ids, format_tag_dict



class TagsManagementTest(unittest.TestCase):
    def test_parse_mps_ids_variations(self):
        # 1. 空值或空列表
        self.assertEqual(parse_mps_ids(None), [])
        self.assertEqual(parse_mps_ids(""), [])
        self.assertEqual(parse_mps_ids("[]"), [])
        self.assertEqual(parse_mps_ids([]), [])

        # 2. 纯字符串 ID 列表
        str_list = ["mp_001", "mp_002"]
        self.assertEqual(parse_mps_ids(str_list), ["mp_001", "mp_002"])
        self.assertEqual(parse_mps_ids(json.dumps(str_list)), ["mp_001", "mp_002"])

        # 3. 字典对象列表 [{"id": "mp_001", "name": "科技"}]
        dict_list = [{"id": "mp_001", "name": "科技"}, {"id": "mp_002"}]
        self.assertEqual(parse_mps_ids(dict_list), ["mp_001", "mp_002"])
        self.assertEqual(parse_mps_ids(json.dumps(dict_list)), ["mp_001", "mp_002"])

        # 4. 混合类型列表 [123, "mp_004", {"id": "mp_005"}]
        mixed_list = [123, "mp_004", {"id": "mp_005"}]
        self.assertEqual(parse_mps_ids(mixed_list), ["123", "mp_004", "mp_005"])
        self.assertEqual(parse_mps_ids(json.dumps(mixed_list)), ["123", "mp_004", "mp_005"])

        # 5. 非法 JSON
        self.assertEqual(parse_mps_ids("invalid-json-string"), [])

    def test_format_tag_dict(self):
        class DummyTag:
            id = "tag-123"
            name = "深度阅读"
            cover = "http://example.com/cover.png"
            intro = "高质量公众号合集"
            status = 1
            mps_id = json.dumps(["mp_1", "mp_2"])
            created_at = None
            updated_at = None

        formatted = format_tag_dict(DummyTag())
        self.assertEqual(formatted["id"], "tag-123")
        self.assertEqual(formatted["name"], "深度阅读")
        self.assertEqual(formatted["mps_list"], ["mp_1", "mp_2"])
        self.assertEqual(formatted["mp_count"], 2)

    def test_tag_name_validation(self):
        # 标签名称不能为空或纯空白字符
        invalid_names = [None, "", "   ", "\t\n"]
        for name in invalid_names:
            is_valid = bool(name and name.strip())
            self.assertFalse(is_valid)

        valid_names = ["科技", " 财经资讯 ", "A"]
        for name in valid_names:
            is_valid = bool(name and name.strip())
            self.assertTrue(is_valid)

if __name__ == "__main__":
    unittest.main()
