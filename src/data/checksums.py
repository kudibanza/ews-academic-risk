"""
Compute SHA-256 checksums for OULAD raw files and record a manifest.
Run from project root: python -m src.data.checksums
"""
import hashlib
import csv
from pathlib import Path
from datetime import date

RAW_DIR = Path("data/raw")
MANIFEST = RAW_DIR / "checksums_manifest.csv"
FILES = [
    "courses.csv",
    "assessments.csv",
    "vle.csv",
    "studentAssessment.csv",
    "studentVle.csv",
    "studentInfo.csv",
    "studentRegistration.csv",
]
SOURCE = "UCI ML Repository, OULAD, DOI 10.24432/C5KK69"
CHUNK_SIZE = 1 << 20  # 1 MB


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    rows = []
    for name in FILES:
        path = RAW_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")
        size = path.stat().st_size
        digest = sha256(path)
        rows.append({
            "file": name,
            "size_bytes": size,
            "sha256": digest,
            "source": SOURCE,
            "date": date.today().isoformat(),
        })
        print(f"{name:30s} {size:>12,d} bytes  {digest}")

    with MANIFEST.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "size_bytes", "sha256", "source", "date"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nManifest written to {MANIFEST}")


if __name__ == "__main__":
    main()