import unittest
import os
import json
import shutil
from storage import Storage, Video

class TestStorage(unittest.TestCase):
    def setUp(self):
        # 使用暫存測試目錄
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_data")
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "analysis"), exist_ok=True)
        
        # 覆蓋 Storage 中的路徑常量 (需謹慎，此處假設 Storage 可透過傳參或環境變數自訂路徑，
        # 但目前 storage.py 是寫死的，所以我們手動模擬一個測試場景)
        self.db_path = os.path.join(self.test_dir, "database.json")
        self.s = Storage()
        self.s.DB_PATH = self.db_path # 強制注入測試路徑
        self.s.videos = {}
        self.s.last_updated = ""

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_upsert_and_save(self):
        v = Video(id="test_v1", title="Test Video", url="http://test", date="20260101", channel="TestCh")
        # 測試新增
        result = self.s.upsert_video(v)
        self.assertTrue(result)
        self.assertEqual(len(self.s.videos), 1)
        
        # 測試重複新增 (應該回傳 False 代表未更新)
        result = self.s.upsert_video(v)
        self.assertFalse(result)
        
        # 測試存檔與讀取
        # 注意：Storage.save_database 使用寫死的 DATA_DIR，所以我們只測試記憶體內的狀態
        # 這裡主要是示範單元測試的邏輯
        self.assertEqual(self.s.videos["test_v1"].status, "pending")

    def test_aggregation(self):
        # 模擬數據
        self.s.videos = {
            "v1": Video(id="v1", title="V1", url="u1", date="20260520", channel="Ch1", status="analyzed")
        }
        # 模擬分析檔案邏輯需要 Mock 或更複雜的 Setup，此處測試基礎方法結構
        pending = self.s.get_pending_videos()
        self.assertEqual(len(pending), 0)

if __name__ == '__main__':
    unittest.main()
