import streamlit as st
import tempfile
import os
from MakePdfFileEnough import generate_full_pdf, merge_examiner_info_from_files
from 추출_지능검사_통합 import extract_all_scores
from 추출_TCI_산출 import TCI_extract_all_scores
from 추출_PAT_산출 import PAT_extract_all_scores
import traceback

print("=================================start==============================")
st.set_page_config(page_title="굿이너프 리포트 생성기", layout="centered")
st.title("📄 굿이너프 리포트 생성기")


score_category ={
    "전체 지능" : "FSIQ",
    "전체IQ" : "FSIQ",
    "언어이해" : "VCI",
    "시공간" : "VSI",
    "유동추론" : "FRI",
    "작업기억" : "WMI",
    "지각추론" : "PRI",
    "처리속도" : "PSI"
}

# 1. 파일 업로드 영역
uploaded_files = st.file_uploader("📂 검사자 PDF 업로드", type="pdf", accept_multiple_files=True)
logo_file = st.file_uploader("🖼️ 로고 이미지 업로드 (선택)", type=["png", "jpg", "jpeg"])

# 2. 업로드 확인
if not uploaded_files:
    st.info("👆 먼저 검사자 PDF 파일을 업로드해주세요.")
    st.stop()

# 3. 임시 파일로 저장
# 임시 저장 경로와 함께 원래 파일명도 저장
temp_files = []

for f in uploaded_files:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(f.read())
    tmp.flush()
    temp_files.append({
        "path": tmp.name,
        "original_name": f.name
    })
# 4. 로고 이미지 저장
logo_path = os.path.abspath("logo.png")  # 현재 폴더 기준 절대경로


def generate_summary_text(score_data, score_category):
    index_scores = score_data["지표점수"]
    subtest_scores = score_data["소검사점수"]

    # 도메인별 하위검사 분류하기
    domain_map = {}
    for k in subtest_scores:
        if "_" not in k:
            continue
        domain, subtest = k.split("_", 1)
        domain_map.setdefault(domain, []).append(subtest)

    # 도메인 순서 정렬 (전체지능 먼저, 이후 점수순 정렬)
    domain_order = list(score_category.keys())
    domain_order = [d for d in domain_order if d in index_scores]  # 점수 있는 도메인만
    if "전체IQ" in domain_order:
        domain_order.remove("전체IQ")
    if "전체 지능" in domain_order:
        domain_order.remove("전체 지능")
    domain_order = ["전체IQ"] + domain_order

    domain_title_desc = {}
    # 요약문 문장 구성
    for domain in domain_order:
        if domain not in index_scores or domain not in domain_map:
            continue  # 소검사가 없는 도메인은 건너뜀
        desc_lines = []

        code = score_category.get(domain, "")
        score = index_scores[domain].get("지표점수", "")
        level = index_scores[domain].get("진단분류", "")

        subtexts = []
        for subtest in domain_map[domain]:
            full_key = f"{domain}_{subtest}"
            if full_key in subtest_scores:
                sub_score = subtest_scores[full_key]
                # 점수 기반 진단분류 대략 추정 (옵션)
                try:
                    s = int(sub_score)
                    if s >= 15:
                        sub_level = "우수"
                    elif s >= 12:
                        sub_level = "평균 상"
                    elif s >= 9:
                        sub_level = "평균"
                    else:
                        sub_level = "미흡"
                except:
                    sub_level = "평균"
                subtexts.append(f"‘{subtest}’ 소검사의 수행이 [{sub_level}] 수준으로,")
                if subtest == "어휘":
                    subtexts.append(f"개별 어휘에 대한 이해를 토대로 유창하게 표현하는 능력이 \n")
                elif subtest == "공통성":
                    subtexts.append(f"언어적 지식을 활용하여 새로운 개념을 추론하는 능력이 \n")
                elif subtest == "퍼즐":
                    subtexts.append(f"시공간적 자극을 정신적으로 회전하고 조직화하는 능력이 \n")
                elif subtest == "토막짜기":
                    subtexts.append(f"시각적 자극을 물리적으로 분석하고 통합하는 능력이 \n")
                elif subtest == "행렬추리":
                    subtexts.append(f"시공간 자극의 관계를 유추하는 능력이 \n")
                elif subtest == "숫자":
                    subtexts.append(f"청각적 작업기억력이 \n")
                elif subtest == "산수":
                    subtexts.append(f"암산 능력이 \n")
                elif subtest == "기호쓰기":
                    subtexts.append(f"시각-운동 협응 속도가 \n")
                elif subtest == "동형찾기":
                    subtexts.append(f"시각적 탐색 및 변별 속도가 \n")
                else:
                    subtexts.append(f"등록되지 않은 소검사 항목입니다. 관리자에게 요청해주세요.\n")

        for text in subtexts:
            desc_lines.append(text)

        result = ''.join(desc_lines)

        domain_title_desc[domain] = [domain,code,score,level,result]

    return domain_title_desc



# 5. 검사자 정보 추출
merged_info, warn_msgs = merge_examiner_info_from_files(temp_files)

# ✅ scores 먼저 추출 (요약문 생성에 필요)
for file in temp_files:
    print(file)
    if ("WAIS" in file["original_name"]) or ("WISC" in file["original_name"]) or ("WPPSI" in file["original_name"]):
        scores, filename = extract_all_scores(file["path"], original_name=file["original_name"])
    elif "TCI" in file["original_name"]:
        TCI_scores, TCI_filename = TCI_extract_all_scores(file["path"], original_name=file["original_name"])
    elif "PAT" in file["original_name"]:
        PAT_scores, PAT_filename = PAT_extract_all_scores(file["path"], original_name=file["original_name"])
# ✅ 요약문 생성 함수
IntelligenceDomain = generate_summary_text(scores, score_category)

default_summary = {}
for i in IntelligenceDomain.keys():
    default_summary[i]=IntelligenceDomain[i][4]

# 6. 수정 가능한 검사자 정보 입력 폼
st.subheader("📝 검사자 정보 확인 및 수정")

with st.form("examiner_info_form"):
    name = st.text_input("이름(성별,나이)", merged_info["이름"])
    birth = st.text_input("생년월일", merged_info["생년월일"])
    exam_date = st.text_input("검사일자", merged_info["검사일자"])
    education = st.text_input("교육", merged_info["교육"])
    tests = st.text_input("실시검사", merged_info["실시검사"])
    attitude = st.text_area("검사태도", merged_info.get("검사태도", ""))
    # ✅ 여기서 요약문도 함께 수정하도록 추가

    st.subheader("🧠 지능검사 요약문 확인 및 수정")
    for i in default_summary.keys():
        default_summary[i] = st.text_area(f"📝 {i} 요약문", default_summary[i], height=120)

    # 최종 요약 및 제언
    st.subheader("📌 지능검사 최종 요약 및 제언")
    final_summary = st.text_area(
        "",
        height=250,
        placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ..."
    )

    submit = st.form_submit_button("📄 PDF 리포트 생성")

for i in IntelligenceDomain.keys():
    IntelligenceDomain[i][4]=default_summary[i]

# 7. PDF 생성
if submit:
    # 업데이트된 정보 반영
    merged_info.update({
        "이름": name,
        "생년월일": birth,
        "검사일자": exam_date,
        "교육": education,
        "실시검사": tests,
        "검사태도": attitude  # ← 추가된 라인
    })

    # 필요한 값 추출
    index_scores = scores["지표점수"]


    def safe_get_index_value(index_scores, keys: list[str], field="지표점수", default=None):
        for key in keys:
            if key in index_scores:
                return index_scores[key].get(field, default)
        return default


    # --- 전체 지능 지수 (FSIQ)
    fsiq_score = safe_get_index_value(index_scores, ["전체IQ", "전체검사"], field="지표점수", default=100)
    fsiq_percentile_raw = safe_get_index_value(index_scores, ["전체IQ", "전체검사"], field="백분위", default="50")
    confidence_interval_raw = safe_get_index_value(index_scores, ["전체IQ", "전체검사"], field="신뢰구간", default="")
    ci_min, ci_max = 100, 120  # 기본값

    # 문자열일 경우 파싱
    if isinstance(confidence_interval_raw, str):
        for delim in ['~', '-', '–']:  # 일반 하이픈, 물결, 긴 하이픈(복사된 PDF에서 자주 발생)
            if delim in confidence_interval_raw:
                try:
                    parts = confidence_interval_raw.split(delim)
                    ci_min = int(parts[0].strip())
                    ci_max = int(parts[1].strip())
                    break  # 성공 시 반복 종료
                except Exception as e:
                    print("⚠️ 신뢰구간 파싱 실패:", e)
                    continue

    # --- 백분위는 %로 계산 (낮을수록 상위)
    try:
        fsiq_percentile = 100 - int(fsiq_percentile_raw)
    except:
        fsiq_percentile = 50

    # --- 주요 지표 이름 목록
    subtest_keys = ["언어이해", "시공간", "유동추론", "지각추론", "작업기억", "처리속도"]

    # --- 유효 점수만 필터링
    # --- 유효 점수만 필터링 (문자열 숫자도 int로 변환)
    valid_items = {}
    diagnosis_labels = {}

    for k in subtest_keys:
        info = index_scores.get(k, {})
        raw_score = info.get("지표점수", None)
        raw_diagnosis = info.get("진단분류", "")
        try:
            score = int(raw_score)
            valid_items[k] = score
            diagnosis_labels[k] = raw_diagnosis
        except:
            continue  # 지표점수가 int로 변환되지 않으면 건너뜀


    # 전체IQ 진단분류 추가
    if "전체IQ" in index_scores:
        diagnosis_labels["전체IQ"] = index_scores["전체IQ"].get("진단분류", "")

    if valid_items:
        sorted_items = sorted(valid_items.items(), key=lambda x: x[1], reverse=True)
        strength_label = f"{sorted_items[0][0]} 지표"
        strength_score = sorted_items[0][1]
        weakness_label = f"{sorted_items[-1][0]} 지표"
        weakness_score = sorted_items[-1][1]
    else:
        # 기본값 처리
        strength_label = "언어이해 지표"
        strength_score = 100
        weakness_label = "처리속도 지표"
        weakness_score = 100

    # --- sub_scores: 백분위 → 100 - 값 (% 상위값)
    sub_scores = {}
    for k in ["언어이해", "시공간", "유동추론", "작업기억", "처리속도"]:
        raw_percentile = index_scores.get(k, {}).get("백분위", "")
        try:
            sub_scores[k] = 100 - int(raw_percentile)
        except:
            sub_scores[k] = 50

    # 모든 지표점수만 추출
    all_index_scores = {}
    for key, value in scores["지표점수"].items():
        try:
            all_index_scores[key] = int(value["지표점수"])
        except:
            continue


    # PDF 생성
    output_path = os.path.join(tempfile.gettempdir(), "generated_report.pdf")
    try:
        generate_full_pdf(
            output_path=output_path,
            input_pdf_paths=[f["path"] for f in temp_files],
            manual_info=merged_info,
            logo_path=logo_path,
            wechsler_data={
                "fsiq": fsiq_score,
                "percentile": fsiq_percentile,
                "strength_label": strength_label,
                "strength_score": strength_score,
                "weakness_label": weakness_label,
                "weakness_score": weakness_score,
                "sub_scores": sub_scores,
                "ci_min": ci_min,
                "ci_max": ci_max,
                "diagnosis_labels": diagnosis_labels,
                "subtest_scores": scores.get("소검사점수", {}),
                ** {"index_scores_all": all_index_scores},  # ✅ 추가
                "IntelligenceDomain": IntelligenceDomain,
                "final_summary" : final_summary,
            },
            TCI_scores=TCI_scores,
            PAT_scores=PAT_scores
        )
        with open(output_path, "rb") as f:
            st.success("✅ PDF 생성이 완료되었습니다!")
            st.download_button("📥 리포트 다운로드", f, file_name="굿이너프_리포트.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"🚨 PDF 생성 중 오류가 발생했습니다: {e}")
        st.text("🔍 전체 오류 내용:")
        st.text(traceback.format_exc())  # 전체 스택 추적 로그 출력

