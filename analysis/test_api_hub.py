"""NAVER API HUB 19종 소량 연동 점검. 실행: .venv/bin/python analysis/test_api_hub.py"""
import csv
import argparse
import html
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://naverapihub.apigw.ntruss.com"


def cases(keyword=None):
    for slug, name in [("news", "뉴스"), ("encyc", "백과사전"),
                       ("blog", "블로그"), ("adult", "성인 검색어 판별"),
                       ("errata", "오타 변환"), ("webkr", "웹 문서"),
                       ("image", "이미지"), ("kin", "지식iN"),
                       ("local", "지역"), ("cafearticle", "카페글")]:
        if keyword and slug in {"adult", "errata", "image"}:
            continue  # 앞선 점검에서 비활성화로 확인된 API
        params = {"query": "spdlqj" if slug == "errata" else "커피", "format": "json"}
        if keyword:
            params["query"] = keyword
        if slug not in {"adult", "errata"}:
            params.update(display=(5 if slug == "local" else 10) if keyword else 2, start=1)
        yield "검색", name, "GET", f"/search/v1/{slug}", params
    end = datetime.now(ZoneInfo("Asia/Seoul")).date() - timedelta(days=2)
    period = {"startDate": str(end - timedelta(days=89 if keyword else 6)), "endDate": str(end), "timeUnit": "date"}
    yield "검색어 트렌드", "검색어 트렌드", "POST", "/search-trend/v1/search", {
        **period, "keywordGroups": ([{"groupName": keyword, "keywords": [keyword]}] if keyword else
                                   [{"groupName": "커피", "keywords": ["커피"]},
                                    {"groupName": "차", "keywords": ["녹차"]}])}
    if keyword:
        return  # 부동산 키워드에 임의의 쇼핑 카테고리를 지정하지 않는다.
    yield "쇼핑 인사이트", "분야별", "POST", "/shopping/v1/categories", {
        **period, "category": [{"name": "패션의류", "param": ["50000000"]}]}
    for dim, name in [("device", "기기별"), ("gender", "성별"), ("age", "연령별")]:
        yield "쇼핑 인사이트", name, "POST", f"/shopping/v1/category/{dim}", {
            **period, "category": "50000000"}
    yield "쇼핑 인사이트", "키워드별", "POST", "/shopping/v1/category/keywords", {
        **period, "category": "50000000", "keyword": [{"name": "정장", "param": ["정장"]}]}
    for dim, name in [("device", "키워드 기기별"), ("gender", "키워드 성별"), ("age", "키워드 연령별")]:
        yield "쇼핑 인사이트", name, "POST", f"/shopping/v1/category/keyword/{dim}", {
            **period, "category": "50000000", "keyword": "정장"}


def check(body, path):
    if not isinstance(body, dict):
        return "응답 형식 확인 필요", 0
    if any(k in body for k in ("error", "errorCode", "errMsg")):
        return "API 오류", 0
    if path.endswith("/adult"):
        return ("성공", 1) if str(body.get("adult")) in {"0", "1"} else ("응답 형식 확인 필요", 0)
    if path.endswith("/errata"):
        return ("성공" if body["errata"] else "성공(변환 없음)", 1) if "errata" in body else ("응답 형식 확인 필요", 0)
    if path.startswith("/search/v1/"):
        if not isinstance(body.get("items"), list):
            return "응답 형식 확인 필요", 0
        count = len(body["items"])
    else:
        if not isinstance(body.get("results"), list):
            return "응답 형식 확인 필요", 0
        count = sum(len(g.get("data", [])) for g in body["results"])
    return ("성공" if count else "성공(빈 결과)"), count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", help="입력 키워드로 활성 검색 7종 및 최근 90일 검색어 트렌드 조회")
    args = parser.parse_args()
    load_dotenv(ROOT / "api_keys.env", override=True)
    secrets = [os.getenv(k, "").strip() for k in ("NAVER_API_HUB_CLIENT_ID", "NAVER_API_HUB_CLIENT_SECRET")]
    if not all(secrets):
        raise SystemExit("api_keys.env에 인증값 입력이 필요합니다.")
    def safe(text):
        for secret in secrets:
            text = text.replace(secret, "[REDACTED]")
        return text
    stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S_%f")
    raw = ROOT / "data/raw" / f"api_test_{stamp}"
    raw.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    session.headers.update({"X-NCP-APIGW-API-KEY-ID": secrets[0], "X-NCP-APIGW-API-KEY": secrets[1]})
    rows = []
    items, trends = [], []
    for i, (group, name, method, path, payload) in enumerate(cases(args.keyword), 1):
        now = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        record = {"collected_at": now, "method": method, "url": BASE + path, "request": payload}
        status, result, count, detail = "", "통신 실패", 0, ""
        body = None
        try:
            response = session.request(method, BASE + path, timeout=(10, 30), allow_redirects=False,
                                       **({"params": payload} if method == "GET" else {"json": payload}))
            status = response.status_code
            record.update(http_status=status, response_text=response.text)
            try:
                body = response.json()
            except ValueError:
                body = None
            if response.ok:
                result, count = check(body, path)
                if result.startswith("성공") and args.keyword:
                    clean = lambda s: html.unescape(re.sub(r"<[^>]+>", "", str(s)))
                    for item in body.get("items", []):
                        items.append({"api": name, "query": args.keyword,
                                      **{k: clean(v) for k, v in item.items()}})
                    for series in body.get("results", []):
                        for point in series.get("data", []):
                            trends.append({"keyword": series["title"], **point})
            else:
                result = "HTTP 오류"
            if "오류" in result or "확인" in result:
                detail = safe(response.text)[:400]
        except requests.RequestException as exc:
            # 예외 문자열에는 요청 객체나 인증 헤더를 포함하지 않는다.
            detail = type(exc).__name__
            record["network_error"] = detail
        filename = f"{i:02d}_{path.strip('/').replace('/', '_')}.json"
        with (raw / filename).open("x", encoding="utf-8") as f:
            f.write(safe(json.dumps(record, ensure_ascii=False, indent=2)))
        rows.append(dict(group=group, api=name, method=method, endpoint=path, http_status=status,
                         result=result, records=count, total=body.get("total", "") if isinstance(body, dict) else "",
                         detail=detail, collected_at=now,
                         raw_file=str((raw / filename).relative_to(ROOT))))
        print(f"{name}: HTTP {status or '-'} / {result} / {count}건", flush=True)
    table = ROOT / "data/processed" / f"api_test_{stamp}.csv"
    table.parent.mkdir(parents=True, exist_ok=True)
    with table.open("x", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"결과표: {table.relative_to(ROOT)}")
    for label, data in [("search_items", items), ("search_trend", trends)]:
        if data:
            target = table.with_name(f"{label}_{stamp}.csv")
            fields = list(dict.fromkeys(k for row in data for k in row))
            with target.open("x", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(data)
            print(f"데이터: {target.relative_to(ROOT)}")
    if any(r["result"] == "통신 실패" for r in rows):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
