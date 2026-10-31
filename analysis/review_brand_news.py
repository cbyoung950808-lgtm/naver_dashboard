"""수집 뉴스 200행의 중복·관련성 검토표. 원자료를 삭제하거나 필터링하지 않는다.

관련성은 제목 및 API 요약에 대한 수동 검토이며 본문 전수 검증이 아니다.
동일 URL은 확정 중복, 같은 사건은 내용 중복 후보로 별도 기록한다.
행 ID는 원본 CSV의 데이터 행 순서(1부터), 검색 순위는 브랜드별 순위다.
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/processed"
SOURCE = FOLDER / "brand_news_20261031_100340_370067.csv"


def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 200
    annotations = {}
    def flag(ids, decision, topic, reason):
        for i in ids:
            assert i not in annotations
            annotations[i] = (decision, topic, reason)
    flag([102,103,104,105,122,123,125,126], "제외 권고", "가수 인기 투표", "탑텐은 텐아시아 투표 서비스명으로 의류 브랜드와 무관")
    flag([106], "제외 권고", "탑텐가요쇼", "탑텐가요쇼 방송 제목으로 의류 브랜드와 무관")
    flag([108], "제외 권고", "뉴스 탑텐", "기독교 매체의 주간 뉴스 10선으로 의류 브랜드와 무관")
    flag([116], "제외 권고", "음악 시상식 순위", "MAMA 베스트송 탑텐 의미. 본문에서도 시상 부문 문맥 확인")
    flag([184], "제외 권고", "무신사 플랫폼·타사 스탠다드핏", "브랜드명 대신 무신사 플랫폼과 타사 스탠다드핏이 분리 등장. 본문 확인 범위에서도 브랜드 직접 언급 미확인")
    flag([1], "판단 필요", "타 브랜드 비유", "고가 브랜드를 억만장자의 유니클로로 비유할 뿐 유니클로 소식이 아님. 브랜드 중심 분석이면 제외 권고")
    flag([2,35,47], "판단 필요", "캐릭터·타사 사업", "캐릭터 IP 또는 롯데홈쇼핑이 중심. 유니클로 협업 자체를 분석할 때만 유지")
    flag([7,23,24], "판단 필요", "백화점 인수", "롯데 센텀시티점 매각이 중심이며 유니클로는 입점 업체로 언급")
    flag([16,21,26], "판단 필요", "일본 기업 연봉", "일본 기업 임금 비교가 중심. 모회사 패스트리테일링 연봉 사례로만 등장")
    flag([22,28,30,33,48], "판단 필요", "경쟁사 중심", "무신사 또는 탑텐 기사에서 경쟁사·과거 마케팅 고객으로 유니클로 등장. 경쟁 동향이면 유지")
    flag([14,25,27], "판단 필요", "타사 상품·시장 비교", "다이소·대형마트·시온드가 중심이며 브랜드는 비교 또는 참고 사례. 비교 분석이면 유지")
    flag([31,34,38,42,43,44], "판단 필요", "런드리고 세탁 통계", "세탁 서비스의 트렌드 발표가 중심. 유니클로 니트 세탁량 수치는 있어 소비·사용 지표 분석이면 유지")
    flag([32,36,37,40], "판단 필요", "기프티엘 해킹", "쿠폰 서비스 장애가 중심. 브랜드 이용 고객 영향 분석이면 유지")
    flag([45], "판단 필요", "롯데 베트남 사업", "롯데 인재 확보·쇼핑몰 사업이 중심이며 유니클로는 입점 브랜드 나열")
    flag([51,66,83], "판단 필요", "이랜드 경영·재무", "이랜드 경영진·지배구조·유동성이 중심. 모회사 리스크까지 포함하면 유지")
    flag([68,69,*range(71,81),82,84], "판단 필요", "이랜드 소장품·기네스", "모회사 소장품과 기록 인증이 중심. 스파오 디자인 활용 연결은 있어 상품기획 분석이면 대표 기사 유지")
    flag([81], "판단 필요", "신한카드·캐릭터", "신한카드 상품이 중심이며 스파오는 캐릭터 협업 사례로만 언급")
    flag([88], "판단 필요", "메이아이 SM 납품", "SM 매장 AI 도입 기사에서 스파오는 공급업체의 기존 고객으로만 나열. 브랜드 중심이면 제외 권고")
    flag([89], "판단 필요", "동성로 상권", "무신사의 상권 기여가 중심. 스파오는 신규 출점 브랜드로 언급")
    flag([95], "판단 필요", "이랜드 미러폰드", "사진 촬영 공간이 중심이며 스파오는 의상 지원 브랜드. 협찬 활동 분석이면 유지")
    flag([64,97,98,99], "판단 필요", "경쟁사 중심", "다이소 또는 탑텐이 중심. 스파오는 비교 브랜드·매출·주변 매장으로 언급. 경쟁 동향이면 유지")
    flag([100], "판단 필요", "무신사 임원 과거 경력", "스파오는 무신사 임원의 이전 경력으로 등장. 스파오 중심 분석이면 제외하고 무신사 스탠다드 관련성은 별도 검토")
    flag([127], "판단 필요", "롯데몰 청량리", "쇼핑몰 방문기가 중심이며 탑텐은 입점 업체로 나열. 출점 정보 분석이면 유지")
    flag([133], "판단 필요", "유니클로 중심", "유니클로 한국 전략이 중심. 탑텐 투자 비교는 있어 경쟁 동향이면 유지")
    flag([153,155,157,159,160,162,163,164,*range(171,181),183], "판단 필요", "천안아산점 리뉴얼", "이번 스포츠·남성관 개편이 중심이며 무신사 스탠다드는 지난 9월 입점 브랜드. 과거 입점 사실을 신규 소식으로 중복 집계하지 않도록 주의")
    flag([170,188,189,190], "판단 필요", "롯데 센텀시티점 매각", "백화점 매각이 중심이며 브랜드는 2024년 입점 사례. 점포 유통망 분석이면 유지")
    flag([152], "판단 필요", "무신사 관련 도서", "무신사 성장사 도서 소개이며 브랜드 상품 성과도 설명. 도서·칼럼 포함 여부에 따라 판단")
    flag([161], "판단 필요", "무신사 뷰티 사업", "무신사와 올리브영 뷰티 경쟁이 중심. 무신사 스탠다드는 기존 사업 배경으로만 등장")
    flag([198], "판단 필요", "탑텐 중심", "탑텐 동성로점 기사에서 인근 경쟁 매장으로만 등장. 경쟁 상권 분석이면 유지")
    flag([192,195], "판단 필요", "무신사 플랫폼", "모회사 AI·IPO 또는 플랫폼 선호도가 중심. 브랜드 기여가 구분되지 않아 플랫폼 분석 포함 여부에 따라 판단")

    by_url = defaultdict(list)
    for i, r in enumerate(rows, 1):
        by_url[r["original_link"] or r["naver_link"]].append(i)
    dup_groups = {f"D{n:02d}": ids for n, ids in enumerate((g for g in by_url.values() if len(g)>1), 1)}
    dup_id = {i: gid for gid, ids in dup_groups.items() for i in ids}
    # 수동으로 제목·요약의 공통 사건을 확인한 후보. 본문 동일 여부를 뜻하지 않는다.
    stories = [
        ("유니클로 양말 가격 인상 철회", [3,4,8,12,13,15,17,18,19,20]),
        ("일본 대기업 연봉 통계", [16,21,26]),
        ("런드리고 가을 세탁 통계", [31,34,38,42,43,44]),
        ("이랜드 소장품·기네스 기록", [68,69,*range(71,81),82,84]),
        ("SPA 키즈 경량패딩 판매", [58,67,110,115,158,186]),
        ("무신사 AI 렌즈·패션업계 AI", [63,65]),
        ("텐텐데이 사흘 매출 309억원", [121,*range(128,133),*range(134,151)]),
        ("천안아산점 리뉴얼", [153,155,157,159,160,162,163,164,*range(171,181),183]),
        ("롯데 센텀시티점 인수·매각", [7,23,24,170,188,189,190]),
        ("무신사 일본 팝업 현장", [168,169,193,194]),
        ("무신사 K패션 생태계 육성", [22,33,185,187,200]),
        ("기프티엘 해킹·쿠폰 장애", [32,36,37,40]),
    ]
    story_id = {i:f"S{n:02d}" for n, (_, ids) in enumerate(stories,1) for i in ids}
    # 브랜드 자체 동향을 기본 범위로 삼고, 구체적인 상품 비교·소비 지표·고객 영향·
    # 디자인 활용·신규 출점·협찬 사실이 있는 경우는 유지한다. 관련성과 중복은 별도 판단.
    ambiguous_keep = {}
    def recommend_keep(ids, reason):
        for i in ids:
            assert annotations[i][0] == "판단 필요"
            ambiguous_keep[i] = reason
    recommend_keep([14,64], "다이소와 비교되는 브랜드 발열내의의 소재·보온 차별화가 구체적으로 제시되어 상품 경쟁 분석에 유효")
    recommend_keep([35], "유니클로 UTme!와 벨리곰 디자인 35종이라는 실제 협업 내용이 확인되어 브랜드 협업 사례로 유지")
    recommend_keep([31,34,38,42,43,44], "유니클로 니트 세탁량 7186벌이라는 브랜드별 사용 지표가 있음. 판매량으로 해석하지 말고 동일 이슈로 묶어 활용")
    recommend_keep([32,36,37,40], "브랜드가 취급되는 쿠폰 서비스의 이용 중단이라는 고객 접점 위험과 연결됨. 브랜드별 피해 규모가 확인됐다는 뜻은 아님")
    recommend_keep([68,69,*range(71,81),82,84], "스파오 디자이너의 실제 자료 이용·상품기획 연결이 명시되어 디자인 역량 자료로 유지. 모회사 기록 인증은 별도 태그로 구분")
    recommend_keep([89], "스파오의 동성로 신규 출점이 명시되어 상권 내 점포 확장 정보로 활용 가능")
    recommend_keep([95], "스파오의 의상 지원이라는 협찬 활동이 명시되어 브랜드 마케팅 자료로 활용 가능")
    recommend_keep([98], "스파오 매출 약 6000억원 등 브랜드 간 수치 비교가 제시되어 경쟁 실적 자료로 유지. 수치는 원문 검증 후 분석에 사용")
    recommend_keep([133], "탑텐의 가족 고객 대상 상품 구성·매장 개편·도심 확장이 설명되어 경쟁 전략 자료로 유지")
    recommend_keep([152], "도서 소개 형식이지만 무신사 스탠다드 슬랙스 판매 실적을 구체적으로 다뤄 브랜드 관련 자료로 유지. 칼럼·서평으로 구분")
    excluded_reasons = {
        "타 브랜드 비유": "다른 브랜드의 별칭에만 사용되어 대상 브랜드의 실제 활동·성과 정보가 없음",
        "캐릭터·타사 사업": "캐릭터 인기 또는 타사 사업이 중심이며 요약에 대상 브랜드 협업의 구체적 변화가 부족",
        "백화점 인수": "백화점 인수가 중심이고 기존 입점 사실만 제시되어 브랜드의 신규 변화로 보기 어려움",
        "일본 기업 연봉": "일본 기업 전반 및 모회사 임금 사례로서 브랜드 상품·실적·전략과 직접 연결되지 않음",
        "경쟁사 중심": "경쟁사 중심 기사에서 과거 고객·인근 매장·브랜드 나열 수준으로 등장. 구체적 브랜드 변화가 부족",
        "타사 상품·시장 비교": "타사 사업 또는 창업자의 과거 참고 사례가 중심이며 해당 브랜드의 현재 변화 정보가 부족",
        "롯데 베트남 사업": "롯데 사업·채용이 중심이며 대상 브랜드는 입점 목록에만 등장",
        "이랜드 경영·재무": "모회사 인물·경영·신용 이슈이며 스파오에 대한 구체적인 영향이 요약에서 확인되지 않음. 모회사 리스크 자료로는 별도 보관",
        "신한카드·캐릭터": "금융상품·캐릭터 흥행이 중심이며 스파오는 주변 사례로만 등장",
        "메이아이 SM 납품": "다른 고객에 대한 AI 납품이 중심이며 스파오는 공급업체 고객 명단에만 등장",
        "무신사 임원 과거 경력": "스파오는 임원의 과거 이력에만 등장. 현재 담당하는 무신사 스탠다드 관련 자료로 재분류 검토",
        "롯데몰 청량리": "탑텐은 기존 입점 업체 나열 수준이며 출점 시점·규모·성과 등 신규 정보가 확인되지 않음",
        "천안아산점 리뉴얼": "현재 개편은 스포츠·남성관 소식이며 브랜드는 지난 9월 입점 사례로 등장. 이번 신규 출점·브랜드 성과로 집계하지 않음",
        "롯데 센텀시티점 매각": "현재 백화점 매각의 배경으로 2024년 입점이 언급될 뿐 브랜드 매장의 향후 운영 변화는 미확인",
        "무신사 뷰티 사업": "모회사 뷰티 사업 경쟁이 중심이며 패션 브랜드는 배경 설명에만 등장",
        "탑텐 중심": "탑텐 매장 개편 기사에서 무신사 스탠다드는 인근 경쟁 매장으로만 등장",
        "무신사 플랫폼": "플랫폼 전체의 AI·IPO·선호도를 해당 PB 브랜드 성과와 구분하기 어려워 브랜드 중심 분석에서 제외",
    }
    output=[]
    for i,r in enumerate(rows,1):
        decision, topic, reason = annotations.get(i, ("유지 권고", "직접 관련·산업 비교", "제목 또는 요약에 브랜드 상품·실적·매장·협업·사회공헌 또는 구체적 산업 비교가 확인됨"))
        recommendation = decision
        recommendation_reason = reason
        if decision == "판단 필요":
            recommendation = "유지 권고" if i in ambiguous_keep else "제외 권고"
            recommendation_reason = ambiguous_keep.get(i) or excluded_reasons[topic]
        output.append({"행ID":i,"브랜드":r["brand"],"브랜드별 순위":r["rank"],"판단":decision,"분류":topic,
                       "판단 근거":reason,"최종 권고":recommendation,"권고 근거":recommendation_reason,
                       "권고 기준":"브랜드 자체 동향 및 구체적인 경쟁·소비·고객 영향 정보",
                       "중복 처리 권고":"통합 분석에서 동일 URL은 1건으로 집계하고 브랜드 연결은 유지" if i in dup_id else
                           ("동일 이슈 후보. 사건 수 분석은 묶고 노출량 분석은 별도 유지" if i in story_id else "추가 처리 없음"),
                       "확정 중복 그룹":dup_id.get(i,""),"동일 이슈 후보 그룹":story_id.get(i,""),
                       "제목":r["title"],"요약":r["description"],"날짜":r["published_at"],
                       "원문 링크":r["original_link"] or r["naver_link"],
                       "검토 범위":"제목·API 요약" + (" 및 웹 본문 확인" if i in [116,184] else "")})
    def save(name, records):
        with (FOLDER/name).open("w",encoding="utf-8-sig",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]))
            writer.writeheader();writer.writerows(records)
    save("브랜드뉴스_관련성_전체검토.csv",output)
    save("브랜드뉴스_제외권고_판단필요.csv",[r for r in output if r["판단"]!="유지 권고"])
    ambiguous=[r for r in output if r["판단"]=="판단 필요"]
    assert len(ambiguous)==85
    assert all(r["최종 권고"] in {"유지 권고","제외 권고"} and r["권고 근거"] for r in ambiguous)
    save("브랜드뉴스_애매한기사_권고사항.csv",ambiguous)
    print('애매한 기사 최종 권고',Counter(r['최종 권고'] for r in ambiguous))
    for brand in dict.fromkeys(r['brand'] for r in rows):
        print(brand,dict(Counter(r['최종 권고'] for r in ambiguous if r['브랜드']==brand)))
    duplicates=[]
    for gid,ids in dup_groups.items():
        first=rows[ids[0]-1]
        duplicates.append({"중복 그룹":gid,"제목":first["title"],"포함 브랜드":" / ".join(rows[i-1]["brand"] for i in ids),
                           "브랜드별 순위":" / ".join(f'{rows[i-1]["brand"]} #{rows[i-1]["rank"]}' for i in ids),
                           "수집 행수":len(ids),"합산시 초과 행수":len(ids)-1,"원문 링크":first["original_link"] or first["naver_link"]})
    save("브랜드뉴스_동일URL_중복목록.csv",duplicates)
    candidates=[]
    for n,(topic,ids) in enumerate(stories,1):
        candidates.append({"후보 그룹":f"S{n:02d}","공통 이슈":topic,"수집 행수":len(ids),
                           "고유 URL수":len({rows[i-1]["original_link"] or rows[i-1]["naver_link"] for i in ids}),
                           "기사 위치":" / ".join(f'{rows[i-1]["brand"]} #{rows[i-1]["rank"]}' for i in ids),
                           "권고":"같은 사건에 대한 별도 보도. 사건 건수 집계시 묶고 노출량·매체별 논조 분석시 유지. 본문 비교 후 병합 판단"})
    save("브랜드뉴스_동일이슈_중복후보.csv",candidates)
    print('전체',Counter(r['판단'] for r in output))
    for brand in dict.fromkeys(r['brand'] for r in rows):
        print(brand,dict(Counter(r['판단'] for r in output if r['브랜드']==brand)))
    print('동일URL 그룹',len(dup_groups),'초과행',sum(len(ids)-1 for ids in dup_groups.values()))
    for r in candidates: print(r['후보 그룹'],r['공통 이슈'],r['고유 URL수'])
    print('애매한 분류별')
    for (brand,topic),count in Counter((r['브랜드'],r['분류']) for r in output if r['판단']=='판단 필요').items():
        group=[r for r in output if r['판단']=='판단 필요' and r['브랜드']==brand and r['분류']==topic]
        print(brand,topic,count,','.join(r['브랜드별 순위'] for r in group))


if __name__ == "__main__":
    main()
