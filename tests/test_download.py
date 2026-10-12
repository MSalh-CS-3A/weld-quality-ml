"""Offline checks for reproducibility and preserving original source files."""

import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import download_data as download


def make_archive(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, content in entries.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.contents = {
            "welddb.data": b"1 N MMA\n",
            "welddb.info": b"Documentation\n",
            "welddb.tex": b"TeX documentation\n",
        }
        self.archive = make_archive(self.contents)

    def test_first_download_and_offline_rerun(self):
        output = self.root / "raw"
        with (
            patch.object(download, "ARCHIVE_SHA256", download.sha256(self.archive)),
            patch.object(download, "urlopen", return_value=io.BytesIO(self.archive)) as network,
        ):
            download.download_data(output)
            manifest = (output / "manifest.json").read_bytes()
            network.assert_called_once()
            network.reset_mock()
            download.download_data(output)
            network.assert_not_called()
            self.assertEqual((output / "manifest.json").read_bytes(), manifest)
        for filename, content in self.contents.items():
            self.assertEqual((output / filename).read_bytes(), content)

    def test_bad_download_is_not_saved(self):
        with patch.object(download, "urlopen", return_value=io.BytesIO(b"incomplete")):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                download.download_data(self.root)
        self.assertFalse((self.root / "welddb.tar").exists())

    def test_changed_raw_file_is_preserved(self):
        (self.root / "welddb.tar").write_bytes(self.archive)
        (self.root / "welddb.data").write_bytes(b"local edits")
        with patch.object(download, "ARCHIVE_SHA256", download.sha256(self.archive)):
            with self.assertRaisesRegex(ValueError, "never overwritten"):
                download.download_data(self.root)
        self.assertEqual((self.root / "welddb.data").read_bytes(), b"local edits")
        self.assertFalse((self.root / "welddb.info").exists())

    def test_archive_cannot_write_outside_output_directory(self):
        path = self.root / "unsafe.tar"
        path.write_bytes(make_archive({"../escape.txt": b"bad"}))
        with self.assertRaisesRegex(ValueError, "expected regular files"):
            download.read_archive(path)
        self.assertFalse((self.root.parent / "escape.txt").exists())

    def test_links_are_rejected(self):
        path = self.root / "links.tar"
        with tarfile.open(path, mode="w") as archive:
            for filename in download.EXPECTED_FILES:
                member = tarfile.TarInfo(filename)
                member.type = tarfile.SYMTYPE
                member.linkname = "/tmp/other-file"
                archive.addfile(member)
        with self.assertRaisesRegex(ValueError, "expected regular files"):
            download.read_archive(path)


if __name__ == "__main__":
    unittest.main()
