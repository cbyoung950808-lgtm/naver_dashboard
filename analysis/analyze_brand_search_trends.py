"""실행: .venv-nlp/bin/python analysis/analyze_brand_search_trends.py
공통 요청 내 지수 비교 및 연령 내 경쟁 비중. 연령 간 검색 규모·브랜드 고객 연령 구성은 추정하지 않는다.
"""
import csv
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"naver-news-matplotlib"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/processed"
FIG=ROOT/"outputs/figures/brand_search_trends"
SOURCE=DATA/"브랜드_검색트렌드_20261031_105155_884984.csv"
BRANDS=["유니클로","스파오","탑텐","무신사 스탠다드"]
AGES=["13~18세","19~24세","25~29세","30~39세","40~49세","50~59세","60세 이상"]
COLORS=["#2563a6","#d77b21","#258565","#8050a2"]


def main():
    FIG.mkdir(parents=True,exist_ok=True)
    font_manager.fontManager.addfont("/Library/Fonts/NanumBarunGothic.ttf")
    plt.rcParams.update({"font.family":"NanumBarunGothic","axes.unicode_minus":False,
                         "font.size":11,"axes.spines.top":False,"axes.spines.right":False,
                         "figure.facecolor":"white","axes.titleweight":"normal"})
    with SOURCE.open(encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
    months=sorted({r["월"] for r in rows});assert len(months)==24 and len(rows)==1248
    matrices={};status=[]
    for kind,label in dict.fromkeys((r["구분"],r["세그먼트"]) for r in rows):
        group=[r for r in rows if r["구분"]==kind and r["세그먼트"]==label]
        assert len(group)==96
        values={(r["브랜드"],r["월"]):float(r["검색지수"]) for r in group}
        assert len(values)==96
        matrix=np.array([[values[(b,m)] for m in months] for b in BRANDS])
        assert np.isfinite(matrix).all() and (matrix>=0).all() and (matrix<=100).all()
        assert np.isclose(matrix.max(),100,atol=.001)
        matrices[(kind,label)]=matrix
        status.append({"구분":kind,"세그먼트":label,"관측수":96,"누락월":0,"명시적 0 관측수":int((matrix==0).sum())})
    # 저장된 원본 실제 값 한 개와 가공 CSV 대조.
    raw=json.loads((ROOT/rows[0]["원본 파일"]).read_text())
    response=json.loads(raw["response_text"])
    assert float(rows[0]["검색지수"])==float(response["results"][0]["data"][0]["ratio"])
    def save(name,data):
        with (DATA/name).open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    def shares(matrix):
        totals=matrix.sum(axis=0)
        return np.divide(matrix,totals,out=np.full_like(matrix,np.nan),where=totals>0)*100
    def change(new,old):return float((new/old-1)*100) if old>0 else None
    def ratio_share(matrix,sl):
        sums=matrix[:,sl].sum(axis=1)
        return sums/sums.sum()*100 if sums.sum()>0 else np.full(4,np.nan)
    transformed=[];stats=[]
    for (kind,label),matrix in matrices.items():
        share=shares(matrix)
        assert np.allclose(share.sum(axis=0),100)
        prior=ratio_share(matrix,slice(0,12));recent=ratio_share(matrix,slice(12,24))
        for j,b in enumerate(BRANDS):
            values=matrix[j]
            firstbase=values[:3].mean()
            for t,m in enumerate(months):
                transformed.append({"구분":kind,"세그먼트":label,"브랜드":b,"월":m,
                                    "API 상대 검색지수":values[t],"네브랜드 내 월별 검색지수 비중_pct":share[j,t],
                                    "첫3개월평균100 성장지수":values[t]/firstbase*100 if firstbase else ""})
            stats.append({"구분":kind,"세그먼트":label,"브랜드":b,
                          "최근12개월 평균지수":float(values[12:].mean()),"최근12개월 전년동기대비_pct":change(values[12:].sum(),values[:12].sum()),
                          "최근3개월 전년동기대비_pct":change(values[-3:].sum(),values[9:12].sum()),
                          "최신월":months[-1],"최신월 지수":float(values[-1]),"최신월 전년동월대비_pct":change(values[-1],values[11]),
                          "이전12개월 네브랜드 내 비중_pct":prior[j],"최근12개월 네브랜드 내 비중_pct":recent[j],
                          "네브랜드 내 비중변화_pp":recent[j]-prior[j],"24개월 최고월":months[int(np.argmax(values))],
                          "24개월 최고지수":float(values.max())})
    save("브랜드_검색트렌드_분석용.csv",transformed)
    save("브랜드_검색트렌드_경쟁지표.csv",stats)
    save("브랜드_검색트렌드_관측검증.csv",status)
    overall=matrices[("전체","전체")];x=np.arange(24);ticks=list(range(0,24,3))+[23]
    def time_axis(ax):
        ax.set_xticks(ticks,[months[i] for i in ticks],rotation=30,ha="right")
        ax.set_xlim(0,23);ax.set_xlabel("월");ax.grid(axis="y",alpha=.2)
    def savefig(fig,name):
        fig.savefig(FIG/name,dpi=160,bbox_inches="tight");plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(14,10),layout="constrained")
    for j,b in enumerate(BRANDS):
        axes[0].plot(x,overall[j],label=b,color=COLORS[j],linewidth=2,marker="o",markersize=3)
        axes[1].plot(x,shares(overall)[j],label=b,color=COLORS[j],linewidth=2)
    axes[0].set_title("월별 브랜드 검색 관심도 · 동일 요청에서 네 브랜드 비교",loc="left",pad=14)
    axes[0].set_ylabel("상대 검색지수 (공통 최고점=100)");axes[0].set_ylim(bottom=0);axes[0].legend(ncol=4,frameon=False)
    axes[1].set_title("선택한 네 브랜드 내 검색지수 비중 · 시장점유율 아님",loc="left",pad=14)
    axes[1].set_ylabel("검색지수 비중 (%)");axes[1].set_ylim(0,100)
    for ax in axes:time_axis(ax)
    savefig(fig,"01_월별_관심도와_경쟁비중.png")
    fig,ax=plt.subplots(figsize=(14,5),layout="constrained")
    for j,b in enumerate(BRANDS):ax.plot(x,overall[j]/overall[j,:3].mean()*100,label=b,color=COLORS[j],linewidth=2)
    ax.axhline(100,color="#77818d",linewidth=1,linestyle="--")
    ax.set_title("브랜드별 관심도 성장 · 각 브랜드 첫 3개월 평균=100",loc="left",pad=14)
    ax.set_ylabel("브랜드별 성장지수");time_axis(ax);ax.legend(ncol=4,frameon=False)
    savefig(fig,"02_브랜드별_기준100_성장추이.png")
    age_share=np.array([ratio_share(matrices[("연령",a)],slice(12,24)) for a in AGES])
    age_growth=np.array([[s["최근12개월 전년동기대비_pct"] for s in stats if s["구분"]=="연령" and s["세그먼트"]==a] for a in AGES],dtype=float)
    fig,axes=plt.subplots(1,2,figsize=(15,6),layout="constrained")
    for ax,arr,title,cmap in [(axes[0],age_share,"연령대 안에서의 경쟁 비중 · 최근 12개월", "Blues"),
                               (axes[1],age_growth,"연령대별 관심도 변화 · 최근 12개월 전년 대비", "RdBu")]:
        if ax is axes[0]:im=ax.imshow(arr,cmap=cmap,vmin=0,vmax=100,aspect="auto")
        else:
            bound=max(10,float(np.nanmax(np.abs(arr))))
            im=ax.imshow(arr,cmap=cmap,vmin=-bound,vmax=bound,aspect="auto")
        ax.set_xticks(range(4),["유니클로","스파오","탑텐","무신사\n스탠다드"])
        ax.set_yticks(range(7),AGES);ax.set_title(title,loc="left",pad=14)
        for i in range(7):
            for j in range(4):
                val=arr[i,j];contrast="white" if (val>55 if ax is axes[0] else abs(val)>bound*.5) else "#172b40"
                ax.text(j,i,f"{val:.1f}%",ha="center",va="center",color=contrast,fontsize=12)
        fig.colorbar(im,ax=ax,shrink=.8,label="검색지수 비중 (%)" if ax is axes[0] else "전년 대비 변화율 (%)")
    fig.supxlabel("비중은 각 연령대의 네 브랜드 검색지수 합 기준 · 연령대별 검색 인구 크기 또는 브랜드 고객 연령 구성비가 아님",fontsize=10)
    savefig(fig,"03_연령대별_경쟁비중과_성장률.png")
    fig,axes=plt.subplots(4,2,figsize=(15,16),layout="constrained",sharex=False,sharey=True)
    for ax,a in zip(axes.flat,AGES):
        arr=shares(matrices[("연령",a)])
        for j,b in enumerate(BRANDS):ax.plot(x,arr[j],label=b,color=COLORS[j],linewidth=1.8)
        ax.set_title(a,loc="left");ax.set_ylim(0,100);time_axis(ax);ax.set_ylabel("연령대 내 경쟁 비중 (%)")
    axes.flat[-1].axis("off")
    handles,labels=axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",ncol=4,frameon=False,bbox_to_anchor=(.5,1.035))
    fig.suptitle("연령대별 월별 경쟁 구도 · 각 월·연령대 안에서 네 브랜드 합=100%",y=1.06,fontsize=16)
    savefig(fig,"04_연령대별_월별_경쟁추이.png")
    segments=[("성별","남성"),("성별","여성"),("기기","PC"),("기기","모바일")]
    fig,axes=plt.subplots(1,4,figsize=(16,5),layout="constrained",sharey=True)
    for ax,(kind,label) in zip(axes,segments):
        vals=ratio_share(matrices[(kind,label)],slice(12,24))
        ax.barh(range(4),vals,color=COLORS,height=.65)
        for j,val in enumerate(vals):ax.text(val+1,j,f"{val:.1f}%",va="center")
        ax.set_yticks(range(4),BRANDS);ax.set_xlim(0,100)
        ax.set_xlabel("네 브랜드 내 검색지수 비중 (%)");ax.set_title(label,loc="left")
        ax.grid(axis="x",alpha=.15)
    axes[0].invert_yaxis()
    fig.suptitle("성별·기기별 경쟁 구도 · 최근 12개월",fontsize=16)
    savefig(fig,"05_성별_기기별_경쟁비중.png")
    narrow=matrices[("보완조회","탑텐 보완어")]
    broad_ratio=np.divide(overall[2],overall[0],out=np.full(24,np.nan),where=overall[0]>0)
    narrow_ratio=np.divide(narrow[2],narrow[0],out=np.full(24,np.nan),where=narrow[0]>0)
    fig,ax=plt.subplots(figsize=(14,5),layout="constrained")
    ax.plot(x,broad_ratio,color=COLORS[2],label="탑텐 단일어 / 유니클로",linewidth=2)
    ax.plot(x,narrow_ratio,color="#6b7280",label="탑텐몰·TOPTEN10 / 유니클로",linewidth=2,linestyle="--")
    ax.set_title("탑텐 검색어 범위에 따른 민감도 · 같은 요청 안의 유니클로를 기준으로 비교",loc="left",pad=14)
    ax.set_ylabel("유니클로 대비 검색지수 배율");ax.set_ylim(bottom=0);time_axis(ax);ax.legend(frameon=False)
    savefig(fig,"06_탑텐_검색어_민감도.png")
    sensitivity=[{"월":m,"탑텐 단일어_유니클로대비 배율":broad_ratio[i],"탑텐 보완어_유니클로대비 배율":narrow_ratio[i]} for i,m in enumerate(months)]
    save("브랜드_검색트렌드_탑텐_검색어민감도.csv",sensitivity)
    meta={"기간":[months[0],months[-1]],"최근12개월":[months[12],months[-1]],"API공식문서":"https://api.ncloud-docs.com/docs/naver-api-hub-search-trend",
          "비중정의":"같은 요청에서 선택한 네 브랜드 지수 합 대비 비율. 전체 검색시장 점유율·고객 구성비·구매율이 아님",
          "정규화":"요청별 네 브랜드·24개월 공통 최대=100. 요청이 다른 연령·성별·기기의 원지수 크기는 직접 비교하지 않음",
          "성장률":"최근12개월 지수 합/직전12개월 지수 합-1; 동일 요청 안에서 계산",
          "검색어묶음":{r["브랜드"]:r["검색어 묶음"] for r in rows if r["구분"]=="전체"},
          "탑텐주의":"단일어는 순위·방송명 동음이의어 포함 가능. 보완어는 범위가 좁아 누락 가능. 두 결과로 순수 브랜드 검색량을 확정할 수 없음",
          "연령주의":"연령별 패널은 13세 이상만 제시. 전체는 연령 필터 없음. 브랜드 고객의 연령 구성비나 연령별 검색 규모 비교는 불가능",
          "기타주의":"상대 검색 추이로 인과관계·구매·매출을 추정하지 않음. 월별 비중은 지정한 검색어 묶음에 의존"}
    (DATA/"브랜드_검색트렌드_분석기준.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    for s in stats:
        if s["구분"]=="전체":print(s)
    print("연령 최근12개월 비중",np.round(age_share,1).tolist())
    print("연령 최근12개월 전년대비",np.round(age_growth,1).tolist())
    print("탑텐_유니클로 대비 평균배율",float(np.mean(broad_ratio)),float(np.mean(narrow_ratio)))


if __name__=="__main__":main()
