import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("chunk_d1.py")


def load_module():
    spec = importlib.util.spec_from_file_location("chunk_d1", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChunkD1Test(unittest.TestCase):
    def test_chunks_by_level_4_heading_with_context_headings(self):
        chunk_d1 = load_module()
        source = """Intro ignored
## Chương 1: Nhóm A
### BỆNH A
#### 1. ĐẠI CƯƠNG
Nội dung A1
##### 1.1. Nhỏ
Chi tiết A1
###### 1.1.1. Rất nhỏ
Chi tiết A1.1
#### 2. CHẨN ĐOÁN
Nội dung A2
### BỆNH B
#### 1. ĐẠI CƯƠNG
Nội dung B1
"""

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample.md"
            out = Path(tmp) / "chunks.jsonl"
            src.write_text(source, encoding="utf-8")

            chunks = chunk_d1.chunk_file(src, out)
            records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(chunks), 3)
        self.assertEqual([r["section"] for r in records], ["1. ĐẠI CƯƠNG", "2. CHẨN ĐOÁN", "1. ĐẠI CƯƠNG"])
        self.assertTrue(records[0]["text"].startswith("BỆNH A\nĐẠI CƯƠNG\n"))
        self.assertNotIn("## Chương 1: Nhóm A", records[0]["text"])
        self.assertNotIn("###", records[0]["text"])
        self.assertNotIn("####", records[0]["text"])
        self.assertNotIn("##### 1.1. Nhỏ", records[0]["text"])
        self.assertIn("1.1 Nhỏ", records[0]["text"])
        self.assertNotIn("###### 1.1.1. Rất nhỏ", records[0]["text"])
        self.assertIn("1.1.1 Rất nhỏ", records[0]["text"])
        self.assertNotIn("#### 2. CHẨN ĐOÁN", records[0]["text"])
        self.assertEqual(records[2]["disease"], "BỆNH B")


if __name__ == "__main__":
    unittest.main()
