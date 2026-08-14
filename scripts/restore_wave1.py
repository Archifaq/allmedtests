#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import ssl
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, "/private/tmp/allmedtests-pydeps")

from bs4 import BeautifulSoup  # type: ignore
from markdownify import markdownify as html_to_markdown  # type: ignore


RAW_DIR = Path("audit/raw_snapshots")
OUT_DIR = Path("src/content/articles/en")
IMAGES_CSV = Path("audit/images_to_recover.csv")
REVIEW_MD = Path("audit/content_review_needed.md")
PRIORITY_CSV = Path("audit/urls_priority.csv")
RESTORED_DATE = "2026-08-14"

SNAPSHOT_OVERRIDES = {
    "spectrophotometer-working-principle-use-applications": (
        "http://web.archive.org/web/20240520022342id_/https://allmedtests.com/"
        "spectrophotometer-working-principle-use-applications/"
    ),
}


def slug_from_url(url: str) -> str:
    return urlparse(url).path.strip("/")


def original_path(url: str) -> str:
    path = urlparse(url).path
    return path if path.endswith("/") else f"{path}/"


def yaml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+-\s+All Medical Tests\s*$", "", text, flags=re.I)
    return text


def fetch_snapshot(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    context = ssl._create_unverified_context()
    for attempt in range(5):
        try:
            request = Request(url, headers={"User-Agent": "allmedtests-wave1-restore/1.0"})
            with urlopen(request, timeout=60, context=context) as response:
                destination.write_bytes(response.read())
            return
        except HTTPError as exc:
            if exc.code not in {429, 503, 504}:
                raise
        except (URLError, TimeoutError):
            pass
        time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"Could not fetch snapshot: {url}")


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
    for selector in [
        ".entry-content",
        "article .entry-content",
        ".post-content",
        ".td-post-content",
        "article",
        "main",
    ]:
        found = soup.select_one(selector)
        if found and len(found.get_text(" ", strip=True)) > 250:
            return found
    return None


def find_title(soup: BeautifulSoup) -> str:
    for selector in ["h1.entry-title", "article h1", "h1"]:
        found = soup.select_one(selector)
        if found and found.get_text(strip=True):
            return clean_title(found.get_text(" ", strip=True))
    if soup.title:
        return clean_title(soup.title.get_text(" ", strip=True))
    return "Untitled"


def find_description(soup: BeautifulSoup) -> str | None:
    for attrs in [{"name": "description"}, {"property": "og:description"}]:
        found = soup.find("meta", attrs=attrs)
        if found and found.get("content"):
            return re.sub(r"\s+", " ", str(found["content"])).strip()
    return None


def find_publish_date(soup: BeautifulSoup) -> str | None:
    selectors = [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "date"}),
        ("meta", {"itemprop": "datePublished"}),
    ]
    for tag_name, attrs in selectors:
        found = soup.find(tag_name, attrs=attrs)
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


def normalize_image_src(src: str) -> str:
    src = src.strip()
    if not src:
        return src
    if src.startswith("//"):
        return f"https:{src}"
    return src


def collect_images(article_slug: str, content: Any) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    for img in content.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        src = normalize_image_src(str(src))
        if not src:
            continue
        images.append(
            {
                "article_slug": article_slug,
                "original_src": src,
                "alt_text": str(img.get("alt") or "").strip(),
            }
        )
    return images


def markdown_from_content(content: Any) -> str:
    remove_unwanted_nodes(content)
    markdown = html_to_markdown(
        str(content),
        heading_style="ATX",
        bullets="-",
        strip=["span"],
    )
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    return markdown.strip() + "\n"


def write_article(row: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    slug = slug_from_url(row["url"])
    raw_path = RAW_DIR / f"{slug}.html"
    snapshot_url = SNAPSHOT_OVERRIDES.get(slug, row["last_snapshot_url_for_fetch"])
    fetch_snapshot(snapshot_url, raw_path)

    soup = BeautifulSoup(raw_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    content = find_content(soup)
    title = find_title(soup)
    description = find_description(soup)
    publish_date = find_publish_date(soup)
    review_notes: list[str] = []

    if slug in SNAPSHOT_OVERRIDES:
        review_notes.append(
            "Latest audit snapshot was a parked-domain redirect; restored from earlier usable Wayback snapshot."
        )

    if not content:
        body = "<!-- TODO: fragment unclear in archived snapshot, needs manual review -->\n"
        images: list[dict[str, str]] = []
        extraction_status = "нет"
        review_notes.append("Could not find a usable article content container.")
    else:
        text_len = len(content.get_text(" ", strip=True))
        body = markdown_from_content(content)
        images = collect_images(slug, content)
        extraction_status = "да" if text_len > 1000 else "частично"
        if text_len <= 1000:
            body += "\n<!-- TODO: fragment unclear in archived snapshot, needs manual review -->\n"
            review_notes.append(f"Extracted content is short ({text_len} characters); needs manual review.")

    frontmatter = [
        "---",
        f"title: {yaml_string(title)}",
    ]
    if description:
        frontmatter.append(f"description: {yaml_string(description)}")
    frontmatter.append(f"originalUrl: {yaml_string(original_path(row['url']))}")
    if publish_date:
        frontmatter.append(f"originalPublishDate: {yaml_string(publish_date)}")
    frontmatter.extend(
        [
            f"restoredDate: {yaml_string(RESTORED_DATE)}",
            f"sourceSnapshot: {yaml_string(snapshot_url)}",
            f"referringDomains: {int(row['referring_domains'])}",
            'priorityTier: "P0"',
            "draft: true",
            "---",
            "",
        ]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{slug}.md").write_text("\n".join(frontmatter) + body, encoding="utf-8")

    return (
        {
            "slug": slug,
            "extraction_status": extraction_status,
            "image_count": len(images),
            "has_todo": "yes" if "<!-- TODO:" in body else "no",
        },
        images,
        review_notes,
    )


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = [row for row in csv.DictReader(PRIORITY_CSV.open(newline="", encoding="utf-8")) if row["priority_tier"] == "P0"]
    all_images: list[dict[str, str]] = []
    summaries: list[dict[str, Any]] = []
    review_items: list[tuple[str, list[str]]] = []

    for row in rows:
        summary, images, notes = write_article(row)
        summaries.append(summary)
        all_images.extend(images)
        if notes:
            review_items.append((summary["slug"], notes))
        time.sleep(0.8)

    with IMAGES_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["article_slug", "original_src", "alt_text"])
        writer.writeheader()
        writer.writerows(all_images)

    lines = ["# Content review needed", ""]
    if review_items:
        for slug, notes in review_items:
            lines.append(f"## {slug}")
            lines.append("")
            for note in notes:
                lines.append(f"- {note}")
            lines.append("")
    else:
        lines.append("No manual-review issues were detected during extraction.")
    REVIEW_MD.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print("slug | extracted | images | TODO")
    print("--- | --- | ---: | ---")
    for item in summaries:
        print(f"{item['slug']} | {item['extraction_status']} | {item['image_count']} | {item['has_todo']}")
    print(f"images_to_recover={len(all_images)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
