#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import ssl
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


IMAGES_CSV = Path("audit/images_to_recover.csv")
REPORT_CSV = Path("audit/images_restore_report.csv")
PUBLIC_DIR = Path("public")
ARTICLES_DIR = Path("src/content/articles/en")
USER_AGENT = "allmedtests-wave1-image-restore/1.0"
ABO_ORIGINAL = "https://allmedtests.com/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png"
IMAGE_BACKLINKS = {
    "https://allmedtests.com/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png": 9,
}


@dataclass
class Snapshot:
    timestamp: str
    original: str
    mimetype: str


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = "https"
    host = (parsed.hostname or parsed.netloc).lower()
    if host.startswith("www."):
        host = host[4:]
    return f"{scheme}://{host}{parsed.path}"


def local_path_for(url: str) -> str:
    return urlparse(url).path


def fullsize_candidate(url: str) -> str | None:
    parsed = urlparse(url)
    path = re.sub(r"-\d+x\d+(\.[A-Za-z0-9]+)$", r"\1", parsed.path)
    if path == parsed.path:
        return None
    return f"https://allmedtests.com{path}"


def request_bytes(url: str, timeout: int = 25) -> bytes:
    ctx = ssl._create_unverified_context()
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout, context=ctx) as response:
        return response.read()


def request_json(url: str) -> list:
    return json.loads(request_bytes(url, timeout=20).decode("utf-8"))


def find_snapshot(url: str) -> Snapshot | None:
    candidates = [url]
    parsed = urlparse(url)
    if parsed.scheme == "https":
        candidates.append(f"http://allmedtests.com{parsed.path}")
    else:
        candidates.append(f"https://allmedtests.com{parsed.path}")

    for candidate in candidates:
        params = {
            "url": candidate,
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype",
            "filter": "statuscode:200",
            "sort": "reverse",
            "limit": "20",
        }
        cdx_url = f"https://web.archive.org/cdx/search/cdx?{urlencode(params)}"
        try:
            print(f"CDX {candidate}", flush=True)
            payload = request_json(cdx_url)
        except HTTPError as exc:
            if exc.code not in {429, 503, 504}:
                raise
            payload = []
        except (URLError, TimeoutError, json.JSONDecodeError):
            payload = []

        for row in payload[1:]:
            if len(row) < 4:
                continue
            timestamp, original, _status, mimetype = row[:4]
            if mimetype.startswith("image/") or mimetype == "application/octet-stream":
                return Snapshot(timestamp=timestamp, original=original, mimetype=mimetype)
        time.sleep(0.6)
    return None


def download_image(snapshot: Snapshot, destination: Path) -> bool:
    if destination.exists() and destination.stat().st_size > 0:
        return True
    destination.parent.mkdir(parents=True, exist_ok=True)
    wayback_url = f"http://web.archive.org/web/{snapshot.timestamp}id_/{snapshot.original}"
    for attempt in range(5):
        try:
            data = request_bytes(wayback_url)
            if data.lstrip().startswith((b"<html", b"<!DOCTYPE", b"<script")):
                return False
            destination.write_bytes(data)
            return True
        except HTTPError as exc:
            if exc.code not in {429, 503, 504}:
                raise
        except (URLError, TimeoutError):
            pass
        time.sleep(min(2**attempt, 30))
    return False


def replace_markdown_image_urls(rows: list[dict[str, str]]) -> None:
    for row in rows:
        md_path = ARTICLES_DIR / f"{row['article_slug']}.md"
        if not md_path.exists():
            continue
        text = md_path.read_text(encoding="utf-8")
        src = row["original_src"]
        local = local_path_for(src)
        variants = {
            src,
            src.replace("https://allmedtests.com", "http://allmedtests.com"),
            src.replace("http://allmedtests.com", "https://allmedtests.com"),
        }
        for variant in variants:
            text = text.replace(variant, local)
        md_path.write_text(text, encoding="utf-8")


def main() -> int:
    rows = list(csv.DictReader(IMAGES_CSV.open(newline="", encoding="utf-8")))
    restore_rows: list[dict[str, str]] = []
    missing: list[str] = []

    for row in rows:
        thumb = normalize_url(row["original_src"])
        original = fullsize_candidate(thumb)
        if thumb == normalize_url(ABO_ORIGINAL):
            original = None
        candidates = [("thumbnail", thumb)]
        if original:
            candidates.append(("original", normalize_url(original)))
        if normalize_url(ABO_ORIGINAL) not in [url for _kind, url in candidates] and row["article_slug"] == "abo-and-rh-blood-grouping":
            candidates.append(("original", normalize_url(ABO_ORIGINAL)))

        status: dict[str, str] = {
            "article_slug": row["article_slug"],
            "thumbnail_url": thumb,
            "thumbnail_restored": "нет",
            "original_url": original or "",
            "original_found": "нет",
            "original_restored": "нет",
            "original_referring_domains": "",
        }

        for kind, url in candidates:
            destination = PUBLIC_DIR / local_path_for(url).lstrip("/")
            if destination.exists() and destination.stat().st_size > 0:
                found = True
                restored = True
            else:
                print(f"restore {kind}: {url}", flush=True)
                snapshot = find_snapshot(url)
                found = snapshot is not None
                restored = download_image(snapshot, destination) if snapshot else False
            if kind == "thumbnail":
                status["thumbnail_restored"] = "да" if restored else "нет"
            else:
                status["original_url"] = url
                status["original_found"] = "да" if found else "нет"
                status["original_restored"] = "да" if restored else "нет"
                status["original_referring_domains"] = str(IMAGE_BACKLINKS.get(url, 0))
            if not found or not restored:
                missing.append(url)
            time.sleep(0.8)
        restore_rows.append(status)

    replace_markdown_image_urls(rows)

    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "article_slug",
                "thumbnail_url",
                "thumbnail_restored",
                "original_url",
                "original_found",
                "original_restored",
                "original_referring_domains",
            ],
        )
        writer.writeheader()
        writer.writerows(restore_rows)

    print("article_slug | thumbnail_restored | original_found | original_restored | original_referring_domains")
    print("--- | --- | --- | --- | ---:")
    for row in restore_rows:
        print(
            f"{row['article_slug']} | {row['thumbnail_restored']} | {row['original_found']} | "
            f"{row['original_restored']} | {row['original_referring_domains'] or 0}"
        )
    print("missing")
    for url in sorted(set(missing)):
        print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
