#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 뉴스 검색 결과를 기간(시작~종료일)으로 수집해서
data/latest.json 및 data/<from>_to_<to>.json 저장.

• 입력(환경변수 또는 CLI 인자):
  START=YYYY-MM-DD, END=YYYY-MM-DD (미입력 시 오늘=KST 기준)
• 의존성: requests, beautifulsoup4, feedparser(불필요하면 제거 가능)
"""

import os, re, json, html, time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

# 검색 쿼리 (한국기사 FDA/EMA 승인)
QUERIES = [
    'FDA 승인 한국 기업',
    'FDA 허가 한국 기업',
    'EMA 승인 한국 기업',
    'EMA 허가 한국 기업',
    '품목허가 FDA 한국',
    '품목허가 EMA 한국',
]

KEYWORDS_FDA = re.compile(r'\bFDA\b|미국\s*식품의약국|품목허가', re.I)
KEYWORDS_EMA = re.compile(r'\bEMA\b|유럽\s*의약품청', re.I)
KEYWORDS_APPROVAL = re.compile(r'승인|허가|품목허가', re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

def kst_today_ymd():
    return datetime.now(KST).strftime("%Y-%m-%d")

def ymd_to_naver_params(ymd: str):
    # Naver는 ds/de=YYYY.MM.DD, nso=fromYYYYMMDDtoYYYYMMDD 형식
    dt = datetime.strptime(ymd, "%Y-%m-%d")
    return dt.strftime("%Y.%m.%d"), dt.strftime("%Y%m%d")

def guess_label(title, summary):
    t = f"{title} {summary or ''}"
    if KEYWORDS_EMA.search(t) and not KEYWORDS_FDA.search(t):
        return "EMA"
    if KEYWORDS_FDA.search(t):
        return "FDA"
    if KEYWORDS_APPROVAL.search(t):
        return "FDA"
    return None

def parse_list_page(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    cards = []
    for area in soup.select("div.news_area"):
        a = area.select_one("a.news_tit")
        if not a: 
            continue
        title = (a.get("title") or a.text or "").strip()
        link = a.get("href") or ""
        press = (area.select_one("a.info.press") or area.select_one("span.info")).get_text(strip=True) if area.select_one("a.info.press") or area.select_one("span.info") else ""
        # 날짜: 보통 span.info 중 하나에 있음
        date_text = ""
        for s in area.select("span.info"):
            txt = s.get_text(strip=True)
            if any(x in txt for x in ["분 전","시간 전","일 전",".","-","202","201"]):
                date_text = txt
        # 네이버 상대 시간/날짜를 대충 ISO 로 변환 (KST)
        published = normalize_published(date_text)

        summary = ""
        dsc = area.select_one("div.news_dsc")
        if dsc:
            summary = dsc.get_text(" ", strip=True)

        cards.append({
            "title": title,
            "link": link,
            "summary": summary[:280],
            "published": published,
            "source": press
        })
    return cards

def normalize_published(txt):
    now = datetime.now(KST)
    try:
        if "분 전" in txt:
            m = int(re.findall(r"(\d+)\s*분", txt)[0])
            dt = now - timedelta(minutes=m)
        elif "시간 전" in txt:
            h = int(re.findall(r"(\d+)\s*시간", txt)[0])
            dt = now - timedelta(hours=h)
        elif "일 전" in txt:
            d = int(re.findall(r"(\d+)\s*일", txt)[0])
            dt = now - timedelta(days=d)
        else:
            # 예: 2025.08.15.
            txt = txt.replace(" ", "")
            dt = datetime.strptime(re.sub(r"[^\d\.]", "", txt), "%Y.%m.%d").replace(tzinfo=KST)
        return dt.isoformat()
    except Exception:
        return now.isoformat()

def fetch_range(start_ymd: str, end_ymd: str):
    ds_dot, ds_compact = ymd_to_naver_params(start_ymd)
    de_dot, de_compact = ymd_to_naver_params(end_ymd)
    nso = f"so:r,p:from{ds_compact}to{de_compact}"
    items = []
    seen = set()

    for q in QUERIES:
        page = 1
        while page <= 3:  # 페이지 더 늘릴 수 있음
            url = ("https://search.naver.com/search.naver?where=news&sm=tab_opt"
                   f"&query={quote_plus(q)}&sort=1&ds={ds_dot}&de={de_dot}&nso={nso}&start={(page-1)*10+1}")
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.raise_for_status()
            batch = parse_list_page(res.text)
            if not batch:
                break
            for it in batch:
                if it["link"] in seen:
                    continue
                seen.add(it["link"])
                label = guess_label(it["title"], it["summary"])
                if not label:
                    continue
                it["label"] = label
                items.append(it)
            page += 1
            time.sleep(0.6)  # 매너 대기
    # 최신순
    items.sort(key=lambda x: x["published"], reverse=True)
    return items

def main():
    start = os.environ.get("START") or (len(os.sys.argv) > 1 and os.sys.argv[1]) or kst_today_ymd()
    end   = os.environ.get("END")   or (len(os.sys.argv) > 2 and os.sys.argv[2]) or start

    items = fetch_range(start, end)

    now_kst = datetime.now(KST).isoformat(timespec="seconds")
    payload = {"generated_at": now_kst, "range": {"start": start, "end": end}, "items": items}

    # latest.json 갱신
    with open(os.path.join(DATA, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 범위 파일 저장
    name = f"{start}_to_{end}.json"
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(items)} items for {start}~{end} (KST).")

if __name__ == "__main__":
    main()
