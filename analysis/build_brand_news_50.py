"""기존 권고를 유지하고 추가 뉴스의 제목·API 요약을 수동 검토해 브랜드당 50건 구성.

기존 200건 검토 기준과 동일: 직접 상품·성과·협업·고객영향·구체적 경쟁 자료 유지,
단순 나열·과거 이력·비유·브랜드별 영향이 불분명한 모회사 소식 제외.
같은 URL은 브랜드 안에서 중복 제외하고 브랜드 간 연결은 유지한다.
동일 사건의 다른 매체 기사는 유지하되 이슈 그룹으로 묶는다.
본문을 읽지 않은 기사에 본문 검증을 했다고 표시하지 않는다.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"data/processed"
EXTRA=FOLDER/"brand_news_20261031_102219_260942.csv"
BRANDS=["유니클로","스파오","탑텐","무신사 스탠다드"]


def canonical(url):
    p=urlsplit(url)
    params=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True)
            if not k.lower().startswith("utm_") and not (k.lower() in {"ref","outurl","sc"} and v.lower()=="naver")]
    return p.netloc.lower().removeprefix("www.")+p.path.rstrip("/")+("?"+urlencode(sorted(params)) if params else "")


def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def save(name,rows):
    path=FOLDER/name
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    assert len(read(path))==len(rows)


def issue(brand,title,summary,old=""):
    text=title+" "+summary
    if brand=="유니클로":
        if "보험" in text and any(x in text for x in ["희망브리지","재해"]):return "유니클로_재해보험료지원"
        if "앱" in text and any(x in text for x in ["58%","157만"]):return "유니클로_앱사용자통계"
    if brand=="스파오":
        if any(x in text for x in ["야장","윈드브레이커"]):return "스파오_야장바람막이소개"
        if "치이카와" in text and any(x in text for x in ["품절","동났다"]):return "스파오_치이카와상품흥행"
    if brand=="탑텐" and "텐텐데이" in text:
        if "309" in text or ("사흘" in text and "300" in text):return "탑텐_텐텐데이매출발표"
        return "탑텐_텐텐데이할인행사"
    if brand=="무신사 스탠다드":
        if "청량리" in text and any(x in text for x in ["600평","12월"]):return "무신사스탠다드_청량리확장이전예정"
        if "슈퍼세일" in text:return "무신사스탠다드_FW슈퍼세일"
        if "서울굿즈" in text or "서울마이소울" in text:return "무신사스탠다드_서울시협업굿즈"
        if "동성로" in text and any(x in text for x in ["349만","662만","660만"]):return "무신사스탠다드_동성로방문객발표"
    return old


def main():
    original=read(FOLDER/"brand_news_20261031_100340_370067.csv")
    reviews=read(FOLDER/"브랜드뉴스_관련성_전체검토.csv")
    extras=read(EXTRA)
    assert len(original)==len(reviews)==200 and len(extras)==400
    decisions={b:{} for b in BRANDS}
    def set_review(b,ranks,keep,reason):
        for rank in ranks:
            assert rank not in decisions[b]
            decisions[b][rank]=(keep,reason)
    b="유니클로"
    set_review(b,[51,56,70],False,"롯데 경영진의 과거 유니클로 운영사 경력으로만 등장")
    set_review(b,[53],False,"아마존 부족 관련 인터뷰의 비유·질문으로 사용되어 브랜드 뉴스와 무관")
    set_review(b,[52,54,60,62,63,66,67],True,"유니클로 앱 이용자 157만명 또는 증가율 58%라는 구체적인 브랜드 지표")
    set_review(b,[55,57,58,59,61,64,65,68],True,"유니클로가 후원하는 재해보험료 지원 사업으로 직접적인 사회공헌 활동")
    set_review(b,[69],False,"미술 전시 개인 체험에 협업 티셔츠 구매가 등장할 뿐 브랜드의 신규 동향은 아님")
    set_review(b,[71],False,"게임 팝업 중심이며 유니클로 협업은 구체적 상품 설명 없이 브랜드 명단에만 등장")
    set_review(b,[72],False,"롯데 베트남 개발이 중심이며 유니클로는 입점 브랜드 명단에만 등장")
    set_review(b,[73],True,"디즈니런 공식 협찬사로 참여해 체험 콘텐츠를 운영한 마케팅 활동")
    set_review(b,[74],False,"무신사 중심 상권 기사에서 지난해 유니클로 재출점을 과거 배경으로 제시")
    set_review(b,[75],True,"유니클로 회계연도 매출과 성장률의 구체적인 산업 비교 자료")
    set_review(b,[76],True,"유니클로 명동 대형점 재개장과 경쟁 브랜드 공간 전략을 구체적으로 비교")
    b="스파오"
    set_review(b,[51,52],True,"동성로 2호점 확장 또는 경주점 지역 특화 상품 등 구체적인 점포·상품 전략")
    set_review(b,[53],True,"팬 요청을 반영하는 스파오 상품기획 전략을 직접 다룸")
    set_review(b,[54,57],True,"스파오 치이카와 협업 상품 종류와 품절 성과가 구체적으로 제시됨")
    set_review(b,[55],False,"10년 전 기사를 재소개하는 과거 자료로 현재 브랜드 동향 집계에서 제외")
    set_review(b,[56],False,"유니클로 중심 기사이며 스파오에 대한 구체적 변화·실적 없이 일반적 경쟁 배경으로 언급")
    set_review(b,[58,59,60,61,62,63],True,"스파오 라이트 후드 윈드브레이커의 발수·투웨이 지퍼 등 제품 특성을 구체적으로 소개")
    b="탑텐"
    set_review(b,[51],True,"탑텐 텐텐데이 실제 매출 발표로 직접 관련. 같은 사건의 다른 원문은 유지")
    set_review(b,[52],True,"탑텐키즈 플러피플리스 상품 구성과 패밀리룩 전략을 구체적으로 제시")
    set_review(b,[53,58],True,"탑텐 에어테크 파카의 가격을 명시한 경쟁 상품 비교")
    set_review(b,[54,55],True,"탑텐 실적·기능성 상품·차세대 매장 등 구체적 브랜드 경쟁 전략")
    set_review(b,[56,61,66,71,73,75,78,80],True,"탑텐 텐텐데이 일정·상품·할인 등 구체적인 행사 정보")
    set_review(b,[57],True,"탑텐 에어테크 파카의 공동 개발 충전재와 보온성을 직접 소개")
    set_review(b,[59],True,"탑텐 대구 동성로점의 리뉴얼 소식을 구체적으로 다룸")
    set_review(b,[60],True,"탑텐 에어테크 착용 상품 및 가격을 구체적으로 다룬 스타일 기사")
    set_review(b,[62,63,64,65,72,76,79],False,"롯데몰 소개에서 탑텐은 입점 브랜드 나열 수준. 신규 매장 변화·성과 미확인")
    set_review(b,[67,68,69,70,74],False,"텐아시아 인기투표 또는 기독교 뉴스 10선으로 의류 브랜드와 무관")
    set_review(b,[77],True,"탑텐키즈 매장의 할인 행사와 할인율을 구체적으로 안내")
    b="무신사 스탠다드"
    set_review(b,[51,53,54,55,56,59],False,"무신사 전체 고용 규모가 중심이며 해당 브랜드별 인원·성과가 분리되지 않음")
    set_review(b,[52,92,98,99,100,104,105,108,109,113,114,117],True,"무신사 스탠다드 FW 슈퍼세일의 일정·매장·할인 등 직접 행사 정보")
    set_review(b,[57,65,70],True,"해당 브랜드의 외국인 매출 비중 또는 쇼핑시설 입점 비율 등 구체적인 지표")
    set_review(b,[58,66,86,94,95,96,102,106,107,110,111,112,115],True,"청량리 매장의 약 600평 확장·이전 또는 12월 개장 예정이라는 구체적 신규 정보. 예정 단계로 표시")
    set_review(b,[60,61],True,"서울시 협업 의류의 출시·라운지 판매라는 구체적인 협업과 유통 접점")
    set_review(b,[62,75,76,82,89],True,"시티레저·키즈·반려견 상품의 디자인·색상·매출 등 직접 상품 정보")
    set_review(b,[63,79,91],True,"GS25 협업 익스프레스·힛탠다드 상품과 유통 확대 정보")
    set_review(b,[64,68,85],False,"무신사 성장·IPO 중심이며 브랜드의 구체적 신규 변화와 플랫폼·전체 제품 매출이 구분되지 않음")
    set_review(b,[67,87],True,"명동 신규 대형점과 외국인 관광 수요 등 구체적인 브랜드 오프라인 전략")
    set_review(b,[69,71,73],False,"의약품 유통사 바로팜의 사업 설명에서 무신사 스탠다드를 비유로 사용")
    set_review(b,[72],False,"한남 상권 설명에서 2024년 입점을 과거 배경으로 소개하여 신규 브랜드 동향 집계에서 제외")
    set_review(b,[74,77,80,81,84],True,"브랜드 매장별 판매·방문객·창원점 개점 실적·연간 판매액 등 구체적인 성과")
    set_review(b,[78],False,"무신사 뷰티 개장 기사에서 인근 기존 매장 위치로만 등장")
    set_review(b,[83],True,"카스 라이트와 무신사 스탠다드 스포츠의 실제 러닝웨어 협업")
    set_review(b,[88],True,"무신사 스탠다드 서울숲점의 연내 개장 예정이라는 구체적 출점 정보")
    set_review(b,[90],False,"정치단체 사무실을 설명하는 비유로 브랜드가 등장해 의류 브랜드 뉴스와 무관")
    set_review(b,[93],True,"동궁 협업 상품 출시 및 관련 캠페인 트래픽이 제시됨. 트래픽을 브랜드 단독 성과로 해석하지 않음")
    set_review(b,[97],False,"퀴즈 정답 안내가 중심이며 행사 자체 기사와 구분해 분석에서 제외")
    set_review(b,[101,103],False,"쇼핑몰 소개에 브랜드가 등장하나 요약의 개장 시점이 다른 기사와 상충하거나 상품·점포 변화가 불충분")

    final=[]; audit=[]; summary=[]
    for brand in BRANDS:
        chosen=[];seen=set()
        for r in reviews:
            if r["브랜드"]!=brand or r["최종 권고"]!="유지 권고":continue
            idx=int(r["행ID"])-1
            original_row=original[idx]
            assert original_row["brand"]==brand and original_row["title"]==r["제목"]
            url=r["원문 링크"];key=canonical(url)
            assert key not in seen
            seen.add(key)
            chosen.append({"브랜드":brand,"제목":r["제목"],"요약":r["요약"],"날짜":r["날짜"],"원문 링크":url,
                           "수집 구분":"기존 유지","검색어":original_row["query"],"검색 순위":r["브랜드별 순위"],
                           "수집 시각":original_row["collected_at"],"채택 근거":r["권고 근거"],
                           "검토 범위":r["검토 범위"],"원본 파일":original_row["raw_file"],
                           "동일 이슈 그룹":issue(brand,r["제목"],r["요약"],r["동일 이슈 후보 그룹"])})
        base=len(chosen);checked=0;excluded=0;dupes=0;last_rank=0
        for r in (x for x in extras if x["brand"]==brand):
            rank=int(r["rank"]);url=r["original_link"] or r["naver_link"];key=canonical(url)
            result="";reason=""
            if len(chosen)>=50:
                result="미검토·목표 충족";reason="이미 브랜드별 50건을 확보해 개별 관련성 판단에 사용하지 않은 여분 후보"
            elif key in seen:
                checked+=1;dupes+=1;last_rank=rank
                result="중복 제외";reason="동일 브랜드 내에 같은 원문 URL이 이미 채택됨"
            else:
                assert rank in decisions[brand],f"추가 검토 필요: {brand} #{rank}"
                keep,reason=decisions[brand][rank]
                checked+=1;last_rank=rank
                result="유지" if keep else "관련성 제외"
                if keep:
                    seen.add(key)
                    chosen.append({"브랜드":brand,"제목":r["title"],"요약":r["description"],"날짜":r["published_at"],"원문 링크":url,
                                   "수집 구분":"추가 채택","검색어":r["query"],"검색 순위":r["rank"],"수집 시각":r["collected_at"],
                                   "채택 근거":reason,"검토 범위":"제목·API 요약","원본 파일":r["raw_file"],
                                   "동일 이슈 그룹":issue(brand,r["title"],r["description"])})
                else:excluded+=1
            audit.append({"브랜드":brand,"검색 순위":rank,"처리":result,"판단 근거":reason,"제목":r["title"],
                          "요약":r["description"],"날짜":r["published_at"],"원문 링크":url,
                          "수집 시각":r["collected_at"],"원본 파일":r["raw_file"]})
        assert len(chosen)==50,f"{brand} 부족: {len(chosen)}"
        chosen.sort(key=lambda r:(r["날짜"],-int(r["검색 순위"])),reverse=True)
        for n,r in enumerate(chosen,1):r["브랜드별 최신순 번호"]=n
        final.extend(chosen)
        dates=[r["날짜"] for r in chosen]
        summary.append({"브랜드":brand,"기존 유지":base,"추가 채택":len(chosen)-base,"최종 기사수":len(chosen),
                        "추가 후보 수집":100,"추가 검토":checked,"추가 관련성 제외":excluded,"추가 동일URL 제외":dupes,
                        "미검토 여분":100-checked,"검토 마지막 검색 순위":last_rank,"최신 발행일":max(dates),"최초 발행일":min(dates)})
    assert Counter(r["브랜드"] for r in final)=={b:50 for b in BRANDS}
    assert len({(r["브랜드"],canonical(r["원문 링크"])) for r in final})==200
    # 기존 제외 권고와 동일한 브랜드-원문 조합이 재유입되지 않았는지 검증한다.
    rejected={(r["브랜드"],canonical(r["원문 링크"])) for r in reviews if r["최종 권고"]=="제외 권고"}
    assert not rejected.intersection((r["브랜드"],canonical(r["원문 링크"])) for r in final)
    for r in final:assert (ROOT/r["원본 파일"]).exists()
    save("브랜드별_뉴스_50건씩_분석용.csv",final)
    save("브랜드뉴스_추가수집_검토내역.csv",audit)
    save("브랜드뉴스_50건확보_요약.csv",summary)
    grouped=defaultdict(list)
    for r in final:grouped[canonical(r["원문 링크"])].append(r)
    unique=[]
    for records in grouped.values():
        representative=max(records,key=lambda r:len(r["요약"]))
        unique.append({"관련 브랜드":" / ".join(r["브랜드"] for r in records),"제목":representative["제목"],
                       "요약":representative["요약"],"날짜":representative["날짜"],"원문 링크":representative["원문 링크"],
                       "브랜드별 요약":json.dumps({r["브랜드"]:r["요약"] for r in records},ensure_ascii=False)})
    unique.sort(key=lambda r:r["날짜"],reverse=True)
    save("브랜드뉴스_50건씩_동일URL통합.csv",unique)
    for row in summary:print(row)
    print('합계',len(final),'고유 원문',len(unique))


if __name__=="__main__":main()
