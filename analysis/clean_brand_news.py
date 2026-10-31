"""검토표의 최종 권고를 반영하고 동일 URL 통합본과 제외 이력을 저장한다.

동일 사건의 다른 매체 기사는 삭제하지 않고 이슈 그룹만 유지한다.
원본 CSV와 API 응답은 변경하지 않는다.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/processed"


def main():
    source = FOLDER / "브랜드뉴스_관련성_전체검토.csv"
    with source.open(encoding="utf-8-sig", newline="") as f:
        reviewed = list(csv.DictReader(f))
    assert len(reviewed) == 200
    assert all(r["최종 권고"] in {"유지 권고", "제외 권고"} for r in reviewed)
    kept = [r for r in reviewed if r["최종 권고"] == "유지 권고"]
    excluded = [r for r in reviewed if r["최종 권고"] == "제외 권고"]
    assert len(kept) + len(excluded) == len(reviewed)
    assert {r["행ID"] for r in kept}.isdisjoint(r["행ID"] for r in excluded)

    def save(name, rows, fields=None):
        target = FOLDER / name
        with target.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]), extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        with target.open(encoding="utf-8-sig", newline="") as f:
            assert len(list(csv.DictReader(f))) == len(rows)

    save("브랜드별_최신뉴스_정제본.csv", kept,
         ["브랜드", "제목", "요약", "날짜", "원문 링크", "브랜드별 순위", "행ID",
          "분류", "최종 권고", "권고 근거", "확정 중복 그룹", "동일 이슈 후보 그룹", "중복 처리 권고", "검토 범위"])
    save("브랜드뉴스_제외내역.csv", excluded)

    grouped = defaultdict(list)
    for r in kept:
        grouped[r["원문 링크"]].append(r)
    unique = []
    for url, records in grouped.items():
        # 검색어별 API 요약은 다를 수 있어 모두 보존한다.
        representative = max(records, key=lambda r: len(r["요약"]))
        unique.append({
            "관련 브랜드": " / ".join(dict.fromkeys(r["브랜드"] for r in records)),
            "제목": representative["제목"], "요약": representative["요약"],
            "날짜": representative["날짜"], "원문 링크": url,
            "유지된 브랜드 행수": len(records),
            "원본 행ID": " / ".join(r["행ID"] for r in records),
            "브랜드별 요약": json.dumps({r["브랜드"]: r["요약"] for r in records}, ensure_ascii=False),
            "동일 이슈 후보 그룹": " / ".join(dict.fromkeys(r["동일 이슈 후보 그룹"] for r in records if r["동일 이슈 후보 그룹"])),
        })
    unique.sort(key=lambda r: r["날짜"], reverse=True)
    assert len({r["원문 링크"] for r in unique}) == len(unique)
    assert sum(r["유지된 브랜드 행수"] for r in unique) == len(kept)
    save("브랜드뉴스_정제본_동일URL통합.csv", unique)
    summary=[]
    for brand in dict.fromkeys(r["브랜드"] for r in reviewed):
        group=[r for r in reviewed if r["브랜드"]==brand]
        summary.append({"브랜드":brand,"수집":len(group),
                        "기존 제외 권고 반영":sum(r["판단"]=="제외 권고" for r in group),
                        "추가 제외 권고 반영":sum(r["판단"]=="판단 필요" and r["최종 권고"]=="제외 권고" for r in group),
                        "제외 합계":sum(r["최종 권고"]=="제외 권고" for r in group),
                        "유지":sum(r["최종 권고"]=="유지 권고" for r in group)})
    save("브랜드뉴스_정제결과_요약.csv", summary)
    assert Counter(r["판단"] for r in excluded) == {"제외 권고":12,"판단 필요":53}
    print(f"수집 {len(reviewed)}행 → 제외 {len(excluded)}행 / 유지 {len(kept)}행")
    print(f"동일 URL 통합: {len(unique)}개 기사 / 중복 연결 {len(kept)-len(unique)}행")
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()
