import unittest
from datetime import datetime
from core.rss import RSS

class TestRSSFeedGeneration(unittest.TestCase):
    def setUp(self):
        self.rss = RSS(name="test_feed")

    def test_rss_with_and_without_images(self):
        items = [
            {
                "id": "1",
                "title": "Article with cover",
                "link": "https://example.com/1",
                "description": "Desc 1",
                "content": "<p>Content 1 <img src=\"https://mmbiz.qpic.cn/img1.jpg\"></p>",
                "image": "https://mmbiz.qpic.cn/cover1.jpg",
                "updated": datetime.now(),
                "mp_name": "TestMP"
            },
            {
                "id": "2",
                "title": "Article without cover",
                "link": "https://example.com/2",
                "description": "Desc 2",
                "content": "<p>Content 2</p>",
                "image": "",
                "updated": datetime.now(),
                "mp_name": "TestMP"
            }
        ]

        # Test RSS 2.0
        rss_xml = self.rss.generate_rss(items, title="Test", link="https://example.com")
        self.assertIn('xmlns:media="http://search.yahoo.com/mrss/"', rss_xml)
        self.assertIn('<media:thumbnail url="https://mmbiz.qpic.cn/cover1.jpg"', rss_xml)
        self.assertIn('<media:content url="https://mmbiz.qpic.cn/cover1.jpg" medium="image"', rss_xml)
        self.assertIn('<enclosure url="https://mmbiz.qpic.cn/cover1.jpg"', rss_xml)
        # Article 2 must NOT have empty enclosure
        self.assertNotIn('<enclosure url=""', rss_xml)
        self.assertNotIn('<media:thumbnail url=""', rss_xml)

        # Test Atom
        atom_xml = self.rss.generate_atom(items, title="Test", link="https://example.com")
        self.assertIn('xmlns:media="http://search.yahoo.com/mrss/"', atom_xml)
        self.assertIn('<link rel="enclosure" type="image/jpeg" href="https://mmbiz.qpic.cn/cover1.jpg"', atom_xml)
        self.assertIn('<media:thumbnail url="https://mmbiz.qpic.cn/cover1.jpg"', atom_xml)
        # Atom must NOT have empty link or enclosure
        self.assertNotIn('<link rel="enclosure" type="image/jpeg" href=""', atom_xml)
        self.assertNotIn('<enclosure', atom_xml)

        # Check referrerpolicy
        self.assertIn('referrerpolicy="no-referrer"', rss_xml)
        self.assertIn('referrerpolicy="no-referrer"', atom_xml)
        print("RSS and Atom feed generation tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
