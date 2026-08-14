#!/usr/bin/env python3
"""
Audit historical allmedtests.com URLs from the Wayback Machine CDX API.

Usage:
  python3 scripts/audit_urls.py
  python3 scripts/audit_urls.py --refresh
  python3 scripts/audit_urls.py --backlinks audit/backlinks.csv --traffic audit/ahrefs_traffic.csv

Current scoring inputs:
  - audit/backlinks.csv: Ahrefs "Best by Links" export.
  - audit/ahrefs_traffic.csv: Ahrefs "Organic Search -> Top Pages" export.

TODO: when the domain is verified in Google Search Console and has several
months of new-owner data, GSC clicks/impressions can be added as a separate
fresh-performance signal in a later recalculation. Historical GSC data is not
available to the new owner, so it is intentionally not used here.

Outputs:
  - audit/cache/cdx_raw.json
  - audit/urls_full.csv
  - audit/urls_priority.csv
  - audit/legacy_products_review.csv
  - audit/taxonomy_review.csv
  - audit/summary.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


DOMAIN = "allmedtests.com"
ARCHIVE_BASE = "https://web.archive.org/cdx/search/cdx"
CACHE_MAX_AGE = timedelta(hours=24)
REQUEST_SLEEP_SECONDS = 0.75
MAX_RETRIES = 5

AUDIT_DIR = Path("audit")
CACHE_DIR = AUDIT_DIR / "cache"
CDX_CACHE = CACHE_DIR / "cdx_raw.json"
FULL_CSV = AUDIT_DIR / "urls_full.csv"
PRIORITY_CSV = AUDIT_DIR / "urls_priority.csv"
LEGACY_PRODUCTS_CSV = AUDIT_DIR / "legacy_products_review.csv"
TAXONOMY_CSV = AUDIT_DIR / "taxonomy_review.csv"
SUMMARY_MD = AUDIT_DIR / "summary.md"

REAL_SIGNAL_ARTICLE_PATHS = (
    "/spectrophotometer-working-principle-use-applications/",
    "/benedicts-test-reducing-sugar/",
    "/separation-amino-acids-paper-chromatography/",
    "/abo-and-rh-blood-grouping/",
    "/clinical-examination-sensory-system/",
    "/photoelectric-colorimeter/",
    "/creatine-kinase-test/",
    "/serum-urea-test-kinetic-uv-method/",
    "/blood-glucose-test/",
)

TEST_CONTENT_PATTERNS = (
    "-test",
    "-principle",
    "-procedure",
    "-reagent",
    "-method",
    "-stain",
    "-media",
    "-agar",
    "-culture",
    "-reaction",
    "-identification",
)

LEGACY_PRODUCT_PATTERNS = (
    "drug-test",
    "drug-testing-kit",
    "drug-testing-cup",
    "home-test-kit",
    "detox-pills",
    "test-kit",
    "testing-kit",
    "testing-cup",
    "urine-test",
    "saliva-test",
    "hair-test",
    "qtest",
    "xalex",
)

SERVICE_PAGE_PATTERNS = (
    "contact",
    "about",
    "privacy-policy",
    "privacy",
    "terms",
    "disclaimer",
    "facebook-demo",
    "instagram-feed-demo",
)

TECHNICAL_PATH_PARTS = (
    "/wp-admin/",
    "/wp-content/",
    "/wp-includes/",
    "/wp-json/",
    "/xmlrpc.php",
    "/trackback/",
    "/comments/",
    "/comment-page-",
    "/author/",
    "/search/",
)

TECHNICAL_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".css",
    ".js",
    ".json",
    ".xml",
    ".txt",
    ".pdf",
    ".zip",
    ".rar",
    ".gz",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}

FULL_FIELDNAMES = [
    "url",
    "url_type",
    "last_snapshot_timestamp",
    "last_snapshot_url_for_fetch",
    "status_last_seen",
    "estimated_organic_traffic",
    "referring_domains",
    "dofollow_referring_domains",
    "total_backlinks",
    "max_domain_rating",
    "priority_score",
    "priority_tier",
]

REVIEW_FIELDNAMES = ["url", "referring_domains", "estimated_organic_traffic"]


def log(message: str) -> None:
    print(f"[audit] {message}", flush=True)


def normalize_url(url: str) -> str:
    raw_url = url.strip()
    if raw_url.startswith("/"):
        raw_url = f"https://{DOMAIN}{raw_url}"
    parsed = urlparse(raw_url)
    scheme = "https"
    netloc = (parsed.hostname or parsed.netloc).lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = re.sub(r"/+", "/", parsed.path or "/")
    if path != "/" and not path.endswith("/") and "." not in Path(path).name:
        path += "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return datetime.now(timezone.utc) - modified < CACHE_MAX_AGE


def build_cdx_url(extra_params: dict[str, str | list[str]]) -> str:
    params: dict[str, str | list[str]] = {
        "url": f"{DOMAIN}/*",
        "output": "json",
        "fl": "original,timestamp,statuscode,mimetype",
        "collapse": "urlkey",
        "limit": "10000",
        "showResumeKey": "true",
        "sort": "reverse",
    }
    params.update(extra_params)
    return f"{ARCHIVE_BASE}?{urlencode(params, doseq=True)}"


def request_json(url: str) -> Any:
    last_error: Exception | None = None
    ssl_context = ssl._create_unverified_context()
    for attempt in range(MAX_RETRIES):
        try:
            request = Request(url, headers={"User-Agent": "allmedtests-url-audit/1.0"})
            with urlopen(request, timeout=60, context=ssl_context) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 503, 504}:
                raise
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
        wait = min(2**attempt, 30)
        log(f"CDX request failed ({last_error}); retrying in {wait}s")
        time.sleep(wait)
    raise RuntimeError(f"CDX request failed after {MAX_RETRIES} retries: {last_error}")


def split_cdx_payload(payload: Any) -> tuple[list[dict[str, str]], str | None]:
    if not payload:
        return [], None
    header = payload[0]
    if not isinstance(header, list):
        raise ValueError("Unexpected CDX JSON payload shape")

    rows: list[dict[str, str]] = []
    resume_key: str | None = None
    for item in payload[1:]:
        if not isinstance(item, list):
            continue
        if len(item) == 1 and isinstance(item[0], str) and item[0].startswith("resumeKey"):
            resume_key = item[0].split(":", 1)[-1].strip()
            continue
        if len(item) == 2 and item[0] == "resumeKey":
            resume_key = item[1]
            continue
        if len(item) == len(header):
            rows.append(dict(zip(header, item)))
    return rows, resume_key


def fetch_cdx_dataset(label: str, extra_params: dict[str, str | list[str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    resume_key: str | None = None
    page = 1

    while True:
        params = dict(extra_params)
        if resume_key:
            params["resumeKey"] = resume_key
        payload = request_json(build_cdx_url(params))
        page_rows, resume_key = split_cdx_payload(payload)
        rows.extend(page_rows)
        log(f"{label}: page {page}, fetched {len(page_rows)} rows, total {len(rows)}")
        page += 1
        if not resume_key:
            break
        time.sleep(REQUEST_SLEEP_SECONDS)

    return rows


def load_or_fetch_cdx(refresh: bool) -> dict[str, Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not refresh and cache_is_fresh(CDX_CACHE):
        log(f"Using fresh cache: {CDX_CACHE}")
        return json.loads(CDX_CACHE.read_text(encoding="utf-8"))

    log("Fetching latest HTML snapshots from CDX")
    latest_html = fetch_cdx_dataset("latest_html", {"filter": "mimetype:text/html"})
    log("Fetching latest successful HTML snapshots from CDX")
    latest_200_html = fetch_cdx_dataset(
        "latest_200_html",
        {"filter": ["mimetype:text/html", "statuscode:200"]},
    )

    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "latest_html": latest_html,
        "latest_200_html": latest_200_html,
    }
    CDX_CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Wrote cache: {CDX_CACHE}")
    return data


def parse_number(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip().replace(",", "").replace(" ", "")
    if not text or text.lower() in {"n/a", "na", "-", "unknown"}:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def find_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    normalized = {name.strip().lower(): name for name in fieldnames}
    for candidate in candidates:
        found = normalized.get(candidate.lower())
        if found:
            return found
    return None


def make_real_signal_article_urls() -> set[str]:
    return {normalize_url(path) for path in REAL_SIGNAL_ARTICLE_PATHS}


def load_backlinks_export(path: str | None) -> dict[str, dict[str, int]] | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        log(f"Backlink export not found: {path}; referring_domains will be unknown")
        return None

    with file_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return None
        url_col = find_column(
            reader.fieldnames,
            ("Target URL", "Target", "URL", "Page", "Address", "Landing page"),
        )
        rd_col = find_column(
            reader.fieldnames,
            ("Referring domains", "Ref domains", "RD", "Domains", "Referring Domains"),
        )
        dofollow_col = find_column(
            reader.fieldnames,
            ("Dofollow referring domains", "Dofollow ref domains", "Dofollow RD"),
        )
        total_col = find_column(
            reader.fieldnames,
            ("Total backlinks", "Backlinks", "External backlinks"),
        )
        dr_col = find_column(
            reader.fieldnames,
            ("Max domain rating", "Max DR", "Domain rating", "DR"),
        )
        log(
            "Backlinks columns found: "
            f"url={url_col!r}, referring_domains={rd_col!r}, "
            f"dofollow={dofollow_col!r}, total_backlinks={total_col!r}, max_dr={dr_col!r}"
        )
        if not url_col or not rd_col:
            raise ValueError("Backlink CSV must contain Target URL and Referring domains columns")

        result: dict[str, dict[str, int]] = {}
        for row in reader:
            raw_url = row.get(url_col, "")
            if not raw_url:
                continue
            url = normalize_url(raw_url)
            metrics = {
                "referring_domains": parse_number(row.get(rd_col)),
                "dofollow_referring_domains": parse_number(row.get(dofollow_col)) if dofollow_col else 0,
                "total_backlinks": parse_number(row.get(total_col)) if total_col else 0,
                "max_domain_rating": parse_number(row.get(dr_col)) if dr_col else 0,
            }
            current = result.get(url)
            if current is None or metrics["referring_domains"] > current["referring_domains"]:
                result[url] = metrics
        log(f"Loaded {len(result)} backlink rows from {path}")
        return result


def load_ahrefs_traffic_export(path: str | None) -> dict[str, int] | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        log(f"Ahrefs traffic export not found: {path}; estimated_organic_traffic will be unknown")
        return None

    with file_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return None
        url_col = find_column(
            reader.fieldnames,
            ("URL", "Page", "Target URL", "Address", "Landing page", "Top page"),
        )
        traffic_col = find_column(
            reader.fieldnames,
            ("Traffic", "Organic traffic", "Estimated traffic", "Est. traffic"),
        )
        log(f"Ahrefs traffic columns found: url={url_col!r}, traffic={traffic_col!r}")
        if not url_col or not traffic_col:
            raise ValueError("Ahrefs traffic CSV must contain URL/Page and Traffic columns")

        result: dict[str, int] = {}
        for row in reader:
            raw_url = row.get(url_col, "")
            if not raw_url:
                continue
            url = normalize_url(raw_url)
            result[url] = max(result.get(url, 0), parse_number(row.get(traffic_col)))
        log(f"Loaded {len(result)} Ahrefs traffic rows from {path}")
        return result


def should_keep_url(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    lower_path = (parsed.path or "/").lower()
    lower_path_no_slash = lower_path.rstrip("/")
    hostname = (parsed.hostname or parsed.netloc).lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if hostname != DOMAIN:
        return False, "other_domain"
    if parsed.query:
        return False, "query_url"
    if lower_path_no_slash in {"/wp-admin", "/wp-login.php", "/xmlrpc.php"}:
        return False, "technical_path"
    if any(part in lower_path for part in TECHNICAL_PATH_PARTS):
        return False, "technical_path"
    if lower_path.endswith("/feed/") or lower_path == "/feed/":
        return False, "feed"
    if re.search(r"/page/\d+/?$", lower_path):
        return False, "pagination"
    if re.search(r"/(category|tag)/[^/]+/page/\d+/?$", lower_path):
        return False, "archive_pagination"
    if Path(lower_path).suffix in TECHNICAL_EXTENSIONS:
        return False, "file_asset"
    return True, "kept"


def is_specific_test_content(url: str) -> bool:
    slug = urlparse(url).path.strip("/").lower()
    return any(pattern in slug for pattern in TEST_CONTENT_PATTERNS)


def classify_url(url: str) -> str:
    path = urlparse(url).path.strip("/").lower()
    segments = [segment for segment in path.split("/") if segment]

    if not segments:
        return "homepage"
    if segments and segments[0] in {"tag", "category"}:
        return "taxonomy"

    if segments:
        first = segments[0]
        second = segments[1] if len(segments) > 1 else ""
        if re.match(r"^\d+-", first) or (first.isdigit() and re.match(r"^\d+-", second)):
            return "legacy_product"
    if any(pattern in path for pattern in LEGACY_PRODUCT_PATTERNS):
        return "legacy_product"
    if any(segment in SERVICE_PAGE_PATTERNS for segment in segments):
        return "other"
    if any(pattern in path for pattern in SERVICE_PAGE_PATTERNS):
        return "other"

    if len(segments) == 1 and re.match(r"^[a-z0-9][a-z0-9-]+$", segments[0]):
        return "article"

    return "other"


def status_label(status: str | None) -> str:
    if status in {"200", "301", "302", "404"}:
        return status
    if not status or status == "-":
        return "gone"
    return status


def wayback_fetch_url(timestamp: str, original: str) -> str:
    return f"http://web.archive.org/web/{timestamp}id_/{original}"


def priority_for_article(
    url: str,
    referring_domains: int | None,
    estimated_organic_traffic: int | None,
) -> tuple[int, str]:
    rd = referring_domains or 0
    traffic = estimated_organic_traffic or 0
    score = 0
    if rd > 0:
        score += 50
    if rd >= 3:
        score += 15
    if traffic > 0:
        score += 30
    if is_specific_test_content(url):
        score += 5

    if score >= 50:
        tier = "P0"
    elif score >= 20:
        tier = "P1"
    elif score >= 1:
        tier = "P2"
    else:
        tier = "P3"
    return score, tier


def add_latest(map_by_url: dict[str, dict[str, str]], item: dict[str, str]) -> None:
    keep, _ = should_keep_url(item["original"])
    if not keep:
        return
    url = normalize_url(item["original"])
    current = map_by_url.get(url)
    if current is None or item.get("timestamp", "") > current.get("timestamp", ""):
        map_by_url[url] = item


def build_rows(
    cdx_data: dict[str, Any],
    backlinks: dict[str, dict[str, int]] | None,
    traffic: dict[str, int] | None,
) -> tuple[list[dict[str, Any]], Counter[str], set[str], set[str], list[dict[str, str]]]:
    latest_by_url: dict[str, dict[str, str]] = {}
    last_200_by_url: dict[str, dict[str, str]] = {}
    filter_reasons_by_url: dict[str, str] = {}

    for dataset_name in ("latest_html", "latest_200_html"):
        for item in cdx_data.get(dataset_name, []):
            keep, reason = should_keep_url(item["original"])
            normalized = normalize_url(item["original"])
            if keep:
                filter_reasons_by_url[normalized] = "kept"
            else:
                filter_reasons_by_url.setdefault(normalized, reason)
            if not keep:
                continue
            if dataset_name == "latest_html":
                add_latest(latest_by_url, item)
            else:
                add_latest(last_200_by_url, item)

    rows: list[dict[str, Any]] = []
    all_urls = sorted(set(latest_by_url) | set(last_200_by_url))
    real_signal_urls = make_real_signal_article_urls()
    reclassified: list[dict[str, str]] = []
    for url in all_urls:
        latest = latest_by_url.get(url)
        last_200 = last_200_by_url.get(url)
        snapshot = last_200 or latest
        timestamp = snapshot.get("timestamp", "") if snapshot else ""
        original = snapshot.get("original", url) if snapshot else url
        original_url_type = classify_url(url)
        url_type = original_url_type

        rd_value: int | str
        rd_for_score: int | None
        dofollow_value: int | str
        total_backlinks_value: int | str
        max_dr_value: int | str
        if backlinks is None:
            rd_value = "unknown"
            rd_for_score = None
            dofollow_value = "unknown"
            total_backlinks_value = "unknown"
            max_dr_value = "unknown"
        else:
            backlink_metrics = backlinks.get(
                url,
                {
                    "referring_domains": 0,
                    "dofollow_referring_domains": 0,
                    "total_backlinks": 0,
                    "max_domain_rating": 0,
                },
            )
            rd_for_score = backlink_metrics["referring_domains"]
            rd_value = rd_for_score
            dofollow_value = backlink_metrics["dofollow_referring_domains"]
            total_backlinks_value = backlink_metrics["total_backlinks"]
            max_dr_value = backlink_metrics["max_domain_rating"]

        traffic_value: int | str
        traffic_for_score: int | None
        if traffic is None:
            traffic_value = "unknown"
            traffic_for_score = None
        else:
            traffic_for_score = traffic.get(url, 0)
            traffic_value = traffic_for_score

        before_score, before_tier = "", ""
        if url_type == "article":
            before_score, before_tier = priority_for_article(url, rd_for_score, traffic_for_score)

        if url in real_signal_urls:
            log(f"Real-signal URL classification: {url} -> {url_type}")
            if url_type != "article":
                reclassified.append(
                    {
                        "url": url,
                        "from_url_type": url_type,
                        "from_priority_tier": str(before_tier),
                        "to_url_type": "article",
                    }
                )
                url_type = "article"

        if url_type == "article":
            score, tier = priority_for_article(url, rd_for_score, traffic_for_score)
            if reclassified and reclassified[-1].get("url") == url:
                reclassified[-1]["to_priority_tier"] = tier
        else:
            score, tier = "", ""

        rows.append(
            {
                "url": url,
                "url_type": url_type,
                "last_snapshot_timestamp": timestamp,
                "last_snapshot_url_for_fetch": wayback_fetch_url(timestamp, original) if timestamp else "",
                "status_last_seen": status_label(latest.get("statuscode") if latest else None),
                "estimated_organic_traffic": traffic_value,
                "referring_domains": rd_value,
                "dofollow_referring_domains": dofollow_value,
                "total_backlinks": total_backlinks_value,
                "max_domain_rating": max_dr_value,
                "priority_score": score,
                "priority_tier": tier,
            }
        )

    cdx_url_set = set(all_urls)
    unmatched_backlinks = set(backlinks or {}) - cdx_url_set
    unmatched_traffic = set(traffic or {}) - cdx_url_set
    return rows, Counter(filter_reasons_by_url.values()), unmatched_backlinks, unmatched_traffic, reclassified


def article_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    score = int(row["priority_score"] or 0)
    rd = row["referring_domains"]
    rd_num = rd if isinstance(rd, int) else 0
    return (-score, -rd_num, row["url"])


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log(f"Wrote {len(rows)} rows: {path}")


def summarize(
    rows: list[dict[str, Any]],
    filter_reasons: Counter[str],
    unmatched_backlinks: set[str],
    unmatched_traffic: set[str],
    reclassified: list[dict[str, str]],
) -> str:
    statuses = Counter(row["status_last_seen"] for row in rows)
    types = Counter(row["url_type"] for row in rows)
    article_rows = [row for row in rows if row["url_type"] == "article"]
    article_tiers = Counter(row["priority_tier"] for row in article_rows)
    wave_1 = [row for row in sorted(article_rows, key=article_sort_key) if row["priority_tier"] == "P0"]
    wave_2 = [row for row in sorted(article_rows, key=article_sort_key) if row["priority_tier"] == "P1"]
    remaining_without_backlinks = [
        row
        for row in article_rows
        if row["priority_tier"] in {"P2", "P3"}
        and (not isinstance(row["referring_domains"], int) or row["referring_domains"] == 0)
    ]
    homepage = next((row for row in rows if row["url_type"] == "homepage"), None)

    lines = [
        "# allmedtests.com URL audit summary",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Counts",
        "",
        f"- Total kept URLs: {len(rows)}",
        f"- Last seen 200: {statuses.get('200', 0)}",
        f"- Last seen 301/302: {statuses.get('301', 0) + statuses.get('302', 0)}",
        f"- Last seen 404/gone: {statuses.get('404', 0) + statuses.get('gone', 0)}",
        "",
        "## URL Types",
        "",
    ]
    for url_type in ("homepage", "article", "legacy_product", "taxonomy", "other"):
        lines.append(f"- {url_type}: {types.get(url_type, 0)}")

    lines.extend(["", "## Article Priority Tiers", ""])
    for tier in ("P0", "P1", "P2", "P3"):
        lines.append(f"- {tier}: {article_tiers.get(tier, 0)}")

    lines.extend(["", "## Homepage", ""])
    if homepage:
        lines.append(
            "КРИТИЧНО: корневой URL не должен менять адрес и не должен редиректиться никуда "
            f"при миграции — {homepage['referring_domains']} ссылающихся домена "
            f"({homepage['dofollow_referring_domains']} dofollow)."
        )
        lines.append("")
        lines.append(
            f"- URL: {homepage['url']}; total backlinks: {homepage['total_backlinks']}; "
            f"max domain rating: {homepage['max_domain_rating']}"
        )
    else:
        lines.append("Homepage URL was not found in the CDX set.")

    lines.extend(["", "## Reclassified By Real Signal", ""])
    if reclassified:
        lines.append("| url | from url_type | from priority | to url_type | to priority |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in reclassified:
            lines.append(
                f"| {item['url']} | {item['from_url_type']} | "
                f"{item.get('from_priority_tier', '') or '-'} | {item['to_url_type']} | "
                f"{item.get('to_priority_tier', '') or '-'} |"
            )
    else:
        lines.append("None. All 9 backlink-confirmed article URLs were already classified as article.")

    lines.extend(["", "## Wave 1 (P0)", ""])
    if wave_1:
        lines.append("| score | referring_domains | dofollow_referring_domains | url |")
        lines.append("| ---: | ---: | ---: | --- |")
        for row in wave_1:
            lines.append(
                f"| {row['priority_score']} | {row['referring_domains']} | "
                f"{row['dofollow_referring_domains']} | {row['url']} |"
            )
    else:
        lines.append("No P0 article URLs.")

    lines.extend(["", "## Wave 2 (P1)", ""])
    if wave_2:
        lines.append("| score | referring_domains | dofollow_referring_domains | url |")
        lines.append("| ---: | ---: | ---: | --- |")
        for row in wave_2:
            lines.append(
                f"| {row['priority_score']} | {row['referring_domains']} | "
                f"{row['dofollow_referring_domains']} | {row['url']} |"
            )
    else:
        lines.append("No P1 article URLs.")

    lines.extend(["", "## Remaining Articles Without Backlinks", ""])
    lines.append(f"- P2/P3 article URLs without backlinks: {len(remaining_without_backlinks)}")

    lines.extend(["", "## Filter Reasons", ""])
    for reason, count in filter_reasons.most_common():
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## Ahrefs URLs Not Matched In CDX", ""])
    lines.append(f"- Backlinks unmatched: {len(unmatched_backlinks)}")
    lines.append(f"- Traffic unmatched: {len(unmatched_traffic)}")
    if unmatched_backlinks:
        lines.extend(["", "### Backlinks", ""])
        lines.extend(f"- {url}" for url in sorted(unmatched_backlinks)[:100])
    if unmatched_traffic:
        lines.extend(["", "### Traffic", ""])
        lines.extend(f"- {url}" for url in sorted(unmatched_traffic)[:100])

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit allmedtests.com historical URLs")
    parser.add_argument("--refresh", action="store_true", help="Refresh CDX cache")
    parser.add_argument("--backlinks", default="audit/backlinks.csv", help="Ahrefs Best by Links CSV")
    parser.add_argument("--traffic", default="audit/ahrefs_traffic.csv", help="Ahrefs Top Pages CSV")
    args = parser.parse_args()

    AUDIT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cdx_data = load_or_fetch_cdx(args.refresh)
    backlinks = load_backlinks_export(args.backlinks)
    traffic = load_ahrefs_traffic_export(args.traffic)
    rows, filter_reasons, unmatched_backlinks, unmatched_traffic, reclassified = build_rows(
        cdx_data,
        backlinks,
        traffic,
    )

    article_rows = sorted([row for row in rows if row["url_type"] == "article"], key=article_sort_key)
    legacy_rows = sorted(
        [
            {
                "url": row["url"],
                "referring_domains": row["referring_domains"],
                "estimated_organic_traffic": row["estimated_organic_traffic"],
            }
            for row in rows
            if row["url_type"] == "legacy_product"
        ],
        key=lambda row: row["url"],
    )
    taxonomy_rows = sorted(
        [
            {
                "url": row["url"],
                "referring_domains": row["referring_domains"],
                "estimated_organic_traffic": row["estimated_organic_traffic"],
            }
            for row in rows
            if row["url_type"] == "taxonomy"
        ],
        key=lambda row: row["url"],
    )
    full_rows = sorted(rows, key=lambda row: (row["url_type"], article_sort_key(row), row["url"]))

    write_csv(FULL_CSV, full_rows, FULL_FIELDNAMES)
    write_csv(PRIORITY_CSV, article_rows, FULL_FIELDNAMES)
    write_csv(LEGACY_PRODUCTS_CSV, legacy_rows, REVIEW_FIELDNAMES)
    write_csv(TAXONOMY_CSV, taxonomy_rows, REVIEW_FIELDNAMES)
    SUMMARY_MD.write_text(
        summarize(full_rows, filter_reasons, unmatched_backlinks, unmatched_traffic, reclassified),
        encoding="utf-8",
    )
    log(f"Wrote summary: {SUMMARY_MD}")

    if unmatched_backlinks:
        log("Backlinks URLs not matched in CDX:")
        for url in sorted(unmatched_backlinks)[:100]:
            log(f"  {url}")
    if unmatched_traffic:
        log("Ahrefs traffic URLs not matched in CDX:")
        for url in sorted(unmatched_traffic)[:100]:
            log(f"  {url}")
    log(f"Processed {len(full_rows)} kept URLs")
    log("Filter reasons: " + ", ".join(f"{key}={value}" for key, value in filter_reasons.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
