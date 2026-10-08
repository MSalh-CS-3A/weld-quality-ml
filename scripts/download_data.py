"""Download and verify the original Cambridge welding database using stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

SOURCE_PAGE = "https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html"
ARCHIVE_URL = "https://www.phase-trans.msm.cam.ac.uk/map/data/tar/welddb.tar"
ARCHIVE_SHA256 = "493b2ec7c2e46e93260040194d86ae35fb8579802c048f94f89539d466b7e6ca"
EXPECTED_FILES = {"welddb.data", "welddb.info", "welddb.tex"}
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def sha256(content: bytes) -> str:
    """Return a checksum for original archive or extracted file bytes."""
    return hashlib.sha256(content).hexdigest()


def verify_archive(content: bytes) -> None:
    """Reject changed or incomplete archives before saving or extracting them."""
    actual = sha256(content)
    if actual != ARCHIVE_SHA256:
        raise ValueError(
            f"Archive checksum mismatch: expected {ARCHIVE_SHA256}, got {actual}. "
            "The archive may be incomplete or the upstream dataset may have changed."
        )


def read_archive(path: Path) -> dict[str, bytes]:
    """Read only the three expected regular files, without extracting tar paths."""
    with tarfile.open(path, mode="r:*") as archive:
        members = archive.getmembers()
        if (
            len(members) != len(EXPECTED_FILES)
            or {member.name for member in members} != EXPECTED_FILES
            or any(not member.isfile() for member in members)
        ):
            raise ValueError("Archive must contain exactly the three expected regular files.")
        contents = {}
        for member in members:
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"Could not read {member.name} from the archive.")
            with stream:
                contents[member.name] = stream.read()
        return contents


def atomic_write(path: Path, content: bytes) -> None:
    """Stage bytes in the destination directory before publishing the file."""
    with tempfile.TemporaryDirectory(prefix=".download-", dir=path.parent) as directory:
        temporary = Path(directory) / path.name
        temporary.write_bytes(content)
        temporary.replace(path)


def download_data(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Download once, verify cached data, and preserve existing unmodified files."""
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "welddb.tar"

    if archive_path.exists():
        verify_archive(archive_path.read_bytes())
        print(f"Verified cached archive: {archive_path}")
    else:
        print(f"Downloading {ARCHIVE_URL}", flush=True)
        with urlopen(ARCHIVE_URL, timeout=30) as response:
            content = response.read()
        verify_archive(content)
        atomic_write(archive_path, content)

    contents = read_archive(archive_path)
    # Check all existing files before writing any extracted files.
    for filename, content in contents.items():
        path = output_dir / filename
        if path.exists() and path.read_bytes() != content:
            raise ValueError(
                f"Existing file differs from the source: {path}. "
                "Move it aside before rerunning; raw files are never overwritten."
            )

    for filename, content in contents.items():
        path = output_dir / filename
        if not path.exists():
            atomic_write(path, content)

    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        manifest = {
            "source_page": SOURCE_PAGE,
            "archive_url": ARCHIVE_URL,
            "archive_sha256": ARCHIVE_SHA256,
            "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
            "files": {
                filename: {"bytes": len(content), "sha256": sha256(content)}
                for filename, content in sorted(contents.items())
            },
        }
        atomic_write(manifest_path, (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))

    print(f"Dataset ready: {output_dir / 'welddb.data'}")
    return output_dir


def main() -> int:
    """Run the downloader from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help="Destination directory (default: this repository's data/raw).",
    )
    args = parser.parse_args()
    try:
        download_data(args.output_dir)
    except (OSError, URLError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f"Download failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
