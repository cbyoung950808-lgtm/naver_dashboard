"""실행: .venv-nlp/bin/python analysis/analyze_musinsa_aliases.py"""
import csv
import os
import tempfile
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"naver-news-matplotlib"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parents[1]


def main():
    data=ROOT/"data/processed"
    with (data/"무신사스탠다드_무탠다드_월별비교.csv").open(encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
    names=["무신사 스탠다드","무탠다드"]
    months=sorted({r["월"] for r in rows})
    arr=np.array([[float(next(r["상대 검색지수"] for r in rows if r["검색어"]==k and r["월"]==m)) for m in months] for k in names])
    assert arr.shape==(2,24) and np.isclose(arr.max(),100,atol=.001)
    summary=[]
    for i,k in enumerate(names):
        v=arr[i]
        summary.append({"검색어":k,"24개월 평균 검색지수":v.mean(),"최근12개월 평균 검색지수":v[12:].mean(),
                        "최근12개월 전년대비_pct":(v[12:].sum()/v[:12].sum()-1)*100,
                        "2026년9월 검색지수":v[-1],"검색지수 최고월":months[int(np.argmax(v))],
                        "24개월 비교배율_무탠다드기준":v.sum()/arr[1].sum(),
                        "최근12개월 비교배율_무탠다드기준":v[12:].sum()/arr[1,12:].sum()})
    with (data/"무신사스탠다드_무탠다드_비교요약.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    font_manager.fontManager.addfont("/Library/Fonts/NanumBarunGothic.ttf")
    plt.rcParams.update({"font.family":"NanumBarunGothic","axes.unicode_minus":False,"font.size":11})
    fig,axes=plt.subplots(2,1,figsize=(13,8),layout="constrained")
    x=np.arange(24)
    for i,k in enumerate(names):
        axes[0].plot(x,arr[i],label=k,color=["#2563A6","#D77B21"][i],linewidth=2.5,marker="o",markersize=3)
        axes[1].plot(x,arr[i]/arr[i,:3].mean()*100,label=k,color=["#2563A6","#D77B21"][i],linewidth=2)
    axes[0].set_title("무신사 스탠다드 vs 무탠다드 · 같은 요청에서 비교",loc="left")
    axes[0].set_ylabel("상대 검색지수 (공통 최고점=100)");axes[0].set_ylim(bottom=0);axes[0].legend(frameon=False,ncol=2)
    axes[1].set_title("성장 속도 비교 · 각 검색어 첫 3개월 평균=100",loc="left")
    axes[1].set_ylabel("검색어별 성장지수");axes[1].axhline(100,color="#A0A8B0",linewidth=1,linestyle="--")
    for ax in axes:
        ticks=list(range(0,24,3))+[23]
        ax.set_xticks(ticks,[months[i] for i in ticks],rotation=25,ha="right")
        ax.set_xlim(0,23);ax.set_xlabel("월");ax.grid(axis="y",alpha=.2)
        ax.spines[["top","right"]].set_visible(False)
    fig.savefig(ROOT/"outputs/figures/무신사스탠다드_무탠다드_검색비교.png",dpi=150,bbox_inches="tight")
    plt.close(fig)
    for r in summary:print(r)


if __name__=="__main__":main()
