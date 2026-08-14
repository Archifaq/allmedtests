#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, "/private/tmp/allmedtests-pydeps")

from bs4 import BeautifulSoup  # type: ignore
from markdownify import markdownify as html_to_markdown  # type: ignore


PRIORITY_CSV = Path("audit/urls_priority.csv")
RAW_DIR = Path("audit/raw_snapshots")
OUT_DIR = Path("src/content/articles/en")
PUBLIC_DIR = Path("public")
REVIEW_MD = Path("audit/content_review_needed.md")
REPORT_CSV = Path("audit/remaining_articles_restore_report.csv")
RESTORED_DATE = "2026-08-14"
USER_AGENT = "allmedtests-remaining-restore/1.0"


def log(message: str) -> None:
    print(f"[restore] {message}", flush=True)


def slug_from_url(url: str) -> str:
    return urlparse(url).path.strip("/")


def original_path(url: str) -> str:
    path = urlparse(url).path
    return path if path.endswith("/") else f"{path}/"


def yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+-\s+All Medical Tests\s*$", "", text, flags=re.I)


def request_bytes(url: str, timeout: int = 45) -> bytes:
    context = ssl._create_unverified_context()
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def request_json(url: str, timeout: int = 35) -> list:
    return json.loads(request_bytes(url, timeout=timeout).decode("utf-8"))


def fetch_url(url: str, destination: Path) -> bool:
    if destination.exists() and destination.stat().st_size > 0:
        return True
    for attempt in range(4):
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(request_bytes(url))
            return True
        except HTTPError as exc:
            if exc.code not in {429, 503, 504}:
                return False
        except (URLError, TimeoutError):
            pass
        time.sleep(min(2**attempt, 20))
    return False


def find_latest_200_snapshot(page_url: str) -> str | None:
    candidates = [
        page_url,
        page_url.replace("https://allmedtests.com", "http://allmedtests.com"),
    ]
    for candidate in candidates:
        params = {
            "url": candidate,
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype",
            "filter": ["statuscode:200", "mimetype:text/html"],
            "sort": "reverse",
            "limit": "20",
        }
        cdx_url = f"https://web.archive.org/cdx/search/cdx?{urlencode(params, doseq=True)}"
        try:
            payload = request_json(cdx_url)
        except Exception:
            payload = []
        for row in payload[1:]:
            if len(row) >= 4:
                timestamp, original, _status, _mimetype = row[:4]
                return f"http://web.archive.org/web/{timestamp}id_/{original}"
        time.sleep(0.8)
    return None


def remove_unwanted_nodes(node: Any) -> None:
    selectors = [
        "script",
        "style",
        "noscript",
        "iframe",
        "form",
        ".sharedaddy",
        ".jp-relatedposts",
        ".yarpp-related",
        ".related-posts",
        ".wp_rp_wrap",
        ".wp_rp_content",
        ".related_post",
        ".related_post_title",
        ".comments-area",
        "#comments",
        ".comment-respond",
        ".navigation",
        ".post-navigation",
        ".entry-footer",
        ".adsbygoogle",
        "[class*=ad-]",
    ]
    for selector in selectors:
        for found in node.select(selector):
            found.decompose()


def find_content(soup: BeautifulSoup) -> Any | None:
    for selector in [".entry-content", "article .entry-content", ".post-content", ".td-post-content", "article", "main"]:
        found = soup.select_one(selector)
        if found and len(found.get_text(" ", strip=True)) > 250:
            return found
    return None


def find_title(soup: BeautifulSoup) -> str:
    for selector in ["h1.entry-title", "article h1", "h1"]:
        found = soup.select_one(selector)
        if found and found.get_text(strip=True):
            return clean_title(found.get_text(" ", strip=True))
    return clean_title(soup.title.get_text(" ", strip=True)) if soup.title else "Untitled"


def find_description(soup: BeautifulSoup) -> str | None:
    for attrs in [{"name": "description"}, {"property": "og:description"}]:
        found = soup.find("meta", attrs=attrs)
        if found and found.get("content"):
            return re.sub(r"\s+", " ", str(found["content"])).strip()
    return None


def find_publish_date(soup: BeautifulSoup) -> str | None:
    for attrs in [{"property": "article:published_time"}, {"name": "date"}, {"itemprop": "datePublished"}]:
        found = soup.find("meta", attrs=attrs)
        value = found.get("content") if found else None
        if value:
            match = re.search(r"\d{4}-\d{2}-\d{2}", str(value))
            if match:
                return match.group(0)
    found_time = soup.find("time")
    if found_time:
        value = found_time.get("datetime") or found_time.get_text(" ", strip=True)
        match = re.search(r"\d{4}-\d{2}-\d{2}", str(value))
        if match:
            return match.group(0)
    return None


def normalize_src(src: str) -> str:
    src = src.strip()
    if src.startswith("//"):
        return f"https:{src}"
    return src


def local_path_for(src: str) -> str:
    parsed = urlparse(src)
    return parsed.path


def wayback_image_urls(src: str, page_snapshot_url: str) -> list[str]:
    timestamp_match = re.search(r"/web/(\d+)", page_snapshot_url)
    timestamp = timestamp_match.group(1) if timestamp_match else ""
    variants = [src]
    if "https://allmedtests.com" in src:
        variants.append(src.replace("https://allmedtests.com", "http://allmedtests.com"))
    urls: list[str] = []
    if timestamp:
        for variant in variants:
            urls.append(f"http://web.archive.org/web/{timestamp}im_/{variant}")
            urls.append(f"http://web.archive.org/web/{timestamp}id_/{variant}")
    return urls


def restore_inline_images(content: Any, slug: str, page_snapshot_url: str) -> tuple[str, list[str]]:
    missing_notes: list[str] = []
    for img in list(content.find_all("img")):
        src = normalize_src(str(img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""))
        alt = str(img.get("alt") or "").strip()
        if not src:
            img.decompose()
            continue
        local_path = local_path_for(src)
        if not local_path.startswith("/wp-content/uploads/"):
            img.decompose()
            continue
        destination = PUBLIC_DIR / local_path.lstrip("/")
        restored = destination.exists() and destination.stat().st_size > 0
        if not restored:
            for wayback_url in wayback_image_urls(src, page_snapshot_url):
                try:
                    data = request_bytes(wayback_url, timeout=30)
                    if data.lstrip().startswith((b"<html", b"<!DOCTYPE", b"<script")):
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
                    restored = True
                    break
                except Exception:
                    pass
                time.sleep(0.5)
        if restored:
            img["src"] = local_path
        else:
            missing_notes.append(
                f'Missing image: {Path(local_path).name}, alt: "{alt}" — not found in Wayback, needs manual re-creation or new illustration before publish.'
            )
            img.decompose()
    return ("да" if not missing_notes else "нет", missing_notes)


def markdown_from_content(content: Any) -> str:
    markdown = html_to_markdown(str(content), heading_style="ATX", bullets="-", strip=["span"])
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    return markdown.strip() + "\n"


def append_review(slug: str, notes: list[str]) -> None:
    if not notes:
        return
    review = REVIEW_MD.read_text(encoding="utf-8") if REVIEW_MD.exists() else "# Content review needed\n"
    header = f"## {slug}"
    additions = [note for note in notes if note not in review]
    if not additions:
        return
    block = "\n".join(f"- {note}" for note in additions)
    if header in review:
        review = review.replace(header, f"{header}\n\n{block}", 1)
    else:
        if not review.endswith("\n"):
            review += "\n"
        review += f"\n{header}\n\n{block}\n"
    REVIEW_MD.write_text(review.strip() + "\n", encoding="utf-8")


def write_article(row: dict[str, str]) -> dict[str, str]:
    slug = slug_from_url(row["url"])
    out_path = OUT_DIR / f"{slug}.md"
    if out_path.exists():
        return {"slug": slug, "tier": row["priority_tier"], "text": "skipped", "image": "n-a", "todo": "нет", "not_recoverable": ""}

    snapshot_url = row["last_snapshot_url_for_fetch"]
    if row["status_last_seen"] != "200":
        replacement = find_latest_200_snapshot(row["url"])
        if replacement:
            snapshot_url = replacement
        else:
            append_review(slug, ["Not recoverable: no earlier 200 HTML snapshot found in Wayback CDX."])
            return {
                "slug": slug,
                "tier": row["priority_tier"],
                "text": "нет",
                "image": "n-a",
                "todo": "да",
                "not_recoverable": "no earlier 200 HTML snapshot found",
            }

    raw_path = RAW_DIR / f"{slug}.html"
    if not fetch_url(snapshot_url, raw_path):
        append_review(slug, [f"Not recoverable: failed to download snapshot {snapshot_url}."])
        return {"slug": slug, "tier": row["priority_tier"], "text": "нет", "image": "n-a", "todo": "да", "not_recoverable": "snapshot download failed"}

    soup = BeautifulSoup(raw_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    content = find_content(soup)
    notes: list[str] = []
    if not content:
        append_review(slug, ["Not recoverable: article content container was not found in archived HTML."])
        return {"slug": slug, "tier": row["priority_tier"], "text": "нет", "image": "n-a", "todo": "да", "not_recoverable": "content container not found"}

    remove_unwanted_nodes(content)
    image_status, image_notes = restore_inline_images(content, slug, snapshot_url)
    notes.extend(image_notes)
    text_len = len(content.get_text(" ", strip=True))
    text_status = "да" if text_len > 1000 else "частично"
    body = markdown_from_content(content)
    if text_len <= 1000:
        body += "\n<!-- TODO: fragment unclear in archived snapshot, needs manual review -->\n"
        notes.append(f"Extracted content is short ({text_len} characters); needs manual review.")

    frontmatter = ["---", f"title: {yaml_string(find_title(soup))}"]
    description = find_description(soup)
    if description:
        frontmatter.append(f"description: {yaml_string(description)}")
    frontmatter.append(f"originalUrl: {yaml_string(original_path(row['url']))}")
    publish_date = find_publish_date(soup)
    if publish_date:
        frontmatter.append(f"originalPublishDate: {yaml_string(publish_date)}")
    frontmatter.extend(
        [
            f"restoredDate: {yaml_string(RESTORED_DATE)}",
            f"sourceSnapshot: {yaml_string(snapshot_url)}",
            "referringDomains: 0",
            f"priorityTier: {yaml_string(row['priority_tier'])}",
        ]
    )
    if image_notes:
        frontmatter.append("imageRestoreNeeded: true")
    frontmatter.extend(["draft: true", "---", ""])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(frontmatter) + body, encoding="utf-8")
    append_review(slug, notes)
    return {
        "slug": slug,
        "tier": row["priority_tier"],
        "text": text_status,
        "image": image_status if "!" in body else "n-a",
        "todo": "да" if "<!-- TODO:" in body or notes else "нет",
        "not_recoverable": "",
    }


def main() -> int:
    rows = [
        row
        for row in csv.DictReader(PRIORITY_CSV.open(newline="", encoding="utf-8"))
        if row["priority_tier"] in {"P2", "P3"}
    ]
    results: list[dict[str, str]] = []
    for row in rows:
        slug = slug_from_url(row["url"])
        log(f"{row['priority_tier']} {slug}")
        results.append(write_article(row))
        time.sleep(0.8)

    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["slug", "tier", "text", "image", "todo", "not_recoverable"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("slug | tier | text | image | TODO")
    print("--- | --- | --- | --- | ---")
    for result in results:
        print(f"{result['slug']} | {result['tier']} | {result['text']} | {result['image']} | {result['todo']}")
    unrecoverable = [row for row in results if row["not_recoverable"]]
    print("not_recoverable")
    for row in unrecoverable:
        print(f"{row['slug']}: {row['not_recoverable']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
