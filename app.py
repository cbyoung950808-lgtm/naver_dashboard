"""실행: python -m streamlit run app.py
Python 3.12 / pip install -r requirements.txt
저장된 분석 결과를 조회하는 대시보드. API 키·로컬 폰트·분석 패키지가 필요하지 않다.
"""
from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/processed"
BRANDS = ["유니클로", "스파오", "탑텐", "무신사 스탠다드"]
TOPICS = ["제품 출시", "협업", "할인 혹은 행사", "실적 또는 사업", "기타"]
COLORS = dict(zip(BRANDS, ["#B42332", "#B65C16", "#176B55", "#343D4B"]))
TOPIC_COLORS = dict(zip(TOPICS, ["#528AC0", "#8A70AF", "#E3A254", "#4C9D8A", "#9DAAB8"]))
SHARE = "네브랜드 내 월별 검색지수 비중_pct"
RECENT_SHARE = "최근12개월 네브랜드 내 비중_pct"
YOY = "최근12개월 전년동기대비_pct"
st.set_page_config(page_title="K-SPA | 경쟁사 인사이트", page_icon="◼", layout="wide")
st.markdown("""<style>
.block-container {padding-top:2rem; padding-bottom:3rem; max-width:1440px;}
[data-testid="stMetric"] {background:white; padding:1.05rem 1.2rem; border-radius:6px; border:1px solid #E3EAF1;}
[data-testid="stMetricValue"] {font-size:1.85rem;}
h1 {letter-spacing:-1.4px;} h2,h3 {letter-spacing:-.5px;}
[data-testid="stSidebar"] {border-right:1px solid #E3EAF1;}
.report-context {border-top:3px solid #202C3B; border-bottom:1px solid #D5DBE3;
 padding:14px 0; margin-bottom:24px; color:#344054; font-size:.9rem; line-height:1.8;}
.report-label {font-size:.75rem; letter-spacing:2px; font-weight:700; color:#667085;}
@media print {
 [data-testid="stSidebar"], [data-testid="stToolbar"], [data-testid="stDownloadButton"] {display:none!important;}
 .block-container {max-width:100%; padding:0!important;}
 [data-testid="stMetric"], [data-testid="stPlotlyChart"] {break-inside:avoid;}
}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def csv(name, modified):
    return pd.read_csv(DATA / name, encoding="utf-8-sig").fillna("")


def load(name):
    path = DATA / name
    if not path.exists():
        st.error(f"필요한 분석 데이터가 없습니다: {name}")
        st.stop()
    return csv(name, path.stat().st_mtime_ns).copy()


def download(frame, name, label="CSV 다운로드", key=None):
    st.download_button(label, frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name=name, mime="text/csv", key=key)


def polish(fig, height=420, ytitle=None):
    fig.update_layout(height=height, margin=dict(l=12, r=20, t=25, b=15),
                      font=dict(family="Arial, Noto Sans KR, sans-serif", color="#243247"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(title_text="", orientation="h", y=1.12, x=0),
                      hovermode="x unified")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E3EAF1", title_text=ytitle)
    return fig


def line(frame, value, ytitle, height=400):
    fig = px.line(frame, x="월", y=value, color="브랜드", color_discrete_map=COLORS,
                  category_orders={"브랜드": BRANDS}, markers=True, line_dash="브랜드", symbol="브랜드")
    fig.update_traces(line_width=2.4, marker_size=5,
                      hovertemplate="%{x}<br>%{y:.2f}<extra>%{fullData.name}</extra>")
    return polish(fig, height, ytitle)


def metrics(frame):
    for col, (_, r) in zip(st.columns(len(frame)), frame.iterrows()):
        with col:
            st.metric(r["브랜드"], f"{r[RECENT_SHARE]:.1f}%", f"{r[YOY]:+.1f}% 전년 대비", delta_color="off")
    st.caption("최근 12개월 네 브랜드 내 검색지수 비중 · 증감은 같은 브랜드 검색지수의 전년 동기 대비")


def overview(news, trend, stats, selected):
    st.title("브랜드 경쟁 현황")
    st.caption("브랜드별 기사 50건과 24개월 검색 추이로 살펴보는 K-SPA 경쟁 현황")
    chosen = news[news["브랜드"].isin(selected)]
    a,b,c,d = st.columns(4)
    a.metric("분석 뉴스", f"{len(chosen):,}건")
    b.metric("중복 원문 통합", f"{chosen['원문 링크'].nunique():,}건")
    c.metric("검색 추이", "24개월")
    d.metric("선택 브랜드", f"{len(selected)}개")
    st.subheader("핵심 보고 요약")
    report = stats[(stats["구분"]=="전체") & stats["브랜드"].isin(selected)]
    leader = report.loc[report[RECENT_SHARE].idxmax()]
    growth = report.loc[report[YOY].idxmax()]
    dominant = chosen["대표 주제"].value_counts()
    with st.container(border=True):
        st.markdown(f"**관심도 선두 · {leader['브랜드']}** — 선택 브랜드 중 최근 12개월 검색지수 비중 {leader[RECENT_SHARE]:.1f}%")
        st.markdown(f"**전년 대비 변화 최대 · {growth['브랜드']}** — 같은 브랜드의 전년 동기 대비 {growth[YOY]:+.1f}%")
        top = dominant.max()
        topics = ' · '.join(dominant[dominant==top].index)
        st.markdown(f"**뉴스의 주요 의제 · {topics}** — 주제별 집계 최다 {top}건. 브랜드별 50건을 맞춘 표본이므로 보도량 점유율 해석은 제한됩니다.")
    export = report[["브랜드", RECENT_SHARE, YOY, "네브랜드 내 비중변화_pp"]].rename(columns={RECENT_SHARE:"최근12개월 검색지수 비중_pct",YOY:"전년동기 대비_pct"})
    download(export, "브랜드_보고요약.csv", "보고용 핵심 지표 CSV", key="report_download")
    st.subheader("검색 관심도와 성장")
    overall = stats[(stats["구분"]=="전체") & stats["브랜드"].isin(selected)]
    metrics(overall)
    tf = trend[(trend["구분"]=="전체") & trend["브랜드"].isin(selected)]
    st.plotly_chart(line(tf, "API 상대 검색지수", "상대 검색지수 · 공통 최고점=100"), width="stretch", key="overview_trend")
    st.caption("검색 기간 2024.10~2026.09 · 성장 비교 기간 2025.10~2026.09 / 2024.10~2025.09")
    left,right = st.columns([1.1,1])
    with left:
        st.subheader("뉴스의 주제 구성")
        counts = chosen.groupby(["브랜드","대표 주제"]).size().reset_index(name="기사 수")
        fig = px.bar(counts, x="브랜드", y="기사 수", color="대표 주제", color_discrete_map=TOPIC_COLORS,
                     category_orders={"브랜드":BRANDS,"대표 주제":TOPICS}, text="기사 수")
        fig.update_traces(textposition="inside")
        st.plotly_chart(polish(fig, 410, "기사 수"), width="stretch", key="overview_topics")
    with right:
        st.subheader("브랜드별 관찰")
        insight = load("브랜드_검색트렌드_경쟁분석_인사이트.csv")
        for _,r in insight[insight["브랜드"].isin(selected)].iterrows():
            with st.container(border=True):
                st.markdown(f"**{r['브랜드']}**")
                st.write(r["경쟁 해석"])
    st.info("검색지수는 관심도의 상대 지표입니다. 검색 비중은 지정한 네 브랜드 안에서 계산했으며, 시장점유율·구매자 비율이 아닙니다.")


def news_page(news, selected):
    st.title("뉴스 탐색")
    st.caption("관련성 검토를 통과한 200건 · 기사마다 주제·채택 근거·원문 링크 확인")
    frame = news[news["브랜드"].isin(selected)].copy()
    c1,c2 = st.columns([1,1.3])
    with c1: topics = st.multiselect("주제", TOPICS, default=TOPICS, key="news_topics")
    with c2: query = st.text_input("제목·요약 검색", placeholder="예: 경량패딩, 캐릭터, 텐텐데이")
    dates = pd.to_datetime(frame["날짜"], utc=True).dt.tz_convert("Asia/Seoul").dt.tz_localize(None)
    frame["발행일시"] = dates
    date_range = st.date_input("발행일 범위", value=(dates.min().date(),dates.max().date()),
                               min_value=dates.min().date(), max_value=dates.max().date())
    frame = frame[frame["대표 주제"].isin(topics)]
    if query:
        frame = frame[(frame["제목"]+" "+frame["요약"]).str.contains(query, case=False, regex=False)]
    if len(date_range)==2:
        frame = frame[(frame["발행일시"].dt.date>=date_range[0]) & (frame["발행일시"].dt.date<=date_range[1])]
    frame = frame.sort_values("발행일시", ascending=False)
    if frame.empty:
        st.info("조건에 맞는 기사가 없습니다. 주제·검색어·날짜 범위를 조정해 주세요.")
    st.write(f"**{len(frame)}건** · 고유 원문 {frame['원문 링크'].nunique()}건")
    columns=["브랜드","대표 주제","제목","요약","발행일시","원문 링크"]
    st.dataframe(frame[columns], hide_index=True, width="stretch", height=510,
                 column_config={"원문 링크":st.column_config.LinkColumn("원문",display_text="기사 보기"),
                                "발행일시":st.column_config.DatetimeColumn("날짜",format="YYYY-MM-DD HH:mm"),
                                "제목":st.column_config.TextColumn(width="large"),
                                "요약":st.column_config.TextColumn(width="large")})
    download(frame.drop(columns="발행일시"), "브랜드뉴스_필터결과.csv", key="news_download")
    if not frame.empty:
        with st.expander("개별 기사의 분류·채택 근거"):
            options = frame["분류ID"].tolist()
            lookup = frame.set_index("분류ID")
            item = st.selectbox("기사 선택", options,
                                format_func=lambda k:f"[{lookup.loc[k,'브랜드']}] {lookup.loc[k,'제목']}")
            r=lookup.loc[item]
            st.write(r["요약"])
            st.markdown(f"**주제:** {r['대표 주제']} / {r['세부 주제']}")
            st.write("분류 근거: "+r["분류 근거"])
            st.write("채택 근거: "+r["채택 근거"])
            st.caption("검토 범위: "+r["검토 범위"])
            st.link_button("원문 기사 열기",r["원문 링크"])


def keywords_page(selected):
    st.title("BoW · TF-IDF 키워드 비교")
    st.caption("제목과 API 요약의 명사 분석 · 브랜드명·일반 기사 표현 제외 · 그룹 내 동일 원문 중복 제거")
    scope = st.radio("비교 범위", ["브랜드","주제","브랜드×주제"], horizontal=True)
    c1,c2=st.columns(2)
    brand = c1.selectbox("브랜드",selected,key="keyword_brand") if scope!="주제" else "전체"
    topic = c2.selectbox("주제",TOPICS,key="keyword_topic") if scope!="브랜드" else "전체"
    inventory=load("뉴스_키워드_그룹별요약.csv")
    meta=inventory[(inventory["구분"]==scope)&(inventory["브랜드"]==brand)&(inventory["주제"]==topic)].iloc[0]
    st.caption(f"이 그룹의 분석 고유 기사: {meta['분석 고유기사수']}건")
    if int(meta["분석 고유기사수"])==0:
        st.info("이 조합에 분류된 기사가 없어 키워드를 생성하지 않았습니다.")
        return
    scores=load("뉴스_키워드_BoW_TFIDF_전체점수.csv")
    group=scores[(scores["구분"]==scope)&(scores["브랜드"]==brand)&(scores["주제"]==topic)]
    for col,method in zip(st.columns(2),["BoW","TF-IDF"]):
        with col:
            st.subheader(method)
            subset=group[group["방식"]==method].nsmallest(15,"순위").sort_values("점수")
            fig=px.bar(subset,x="점수",y="키워드",orientation="h",text="점수")
            fig.update_traces(marker_color="#2563A6" if method=="BoW" else "#258565",
                              texttemplate="%{x:.0f}" if method=="BoW" else "%{x:.3f}",textposition="outside",cliponaxis=False)
            st.plotly_chart(polish(fig,490,""),width="stretch",key=f"keywords_{method}")
            st.caption("단어 출현 횟수 합계" if method=="BoW" else "문서별 중요도의 평균 · 전체 고유 기사 165개 기준 IDF")
    with st.expander("워드클라우드로 보기", expanded=False):
        st.image(str(ROOT/meta["워드클라우드"]),width="stretch")
        st.caption("왼쪽 BoW · 오른쪽 TF-IDF · 글자 크기는 각 방식의 점수에 비례")
    a=group[group["방식"]=="BoW"][["순위","키워드","점수"]].head(20).rename(columns={"키워드":"BoW 키워드","점수":"출현 횟수"})
    b=group[group["방식"]=="TF-IDF"][["순위","키워드","점수"]].head(20).rename(columns={"키워드":"TF-IDF 키워드","점수":"TF-IDF 점수"})
    st.dataframe(a.merge(b,on="순위",how="outer"),hide_index=True,width="stretch")
    download(group,"키워드_비교결과.csv",key="keyword_download")
    st.caption("서로 다른 원문의 동일 사건 보도는 포함됩니다. 반복 보도량이 키워드 순위에 영향을 줄 수 있습니다.")


def search_page(trend,stats,selected):
    st.title("검색 관심도 · 경쟁 추이")
    st.caption("2024.10~2026.09 · 24개 완료 월 · 월별·연령별·성별·기기별 비교")
    st.info("요청이 다른 연령·성별·기기의 원지수 크기는 직접 비교할 수 없습니다. 비중은 각 집단 안에서 네 브랜드의 검색지수 합을 기준으로 계산합니다.")
    dimension=st.radio("분석 대상",["전체","연령","성별","기기"],horizontal=True)
    segments=trend[trend["구분"]==dimension]["세그먼트"].drop_duplicates().tolist()
    segment=st.selectbox("집단 선택",segments,key=f"segment_{dimension}") if dimension!="전체" else "전체"
    filtered=trend[(trend["구분"]==dimension)&(trend["세그먼트"]==segment)&trend["브랜드"].isin(selected)]
    stat=stats[(stats["구분"]==dimension)&(stats["세그먼트"]==segment)&stats["브랜드"].isin(selected)]
    metrics(stat)
    modes={"공통 검색지수":"API 상대 검색지수","네 브랜드 내 비중":SHARE,"브랜드별 성장":"첫3개월평균100 성장지수"}
    mode=st.radio("그래프 기준",list(modes),horizontal=True)
    ytitle={"공통 검색지수":"같은 요청의 최고점=100","네 브랜드 내 비중":"검색지수 비중 (%)","브랜드별 성장":"각 브랜드 첫 3개월 평균=100"}[mode]
    st.plotly_chart(line(filtered,modes[mode],ytitle,470),width="stretch",key="search_line")
    st.caption("브랜드 선택을 줄여도 비중의 분모는 원래 네 브랜드를 유지합니다. 그래프 위에서 확대하거나 범례를 눌러 브랜드를 숨길 수 있습니다.")
    if dimension=="연령":
        st.subheader("연령대별 경쟁 비중과 성장률")
        ag=stats[(stats["구분"]=="연령")&stats["브랜드"].isin(selected)]
        ages=segments
        for col,field,title in zip(st.columns(2),[RECENT_SHARE,YOY],["최근 12개월 경쟁 비중 (%)","최근 12개월 전년 대비 (%)"]):
            with col:
                arr=ag.pivot(index="세그먼트",columns="브랜드",values=field).reindex(index=ages,columns=selected)
                fig=px.imshow(arr,text_auto=".1f",aspect="auto",color_continuous_scale="Blues" if field==RECENT_SHARE else "RdBu",
                              zmin=0 if field==RECENT_SHARE else None,zmax=100 if field==RECENT_SHARE else None,
                              color_continuous_midpoint=0 if field==YOY else None)
                fig.update_layout(height=400,title=title,margin=dict(t=55,l=10,r=10,b=10),coloraxis_showscale=False)
                st.plotly_chart(fig,width="stretch",key=f"age_{field}")
        st.caption("연령대별 검색 인구 크기나 브랜드 고객의 연령 구성비가 아닙니다. 전체 조회는 연령 제한이 없고 연령 패널은 13세 이상입니다.")
    if dimension in ["성별","기기"]:
        compare=stats[(stats["구분"]==dimension)&stats["브랜드"].isin(selected)]
        fig=px.bar(compare,x="세그먼트",y=RECENT_SHARE,color="브랜드",barmode="group",color_discrete_map=COLORS,text_auto=".1f")
        st.plotly_chart(polish(fig,370,"네 브랜드 내 검색지수 비중 (%)"),width="stretch",key="segment_bars")
    with st.expander("검색어 정의와 탑텐 보완 조회"):
        meta=json.loads((DATA/"브랜드_검색트렌드_분석기준.json").read_text())
        st.dataframe(pd.DataFrame([{"브랜드":b,"검색어 묶음":k} for b,k in meta["검색어묶음"].items()]),hide_index=True,width="stretch")
        st.write(meta["탑텐주의"])
        sensitivity=load("브랜드_검색트렌드_탑텐_검색어민감도.csv")
        melted=sensitivity.melt(id_vars="월",var_name="검색어 기준",value_name="유니클로 대비 배율")
        fig=px.line(melted,x="월",y="유니클로 대비 배율",color="검색어 기준")
        st.plotly_chart(polish(fig,330,"유니클로 대비 배율"),width="stretch",key="topten_sensitivity")
    view=stat[["브랜드",RECENT_SHARE,YOY,"최근3개월 전년동기대비_pct","네브랜드 내 비중변화_pp","24개월 최고월"]].rename(columns={
        RECENT_SHARE:"최근 12개월 비중 (%)",YOY:"최근 12개월 전년 대비 (%)","최근3개월 전년동기대비_pct":"최근 3개월 전년 대비 (%)",
        "네브랜드 내 비중변화_pp":"비중 변화 (%p)"})
    st.dataframe(view,hide_index=True,width="stretch")
    download(filtered,"검색추이_선택결과.csv",key="trend_download")


def quality_page(news):
    st.title("수집·정제 내역")
    st.caption("이 페이지는 브랜드 선택과 관계없이 전체 데이터의 처리 이력을 보여줍니다.")
    st.markdown("**최초 200건 → 제외 65건 → 유지 135건 → 추가 채택 65건 → 최종 200건**")
    summary=load("브랜드뉴스_50건확보_요약.csv")
    st.dataframe(summary,hide_index=True,width="stretch")
    a,b,c=st.columns(3)
    a.metric("최종 기사·브랜드 연결",f"{len(news)}건")
    b.metric("고유 원문",f"{news['원문 링크'].nunique()}건")
    c.metric("추가 후보 중 검토",f"{summary['추가 검토'].sum()}건")
    st.caption("추가 후보 400건 중 94건을 검토해 65건을 채택했습니다. 나머지 306건은 목표 수량 충족 후 미검토 후보로 남겼습니다.")
    tab1,tab2,tab3=st.tabs(["기존 제외 65건","추가 후보 검토","주제 분류 기준"])
    with tab1:
        rejected=load("브랜드뉴스_제외내역.csv")
        st.dataframe(rejected[["브랜드","제목","분류","권고 근거","원문 링크"]],hide_index=True,width="stretch",
                     column_config={"원문 링크":st.column_config.LinkColumn(display_text="원문")})
        download(rejected,"기존_제외내역.csv",key="excluded_download")
    with tab2:
        audit=load("브랜드뉴스_추가수집_검토내역.csv")
        state=st.selectbox("처리 결과",["전체"]+audit["처리"].drop_duplicates().tolist())
        if state!="전체":audit=audit[audit["처리"]==state]
        st.dataframe(audit[["브랜드","검색 순위","처리","제목","판단 근거"]],hide_index=True,width="stretch")
        download(audit,"추가수집_검토내역.csv",key="audit_download")
    with tab3:st.dataframe(load("브랜드뉴스_주제분류_기준.csv"),hide_index=True,width="stretch")
    with st.expander("UI·UX 평가 기준과 개선 내역"):
        st.caption("내부 기준에 따른 구현 점검입니다. 사용자 사용성 평가 점수나 공식 브랜드 가이드 준수 인증은 아닙니다.")
        evaluation=load("UI_UX_평가항목.csv")
        st.dataframe(evaluation, hide_index=True, width="stretch")
        download(evaluation,"UI_UX_평가항목.csv","UI·UX 평가표 다운로드",key="evaluation_download")
    st.subheader("분석 파일 다운로드")
    for name,label in [("뉴스_BoW_TFIDF_분석결과.zip","키워드 분석 · 워드클라우드 전체"),
                       ("브랜드_검색추이_경쟁사분석.zip","검색 추이 분석 · 그래프 전체")]:
        path=DATA/name
        if path.exists():st.download_button(label,path.read_bytes(),file_name=name,mime="application/zip")
    download(news,"브랜드별_뉴스_주제분류_200건.csv","최종 뉴스 · 주제 분류 데이터",key="all_news_download")
    st.caption("뉴스는 제목·API 요약을 기준으로 검토했습니다. 동일 URL은 브랜드 안에서 한 번만 집계하며, 다른 매체의 같은 사건 보도는 유지합니다.")


def main():
    news=load("브랜드별_뉴스_주제분류_200건.csv")
    trend=load("브랜드_검색트렌드_분석용.csv")
    stats=load("브랜드_검색트렌드_경쟁지표.csv")
    with st.sidebar:
        st.markdown("### K-SPA INSIGHTS\n브랜드 경쟁 분석")
        st.caption("NAVER API HUB · 2026.10.31 분석")
        page=st.radio("탐색",["요약","뉴스 탐색","키워드 비교","검색 추이","수집·정제 내역"],label_visibility="collapsed")
        st.divider()
        report_mode=st.toggle("보고 모드", help="필터와 분석 기준을 상단에 표시하고 보고용 화면 여백을 적용합니다.")
        selected=st.multiselect("비교 브랜드",BRANDS,default=BRANDS)
        st.caption("뉴스 200건 · 고유 기사 165건\n\n검색 추이 2024.10—2026.09")
        st.divider()
        st.caption("저장된 분석 결과를 표시합니다. 최신 데이터가 자동으로 수집되지는 않습니다.")
    if report_mode:
        st.markdown('<div class="report-label">COMPETITIVE INTELLIGENCE / NAVER DATA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-context"><strong>비교 범위</strong>　{" · ".join(selected) or "선택 없음"}<br><strong>분석 기준</strong>　검색 2024.10–2026.09 · 데이터 정리 2026.10.31 · 저장 데이터 기준<br><strong>보고 화면</strong>　{page} · 세부 조건은 아래 필터에 표시</div>', unsafe_allow_html=True)
    if not selected:
        st.info("왼쪽에서 비교할 브랜드를 하나 이상 선택해 주세요.")
        return
    if page=="요약":overview(news,trend,stats,selected)
    elif page=="뉴스 탐색":news_page(news,selected)
    elif page=="키워드 비교":keywords_page(selected)
    elif page=="검색 추이":search_page(trend,stats,selected)
    else:quality_page(news)


if __name__=="__main__":main()
