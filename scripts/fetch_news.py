#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google News RSS를 활용해 한국 기사 중 FDA/EMA 승인 관련 뉴스를 수집하여
data/YYYY-MM-DD.json 및 data/latest.json으로 저장합니다.

- 의존성: feedparser, requests, python-dateutil
- 실행: python scripts/fetch_news.py
- 환경: GitHub Actions 또는 로컬
"""
import os, json, re, time, html
from datetime import datetime, timezone
from urllib.parse import quote_plus
import feedparser

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

QUERIES = [
    # FDA 관련 한국어 검색
    'FDA 승인 한국 기업',
    'FDA 허가 한국 기업',
    'FDA 품목허가 한국',
    # EMA 관련 한국어 검색
    'EMA 승인 한국 기업',
    'EMA 허가 한국 기업',
]

# 한국어 뉴스 우선
BASE = 'https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q='

KEYWORDS_FDA = re.compile(r'\bFDA\b|식품의약국|미국\s*식품의약국|품목허가', re.I)
KEYWORDS_EMA = re.compile(r'\bEMA\b|유럽\s*의약품청|유럽의약품청', re.I)
KEYWORDS_APPROVAL = re.compile(r'승인|허가|품목허가', re.I)

# 한국 매체 우선 (강제는 아님)
KOREAN_TLDS = ('.kr', 'naver.com', 'daum.net', 'chosun.com', 'hankyung.com', 'mk.co.kr', 'donga.com', 'joongang.co.kr', 'sedaily.com', 'etnews.com', 'hankyoreh.com', 'edaily.co.kr', 'yna.co.kr')

def guess_label(title, summary):
    t = f"{title} {summary or ''}"
    if KEYWORDS_EMA.search(t) and not KEYWORDS_FDA.search(t):
        return "EMA"
    if KEYWORDS_FDA.search(t):
        return "FDA"
    # 둘 다 없는 경우 요약 키워드로 추정
    if KEYWORDS_APPROVAL.search(t):
        # 모호하면 FDA로 기본
        return "FDA"
    return None

def is_korean_source(link):
    try:
        from urllib.parse import urlparse
        host = urlparse(link).hostname or ''
        return any(host.endswith(tld) for tld in KOREAN_TLDS)
    except Exception:
        return False

def fetch_all():
    items = []
    seen = set()
    for q in QUERIES:
        url = BASE + quote_plus(q)
        feed = feedparser.parse(url)
        for e in feed.entries:
            title = html.unescape(getattr(e, "title", "") or "").strip()
            link = getattr(e, "link", "").strip()
            summary = html.unescape(getattr(e, "summary", "") or "").strip()
            published = getattr(e, "published", "") or getattr(e, "updated", "") or ""
            # dedupe by link
            if not link or link in seen:
                continue
            seen.add(link)
            label = guess_label(title, summary)
            if not label:
                continue
            # 한국 매체 우선 필터 (완전 배제는 하지 않음)
            if not is_korean_source(link):
                # 한국어 기사지만 해외 도메인일 수 있어 통과는 시킴
                pass
            items.append({
                "title": title,
                "link": link,
                "summary": summary[:280],
                "published": parse_to_iso(published),
                "label": label,
                "source": getattr(e, "source", {}).get("title") if isinstance(getattr(e, "source", None), dict) else getattr(e, "source", None)
            })
    # 최신순 정렬
    items.sort(key=lambda x: x["published"], reverse=True)
    return items

def parse_to_iso(pub):
    try:
        # feedparser가 parsed_parsed 제공
        # 이게 없거나 실패하면 현재 시각으로
        return datetime(*feedparser._parse_date(pub)[:6], tzinfo=timezone.utc).isoformat()
    except Exception:
        try:
            # entry.published_parsed 접근
            return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def main():
    items = fetch_all()
    today = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    payload = {
        "generated_at": today,
        "items": items
    }
    # save latest
    with open(os.path.join(DATA, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # save dated file
    ymd = datetime.now().strftime("%Y-%m-%d")
    with open(os.path.join(DATA, f"{ymd}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(items)} items.")

if __name__ == "__main__":
    main()
