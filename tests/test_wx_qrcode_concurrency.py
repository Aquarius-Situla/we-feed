import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if "redis" not in sys.modules:
    sys.modules["redis"] = MagicMock()

from driver.wx import Wx


class WxQrcodeConcurrencyTest(unittest.TestCase):
    def setUp(self):
        self.wx = Wx()
        self.wx.wx_login_url = "tests/test_wx_qrcode.png"
        self.wx.lock_file_path = "tests/test_wx_lock.lock"
        self.cleanup_files()

    def tearDown(self):
        self.cleanup_files()

    def cleanup_files(self):
        for path in [self.wx.wx_login_url, self.wx.lock_file_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_check_lock_when_thread_is_running(self):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        self.wx.thread = mock_thread

        self.assertTrue(self.wx.is_running())
        self.assertTrue(self.wx.check_lock())

    def test_check_lock_when_thread_dead_and_no_lock_file(self):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        self.wx.thread = mock_thread

        self.assertFalse(self.wx.is_running())
        self.assertFalse(self.wx.check_lock())

    def test_check_lock_cleans_expired_lock(self):
        self.wx.thread = None
        os.makedirs(os.path.dirname(self.wx.lock_file_path), exist_ok=True)
        # 写入 400 秒前生成的过期锁
        expired_time = time.time() - 400
        with open(self.wx.lock_file_path, "w") as f:
            f.write(f"999999|{expired_time}")

        self.assertFalse(self.wx.check_lock(timeout=300))
        self.assertFalse(os.path.exists(self.wx.lock_file_path))

    def test_gethascode_size_threshold(self):
        # 1. 文件不存在
        self.assertFalse(self.wx.GetHasCode())

        # 2. 文件小于或等于 364 字节（空或损坏）
        with open(self.wx.wx_login_url, "wb") as f:
            f.write(b"x" * 100)
        self.assertFalse(self.wx.GetHasCode())

        # 3. 正常图片文件（大于 364 字节）
        with open(self.wx.wx_login_url, "wb") as f:
            f.write(b"x" * 1000)
        self.assertTrue(self.wx.GetHasCode())

    def test_qrcode_and_qrstatus_structure(self):
        self.wx.thread = None
        with open(self.wx.wx_login_url, "wb") as f:
            f.write(b"x" * 1000)

        qrcode_data = self.wx.QRcode()
        self.assertTrue(qrcode_data["is_exists"])
        self.assertFalse(qrcode_data["is_running"])
        self.assertIn("tests/test_wx_qrcode.png", qrcode_data["code"])

        status_data = self.wx.QrStatus()
        self.assertTrue(status_data["qr_code"])
        self.assertFalse(status_data["is_running"])
        self.assertIn("tests/test_wx_qrcode.png", status_data["code_url"])

    def test_getcode_concurrency_blocks_duplicate_threads(self):
        # 模拟已有线程在运行
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        self.wx.thread = mock_thread

        with patch("core.thread.ThreadManager") as mock_tm:
            res = self.wx.GetCode()
            # 不能重新创建和启动新线程
            mock_tm.assert_not_called()
            self.assertTrue(res["is_running"])
            self.assertIn("请勿重复运行", res["msg"])

    def test_check_lock_reclaims_stale_lock_from_current_process(self):
        # 锁文件属于当前进程，但活跃线程已死亡
        self.wx.thread = None
        os.makedirs(os.path.dirname(self.wx.lock_file_path), exist_ok=True)
        # 写入几秒前由当前进程写入的锁
        with open(self.wx.lock_file_path, "w") as f:
            f.write(f"{os.getpid()}|{time.time()}")

        # 不应误判为仍有效，而应识别为本进程残留失效锁并自动清理释放
        self.assertFalse(self.wx.check_lock(timeout=300))
        self.assertFalse(os.path.exists(self.wx.lock_file_path))

    def test_release_lock_exact_pid_matching(self):
        # 锁文件由其他进程持有（如当前 PID + 999）
        other_pid = os.getpid() + 999
        os.makedirs(os.path.dirname(self.wx.lock_file_path), exist_ok=True)
        with open(self.wx.lock_file_path, "w") as f:
            f.write(f"{other_pid}|{time.time()}")

        # 当前进程调用 release_lock 不应误删其他进程的锁
        self.wx.release_lock()
        self.assertTrue(os.path.exists(self.wx.lock_file_path))

    def test_getcode_resets_haslogin_synchronously(self):
        self.wx._haslogin = True
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        self.wx.thread = mock_thread

        # 即使被并发检查拦截，GetCode 也会在同步入口重置 _haslogin
        self.wx.GetCode()
        self.assertFalse(self.wx.HasLogin())


if __name__ == "__main__":
    unittest.main()
