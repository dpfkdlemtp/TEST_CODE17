import pandas as pd
import os

# === 기존 추출 함수 import ===
from Extract_WPPSI import extract_wppsi_scores_from_page3, extract_wppsi_subtest_scores
from Extract_WISC import extract_wisc_scores_from_page3, extract_wisc_subtest_scores
from Extract_WAIS import extract_combination_scores_from_page4, extract_subtest_scores_from_page3

# ✅ 추가: 코드 → 도메인/한글명칭 매핑
subtest_name_map = [
    ("언어이해", "공통성"),
    ("언어이해", "어휘"),
    ("언어이해", "상식"),
    ("지각추론", "토막짜기"),
    ("지각추론", "행렬추론"),
    ("지각추론", "퍼즐"),
    ("작업기억", "숫자"),
    ("작업기억", "산수"),
    ("처리속도", "동형찾기"),
    ("처리속도", "기호쓰기")
]


def extract_all_scores(pdf_path, original_name=None):
    filename = (original_name or os.path.basename(pdf_path)).upper()
    result = {"지표점수": {}, "소검사점수": {}}

    if "WPPSI" in filename:
        result["지표점수"] = extract_wppsi_scores_from_page3(pdf_path)
        result["소검사점수"] = extract_wppsi_subtest_scores(pdf_path)
    elif "WISC" in filename:
        result["지표점수"] = extract_wisc_scores_from_page3(pdf_path)
        result["소검사점수"] = extract_wisc_subtest_scores(pdf_path)
    elif "WAIS" in filename:
        result["지표점수"] = extract_combination_scores_from_page4(pdf_path)
        result["소검사점수"] = extract_subtest_scores_from_page3(pdf_path, subtest_name_map)

    return result, filename



def format_index_scores_excel(scores, is_wais=False):
    if is_wais:
        ordered_keys = ["전체검사", "언어이해", "지각추론", "작업기억", "처리속도"]
        data = {"지표점수": [], "백분위": [], "진단분류": [], "신뢰구간": []}

        for key in ordered_keys:
            if key in scores:
                data["지표점수"].append(scores[key].get("조합점수", ""))
                data["백분위"].append(scores[key].get("백분위", ""))
                data["신뢰구간"].append(scores[key].get("신뢰구간", ""))
                data["진단분류"].append("")
            else:
                data["지표점수"].append("")
                data["백분위"].append("")
                data["진단분류"].append("")
                data["신뢰구간"].append("")
    else:
        ordered_keys = ["전체IQ", "언어이해", "시공간", "유동추론", "작업기억", "처리속도"]
        data = {"지표점수": [], "백분위": [], "진단분류": [], "신뢰구간": []}

        for key in ordered_keys:
            if key in scores:
                data["지표점수"].append(scores[key].get("지표점수", ""))
                data["백분위"].append(scores[key].get("백분위", ""))
                data["진단분류"].append(scores[key].get("진단분류", ""))
                data["신뢰구간"].append(scores[key].get("신뢰구간", ""))
            else:
                data["지표점수"].append("")
                data["백분위"].append("")
                data["진단분류"].append("")
                data["신뢰구간"].append("")

    df = pd.DataFrame(data, index=ordered_keys).T
    return df


def format_subtest_scores_excel(scores):
    grouped = {}
    for k, v in scores.items():
        if "_" in k:
            domain, name = k.split("_", 1)
        else:
            domain, name = "기타", k
        grouped.setdefault(domain, {})[name] = v

    ordered_domains = ["언어이해", "시공간", "유동추론", "지각추론", "작업기억", "처리속도", "기타"]

    table_data = {}
    for domain in ordered_domains:
        if domain in grouped:
            for subtest, val in grouped[domain].items():
                table_data.setdefault(domain, []).append((subtest, val))

    columns = []
    values = []
    for domain, items in table_data.items():
        for subtest, _ in items:
            columns.append((domain, subtest))
        for subtest, val in items:
            values.append(val if val is not None else "")

    if not columns:
        return pd.DataFrame()
    df = pd.DataFrame([values], columns=pd.MultiIndex.from_tuples(columns))
    return df


# -------------------------------
# ✅ 하드코딩 실행 진입점
# -------------------------------
if __name__ == "__main__":
    pdf_path = r"C:\Users\HATAE\Downloads\PythonProject2\K-WPPSI-IV(유아용)_4세미만.pdf"

    if not os.path.exists(pdf_path):
        print(f"❗ 파일이 존재하지 않습니다: {pdf_path}")
        exit(1)

    print(f"✅ PDF 분석 시작: {pdf_path}")
    scores, filename = extract_all_scores(pdf_path)
    is_wais = "WAIS" in filename

    print("\n📌 [지표 점수]")
    df_index = format_index_scores_excel(scores["지표점수"], is_wais=is_wais)
    print(df_index.fillna(""))

    print("\n📌 [소검사 점수]")
    df_subtest = format_subtest_scores_excel(scores["소검사점수"])
    if not df_subtest.empty:
        print(df_subtest.fillna(""))
    else:
        print("❗ 소검사 점수가 없습니다.")
