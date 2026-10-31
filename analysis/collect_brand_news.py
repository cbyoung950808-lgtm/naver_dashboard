"""브랜드별 뉴스 최신순 50건 수집. 원본 응답과 통합 CSV 보존."""
import csv
import argparse
import html
import json
import os
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BRANDS = ["유니클로", "스파오", "탑텐", "무신사 스탠다드"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--display", type=int, default=50)
    args = parser.parse_args()
    if not 1 <= args.start <= 1000 or not 1 <= args.display <= 100:
        parser.error("start는 1~1000, display는 1~100이어야 합니다.")
    load_dotenv(ROOT / "api_keys.env", override=True)
    keys = [os.getenv(k, "").strip() for k in ["NAVER_API_HUB_CLIENT_ID", "NAVER_API_HUB_CLIENT_SECRET"]]
    if not all(keys):
        raise SystemExit("api_keys.env에 인증값 입력이 필요합니다.")
    def redact(text):
        for key in keys:
            text = text.replace(key, "[REDACTED]")
        return text
    stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S_%f")
    raw = ROOT / "data/raw" / f"brand_news_{stamp}"
    raw.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    session.headers.update({"X-NCP-APIGW-API-KEY-ID": keys[0], "X-NCP-APIGW-API-KEY": keys[1]})
    rows = []
    failed = False
    for brand in BRANDS:
        params = {"query": brand, "display": args.display, "start": args.start, "sort": "date", "format": "json"}
        now = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        record = {"collected_at": now, "method": "GET", "url": "https://naverapihub.apigw.ntruss.com/search/v1/news", "request": params}
        try:
            response = session.get(record["url"], params=params, timeout=(10, 30), allow_redirects=False)
        except requests.RequestException as exc:
            record["network_error"] = type(exc).__name__
            (raw / f"{brand}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
            print(f"{brand}: 통신 실패 ({type(exc).__name__})", flush=True)
            failed = True
            continue
        record.update(http_status=response.status_code, response_text=response.text)
        (raw / f"{brand}.json").write_text(redact(json.dumps(record, ensure_ascii=False, indent=2)), encoding="utf-8")
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code != 200 or not isinstance(body.get("items"), list):
            print(f"{brand}: HTTP {response.status_code} / 응답 오류", flush=True)
            failed = True
            continue
        clean = lambda v: html.unescape(re.sub(r"<[^>]+>", "", v))
        for rank, item in enumerate(body["items"], args.start):
            rows.append({"brand": brand, "rank": rank,
                         "published_at": parsedate_to_datetime(item["pubDate"]).astimezone(ZoneInfo("Asia/Seoul")).isoformat(),
                         "title": clean(item["title"]), "description": clean(item["description"]),
                         "original_link": item.get("originallink", ""), "naver_link": item.get("link", ""),
                         "query": brand, "sort": "date", "collected_at": now,
                         "raw_file": str((raw / f"{brand}.json").relative_to(ROOT))})
        print(f"{brand}: HTTP 200 / {len(body['items'])}건", flush=True)
    if rows:
        target = ROOT / "data/processed" / f"brand_news_{stamp}.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"결과: {target.relative_to(ROOT)}")
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
