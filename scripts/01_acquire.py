import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifest.json"
LEDGER_PATH = DATA_DIR / "license_ledger.csv"

SOURCES = [
    {
        "doc_id": "cs_kaviratna_1890",
        "title": "Charaka-Samhita (Avinash Chandra Kaviratna 1890)",
        "download_url": "https://archive.org/download/BIUSante_47357/BIUSante_47357_djvu.txt",
        "dest_filename": "cs_kaviratna_1890.txt",
    },
    {
        "doc_id": "ss_bhishagratna_1907",
        "title": "Sushruta Samhita Vol 1 Sutrasthana (Kaviraj Kunja Lal Bhishagratna 1907)",
        "download_url": "https://archive.org/download/englishtranslati01susruoft/englishtranslati01susruoft_djvu.txt",
        "dest_filename": "ss_bhishagratna_1907.txt",
    },
]


def calculate_sha256(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def acquire():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_at": "2026-09-19", "sources": []}
    checksums = {}

    headers = {"User-Agent": "AyurCite/1.0.0 (Research Corpus Acquisition)"}

    for src in SOURCES:
        dest_path = RAW_DIR / src["dest_filename"]
        print(f"\n[Acquire] Downloading {src['title']}...")
        print(f"          URL: {src['download_url']}")

        req = urllib.request.Request(src["download_url"], headers=headers)
        with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out:
            data = resp.read()
            out.write(data)
            print(f"          Saved {len(data):,} bytes -> {dest_path.name}")

        sha256_hash = calculate_sha256(dest_path)
        file_size = dest_path.stat().st_size
        checksums[src["doc_id"]] = sha256_hash

        manifest["sources"].append(
            {
                "doc_id": src["doc_id"],
                "title": src["title"],
                "filename": src["dest_filename"],
                "url": src["download_url"],
                "sha256": sha256_hash,
                "bytes": file_size,
            }
        )
        print(f"          SHA256: {sha256_hash}")

    # Write data/manifest.json
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[Acquire] Manifest updated -> {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")

    # Update data/license_ledger.csv with sha256
    if LEDGER_PATH.exists():
        df = pd.read_csv(LEDGER_PATH)
        for doc_id, h in checksums.items():
            df.loc[df["doc_id"] == doc_id, "sha256"] = h
        df.to_csv(LEDGER_PATH, index=False)
        print(
            f"[Acquire] License ledger updated with SHA256 hashes -> {LEDGER_PATH.relative_to(PROJECT_ROOT)}"
        )


if __name__ == "__main__":
    acquire()
