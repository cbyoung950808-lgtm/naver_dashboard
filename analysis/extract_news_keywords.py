"""실행: .venv-nlp/bin/python analysis/extract_news_keywords.py

브랜드 4개·주제 5개·브랜드×주제 20개의 BoW/TF-IDF 비교 및 워드클라우드.
원문 전체가 아닌 제목+API 요약 분석. TF-IDF의 IDF는 고유 URL 165개를 기준으로
한 번 학습하고 모든 그룹에 공통 적용한다. 그룹 내 URL 중복은 제거한다.
"""
import csv
import json
import math
import os
import re
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "naver-news-matplotlib"))

import numpy as np
from kiwipiepy import Kiwi
from PIL import Image, ImageDraw, ImageFont
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from wordcloud import WordCloud

from build_brand_news_50 import canonical

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/processed"
FIG=ROOT/"outputs/figures/news_keywords"
FONT="/Library/Fonts/NanumBarunGothic.ttf"
BRANDS=["유니클로","스파오","탑텐","무신사 스탠다드"]
TOPICS=["제품 출시","협업","할인 혹은 행사","실적 또는 사업","기타"]
STOP=set("유니클로 스파오 탑텐 무신사 스탠다드 무탠다드 키즈탑텐 스파오키즈 탑텐키즈 무신사스탠다드키즈 브랜드 기자 뉴스 기사 사진 제공 출처 관계자 업계 이번 올해 지난해 지난 최근 내년 다음 당시 경우 가운데 통해 관련 해당 비롯 각종 대표 국내 글로벌 패션 의류 상품 제품 시장 중심 주요 운영 공개 발표 결과 기록 기준 동안 기간 대상 모습 다양 구성 강화 확대 증가 이상 최대 최초 부문 분야 수준 규모 약 전 후 곳 명 원 만 억 개 점 종 벌 일 월 년 시간 배 수 등 것 이 그 더 및 또 가장 특히 현재 이후 앞서 함께 한편 때문 서비스 korea news uniqlo spao topten topten10 musinsa standard fw spa kids".split())
STOP.update("afp gq 전체 자체 전년 하반기 상반기 사흘 첫날".split())
COMPOUNDS=["경량패딩","발열내의","텐텐데이","슈퍼세일","풍수해","재해보험","재해보험료","희망브리지",
           "동성로","청량리","명동","성수","플러피플리스","씬라이트","에어테크","히트텍","웜테크",
           "시티레저","치이카와","먼작귀","벨리곰","기프티엘","패밀리룩","팝업스토어","윈드브레이커",
           "소장품","상품기획","경계선지능","오프라인","온라인","패스트리테일링",
           "올리브영","에이블리","런드리고","롯데시네마","GS25","신성통상","이랜드월드","이랜드","미쏘"]


def save_csv(name,rows,fields=None):
    with (DATA/name).open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields or list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    FIG.mkdir(parents=True,exist_ok=True)
    with (DATA/"브랜드별_뉴스_주제분류_200건.csv").open(encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
    assert len(rows)==200 and Path(FONT).exists()
    kiwi=Kiwi(num_workers=1)
    for word in COMPOUNDS:kiwi.add_user_word(word,"NNP")
    def tokens(text):
        text=re.sub(r"<[^>]+>|https?://\S+"," ",text)
        text=re.sub(r"(?:무신사\s*스탠다드|MUSINSA\s*STANDARD|유니클로|UNIQLO|스파오|SPAO|탑텐|TOPTEN10|TOPTEN|무탠다드|무신사|MUSINSA)\s*(?:키즈|KIDS)?", " ", text, flags=re.I)
        for pattern,replacement in [(r"경량\s*패딩","경량패딩"),(r"발열\s*내의","발열내의"),
                                    (r"시티\s*레저","시티레저"),(r"팝업\s*스토어","팝업스토어"),
                                    (r"무신사\s*스탠다드","무신사스탠다드"),
                                    (r"풍수해[·ㆍ\s]*지진재해보험","재해보험")]:
            text=re.sub(pattern,replacement,text)
        result=[]
        for t in kiwi.tokenize(text):
            if t.tag not in {"NNG","NNP","SL"}:continue
            word=t.form.lower().strip()
            if word in STOP or len(word)<2 or not re.fullmatch(r"[가-힣a-z][가-힣a-z0-9]*",word):continue
            if any(b in word for b in ["유니클로","스파오","탑텐","무신사","스탠다드"]):continue
            word={"먼작귀":"치이카와","gs25":"GS25","ip":"IP","ai":"AI"}.get(word,word)
            result.append(word)
        return result
    tokenized=[tokens(r["제목"]+" "+r["요약"]) for r in rows]
    urls=defaultdict(list)
    for i,r in enumerate(rows):urls[canonical(r["원문 링크"])].append(i)
    assert len(urls)==165
    # 같은 기사의 브랜드별 검색 요약에만 있는 단어도 문서빈도 계산에 포함한다.
    corpus=[list(dict.fromkeys(t for i in ids for t in tokenized[i])) for ids in urls.values()]
    vectorizer=CountVectorizer(analyzer=lambda x:x,lowercase=False,min_df=1)
    unique_counts=vectorizer.fit_transform(corpus)
    counts=vectorizer.transform(tokenized)
    transformer=TfidfTransformer(norm="l2",use_idf=True,smooth_idf=True,sublinear_tf=False)
    transformer.fit(unique_counts)
    tfidf=transformer.transform(counts)
    words=vectorizer.get_feature_names_out()
    df=np.asarray((unique_counts>0).sum(axis=0)).ravel()
    assert np.allclose(transformer.idf_,np.log((1+len(corpus))/(1+df))+1)
    assert int(counts.sum())==sum(map(len,tokenized))
    assert all(len(x)>0 for x in tokenized)
    sample=counts[0].toarray().ravel()*transformer.idf_
    sample/=np.linalg.norm(sample)
    assert np.allclose(sample,tfidf[0].toarray().ravel())
    token_rows=[{"브랜드":r["브랜드"],"대표 주제":r["대표 주제"],"분류ID":r["분류ID"],
                 "명사 토큰 수":len(ts),"분석 토큰":" ".join(ts),"원문 링크":r["원문 링크"]} for r,ts in zip(rows,tokenized)]
    save_csv("뉴스_키워드분석_전처리.csv",token_rows)
    save_csv("뉴스_키워드분석_불용어.csv",[{"불용어":w} for w in sorted(STOP)])
    groups=[]
    for b in BRANDS:groups.append(("브랜드",b,"전체",[i for i,r in enumerate(rows) if r["브랜드"]==b]))
    for t in TOPICS:groups.append(("주제","전체",t,[i for i,r in enumerate(rows) if r["대표 주제"]==t]))
    for b in BRANDS:
        for t in TOPICS:groups.append(("브랜드×주제",b,t,[i for i,r in enumerate(rows) if r["브랜드"]==b and r["대표 주제"]==t]))
    long=[];comparison=[];inventory=[];pairs={}
    font=ImageFont.truetype(FONT,27)
    small=ImageFont.truetype(FONT,22)
    def ranked(values):return sorted((i for i,v in enumerate(values) if v>0),key=lambda i:(-values[i],words[i]))
    for gnum,(scope,brand,topic,ids) in enumerate(groups,1):
        # 통합 주제에 같은 기사가 여러 브랜드로 등장하면 긴 요약 한 개만 대표로 사용.
        selected={}
        for i in ids:
            key=canonical(rows[i]["원문 링크"])
            if key not in selected or len(rows[i]["요약"])>len(rows[selected[key]]["요약"]):selected[key]=i
        idx=list(selected.values());n=len(idx)
        bow=np.asarray(counts[idx].sum(axis=0)).ravel() if n else np.zeros(len(words))
        tf=np.asarray(tfidf[idx].mean(axis=0)).ravel() if n else np.zeros(len(words))
        termdf=np.asarray((counts[idx]>0).sum(axis=0)).ravel() if n else np.zeros(len(words))
        rb,rt=ranked(bow),ranked(tf)
        meta={"구분":scope,"브랜드":brand,"주제":topic,"입력 기사행수":len(ids),"분석 고유기사수":n}
        for rank in range(min(20,max(len(rb),len(rt)))):
            ib=rb[rank] if rank<len(rb) else None;it=rt[rank] if rank<len(rt) else None
            comparison.append({**meta,"순위":rank+1,"BoW 키워드":words[ib] if ib is not None else "",
                               "BoW 출현횟수":int(bow[ib]) if ib is not None else "",
                               "TF-IDF 키워드":words[it] if it is not None else "",
                               "TF-IDF 평균점수":round(float(tf[it]),8) if it is not None else ""})
        for method,values,order in [("BoW",bow,rb),("TF-IDF",tf,rt)]:
            for rank,j in enumerate(order,1):long.append({**meta,"방식":method,"순위":rank,"키워드":words[j],
                                                        "점수":round(float(values[j]),8),"기사빈도":int(termdf[j])})
        pair=Image.new("RGB",(1600,590),"white");draw=ImageDraw.Draw(pair)
        title=f"{brand if scope!='주제' else topic}"+(f" · {topic}" if scope=="브랜드×주제" else "")
        draw.text((30,14),f"{title}  |  기사 {n}건",font=font,fill="#172b40")
        for c,(method,values,order) in enumerate([("BoW",bow,rb),("TF-IDF",tf,rt)]):
            x=20+c*800
            draw.text((x+12,59),method+(" · 출현횟수" if c==0 else " · 평균 중요도"),font=small,fill="#34506b")
            if order:
                wc=WordCloud(font_path=FONT,width=760,height=425,background_color="white",max_words=45,
                             random_state=42,collocations=False,prefer_horizontal=1,min_font_size=15,
                             max_font_size=105,relative_scaling=.55,
                             color_func=lambda *args,random_state=None,**kwargs:
                                 random_state.choice(["#174c75","#226b95","#244357","#2b6280"] if c==0 else
                                                     ["#195e51","#256b69","#315481","#533c77"]))
                wc.generate_from_frequencies({str(words[j]):float(values[j]) for j in order[:45]})
                pair.paste(wc.to_image(),(x,95))
                top=" · ".join(str(words[j]) for j in order[:5])
                draw.text((x+12,542),top,font=small,fill="#172b40")
            else:
                draw.text((x+180,280),"해당 기사 없음",font=font,fill="#687786")
        filename=f"group_{gnum:02d}_comparison.png";pair.save(FIG/filename)
        pairs[(scope,brand,topic)]=pair
        inventory.append({**meta,"BoW 상위5":" / ".join(words[j] for j in rb[:5]),
                          "TF-IDF 상위5":" / ".join(words[j] for j in rt[:5]),
                          "상위10 공통키워드수":len(set(rb[:10])&set(rt[:10])),"워드클라우드":str((FIG/filename).relative_to(ROOT)),
                          "상태":"생성 완료" if n else "빈 그룹·키워드 생성 안 함"})
        print(title,n,flush=True)
    def montage(name,keys):
        board=Image.new("RGB",(1600,590*len(keys)),"white")
        for i,k in enumerate(keys):board.paste(pairs[k],(0,590*i))
        board.save(FIG/name)
    montage("브랜드별_BoW_TFIDF_워드클라우드.png",[("브랜드",b,"전체") for b in BRANDS])
    montage("주제별_BoW_TFIDF_워드클라우드.png",[("주제","전체",t) for t in TOPICS])
    for b in BRANDS:montage(f"{b}_주제별_BoW_TFIDF_워드클라우드.png",[("브랜드×주제",b,t) for t in TOPICS])
    save_csv("뉴스_키워드_BoW_TFIDF_상위20_비교.csv",comparison)
    save_csv("뉴스_키워드_BoW_TFIDF_전체점수.csv",long)
    save_csv("뉴스_키워드_그룹별요약.csv",inventory)
    method={"분석시각":datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),"입력행수":len(rows),"고유기사수":len(corpus),
            "분석텍스트":"제목 + 브랜드별 API 요약. 원문 본문 미포함", "토큰화":"Kiwi 일반명사·고유명사·외국어, 2자 이상, 숫자 단독 토큰 제외",
            "복합어사전":COMPOUNDS,
            "브랜드명제외":True,"IDF":"고유 URL 165개의 전체 코퍼스 공통 IDF; log((1+N)/(1+df))+1",
            "TF-IDF":"문서별 원시빈도×IDF 후 L2 정규화, 그룹별 평균. 모든 그룹에 동일 IDF 적용",
            "BoW":"그룹 내 토큰 출현횟수 합계", "그룹중복":"그룹 내 동일 URL은 가장 긴 요약 행 하나로 집계",
            "동일이슈":"다른 URL의 같은 사건 보도는 이전 기준대로 유지. 보도량 반복이 키워드에 영향",
            "그룹수":29,"빈그룹수":sum(not x["분석 고유기사수"] for x in inventory),
            "주의":"브랜드별 기사 기간이 다르고 제목·짧은 요약 분석이므로 시장 전체 경향이나 통계적 유의성을 뜻하지 않음",
            "한글폰트":FONT,"난수시드":42}
    (DATA/"뉴스_키워드분석_설정.json").write_text(json.dumps(method,ensure_ascii=False,indent=2),encoding="utf-8")
    for item in inventory[:9]:print(item)


if __name__=="__main__":main()
