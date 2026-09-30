import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts import model_manager as manager


class ModelManagerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "manifests").mkdir()
        self.data = bytes(range(251)) * 5
        self.original = self.root / "models" / "test.bin"
        self.original.parent.mkdir()
        self.original.write_bytes(self.data)
        self.item = {"id": "test", "path": "models/test.bin", "bytes": len(self.data),
                     "sha256": hashlib.sha256(self.data).hexdigest(), "profiles": ["video"]}
        (self.root / "manifests/models.json").write_text(
            json.dumps({"version": 1, "files": [self.item]}))

    def test_roundtrip_and_corruption(self):
        transport = self.root / "manifests/transport.json"
        manager.pack(self.root, [self.item], 100, transport)
        chunks = manager.load_manifest(transport)["files"]
        self.assertEqual(len(chunks[0]["chunks"]), 13)
        manager.verify_transport(self.root, chunks)
        self.original.unlink()
        manager.restore(self.root, chunks, False)
        self.assertEqual(self.original.read_bytes(), self.data)
        self.original.unlink()
        first = manager.safe_path(self.root, chunks[0]["chunks"][0]["path"])
        first.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "chunk checksum mismatch"):
            manager.restore(self.root, chunks, False)
        self.assertFalse(self.original.exists())

    def test_detect_lfs_pointer(self):
        transport = self.root / "manifests/transport.json"
        manager.pack(self.root, [self.item], 100, transport)
        chunks = manager.load_manifest(transport)["files"]
        first = manager.safe_path(self.root, chunks[0]["chunks"][0]["path"])
        first.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 100\n")
        with self.assertRaisesRegex(ValueError, "LFS pointer"):
            manager.verify_transport(self.root, chunks)

    def test_existing_invalid_file_requires_repair(self):
        transport = self.root / "manifests/transport.json"
        manager.pack(self.root, [self.item], 100, transport)
        chunks = manager.load_manifest(transport)["files"]
        self.original.write_bytes(b"invalid")
        with self.assertRaisesRegex(ValueError, "--repair"):
            manager.restore(self.root, chunks, False)
        self.assertEqual(self.original.read_bytes(), b"invalid")
        manager.restore(self.root, chunks, True)
        self.assertEqual(self.original.read_bytes(), self.data)

    def test_reject_path_escape(self):
        with self.assertRaises(ValueError):
            manager.safe_path(self.root, "../private.bin")
        with self.assertRaises(ValueError):
            manager.safe_path(self.root, "/private.bin")
        outside = self.root.parent / "outside"
        (self.root / "escape").symlink_to(outside)
        with self.assertRaises(ValueError):
            manager.safe_path(self.root, "escape/file.bin")


if __name__ == "__main__":
    unittest.main()
