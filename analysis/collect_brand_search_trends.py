"""최근 24개 완료 월의 브랜드 검색 트렌드: 전체·연령·성별·기기·탑텐 보완어.
실행: .venv/bin/python analysis/collect_brand_search_trends.py
"""
import csv
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
BRANDS={"유니클로":["유니클로"],"스파오":["스파오"],"탑텐":["탑텐"],"무신사 스탠다드":["무신사 스탠다드","무탠다드"]}
SEGMENTS=[("전체","전체",{}),
          ("연령","13~18세",{"ages":["2"]}), ("연령","19~24세",{"ages":["3"]}),
          ("연령","25~29세",{"ages":["4"]}), ("연령","30~39세",{"ages":["5","6"]}),
          ("연령","40~49세",{"ages":["7","8"]}), ("연령","50~59세",{"ages":["9","10"]}),
          ("연령","60세 이상",{"ages":["11"]}),
          ("성별","남성",{"gender":"m"}), ("성별","여성",{"gender":"f"}),
          ("기기","PC",{"device":"pc"}), ("기기","모바일",{"device":"mo"}),
          ("보완조회","탑텐 보완어",{})]


def main():
    load_dotenv(ROOT/"api_keys.env",override=True)
    keys=[os.getenv(k,"").strip() for k in ["NAVER_API_HUB_CLIENT_ID","NAVER_API_HUB_CLIENT_SECRET"]]
    if not all(keys):raise SystemExit("api_keys.env 입력 필요")
    today=datetime.now(ZoneInfo("Asia/Seoul")).date()
    end=today.replace(day=1)-timedelta(days=1)
    end_num=end.year*12+end.month-1;start_num=end_num-23
    start=date(start_num//12,start_num%12+1,1)
    stamp=datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S_%f")
    raw=ROOT/"data/raw"/f"brand_search_trends_{stamp}";raw.mkdir(parents=True,exist_ok=False)
    session=requests.Session()
    session.headers.update({"X-NCP-APIGW-API-KEY-ID":keys[0],"X-NCP-APIGW-API-KEY":keys[1]})
    rows=[];manifest=[];failed=False
    def redact(s):
        for key in keys:s=s.replace(key,"[REDACTED]")
        return s
    for n,(kind,label,filters) in enumerate(SEGMENTS,1):
        groups={k:list(v) for k,v in BRANDS.items()}
        if kind=="보완조회":groups["탑텐"]=["탑텐몰","TOPTEN10"]
        body={"startDate":str(start),"endDate":str(end),"timeUnit":"month",
              "keywordGroups":[{"groupName":k,"keywords":v} for k,v in groups.items()],**filters}
        now=datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        record={"collected_at":now,"segment_type":kind,"segment":label,
                "url":"https://naverapihub.apigw.ntruss.com/search-trend/v1/search","request":body}
        filename=raw/f"{n:02d}.json"
        try:
            response=session.post(record["url"],json=body,timeout=(10,45),allow_redirects=False)
            record.update(http_status=response.status_code,response_text=response.text)
            filename.write_text(redact(json.dumps(record,ensure_ascii=False,indent=2)),encoding="utf-8")
            if response.status_code!=200:
                print(f"{label}: HTTP {response.status_code}",flush=True);failed=True;continue
            parsed=response.json()
            if not isinstance(parsed.get("results"),list):
                print(f"{label}: 응답 형식 오류",flush=True);failed=True;continue
            count=0
            for g in parsed["results"]:
                for point in g.get("data",[]):
                    rows.append({"구분":kind,"세그먼트":label,"브랜드":g["title"],"월":point["period"][:7],
                                 "검색지수":point["ratio"],"검색어 묶음":" / ".join(groups[g["title"]]),
                                 "조회 시작일":str(start),"조회 종료일":str(end),"수집 시각":now,
                                 "원본 파일":str(filename.relative_to(ROOT))})
                    count+=1
            manifest.append({"구분":kind,"세그먼트":label,"HTTP":200,"관측수":count,
                             "원본 파일":str(filename.relative_to(ROOT))})
            print(f"{kind} {label}: HTTP 200 / {count}개 월별 관측",flush=True)
        except (requests.RequestException,ValueError) as exc:
            record["exception_type"]=type(exc).__name__
            if not filename.exists():filename.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
            print(f"{label}: {type(exc).__name__}",flush=True);failed=True
    processed=ROOT/"data/processed"
    for name,data in [(f"브랜드_검색트렌드_{stamp}.csv",rows),(f"브랜드_검색트렌드_수집내역_{stamp}.csv",manifest)]:
        if data:
            with (processed/name).open("x",encoding="utf-8-sig",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
            print(name)
    if failed:raise SystemExit(2)


if __name__=="__main__":main()
