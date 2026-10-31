"""무신사 스탠다드와 무탠다드를 동일 요청에서 월별 비교한다."""
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]


def main():
    load_dotenv(ROOT/"api_keys.env",override=True)
    keys=[os.getenv(k,"").strip() for k in ["NAVER_API_HUB_CLIENT_ID","NAVER_API_HUB_CLIENT_SECRET"]]
    if not all(keys):raise SystemExit("인증값 입력 필요")
    body={"startDate":"2024-10-01","endDate":"2026-09-30","timeUnit":"month",
          "keywordGroups":[{"groupName":s,"keywords":[s]} for s in ["무신사 스탠다드","무탠다드"]]}
    now=datetime.now(ZoneInfo("Asia/Seoul"));stamp=now.strftime("%Y%m%d_%H%M%S_%f")
    url="https://naverapihub.apigw.ntruss.com/search-trend/v1/search"
    try:
        response=requests.post(url,json=body,headers={"X-NCP-APIGW-API-KEY-ID":keys[0],"X-NCP-APIGW-API-KEY":keys[1]},timeout=(10,45),allow_redirects=False)
    except requests.RequestException as exc:raise SystemExit(type(exc).__name__)
    record={"collected_at":now.isoformat(),"url":url,"request":body,"http_status":response.status_code,"response_text":response.text}
    text=json.dumps(record,ensure_ascii=False,indent=2)
    for key in keys:text=text.replace(key,"[REDACTED]")
    raw=ROOT/"data/raw"/f"musinsa_aliases_{stamp}.json"
    raw.write_text(text,encoding="utf-8")
    if response.status_code!=200:raise SystemExit(f"HTTP {response.status_code}")
    data=response.json();rows=[]
    for series in data["results"]:
        for p in series["data"]:
            rows.append({"검색어":series["title"],"월":p["period"][:7],"상대 검색지수":p["ratio"],"수집 시각":now.isoformat(),"원본 파일":str(raw.relative_to(ROOT))})
    assert len(rows)==48 and len({(r["검색어"],r["월"]) for r in rows})==48
    target=ROOT/"data/processed"/"무신사스탠다드_무탠다드_월별비교.csv"
    with target.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("HTTP 200 / 월별 관측 48개 저장 완료")


if __name__=="__main__":main()
