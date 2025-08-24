import streamlit as st
import tempfile
import os
from MakePdfFileEnough import generate_full_pdf, merge_examiner_info_from_files
from 추출_지능검사_통합 import INT_extract_all_scores
from 추출_TCI_산출 import TCI_extract_all_scores
from 추출_PAT_산출 import PAT_extract_all_scores
import traceback
import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials

def load_google_service_account_key():
    return st.secrets["gcp"]

@st.cache_resource(ttl=3000, show_spinner=False)
def get_drive_service():
    scope = ['https://www.googleapis.com/auth/drive']
    key_dict = load_google_service_account_key()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    return build('drive', 'v3', credentials=creds)

def load_temperament_dict_from_drive(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)

st.set_page_config(page_title="굿이너프 보고서 생성기", layout="centered")


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "password_attempted" not in st.session_state:
    st.session_state.password_attempted = ""  


if not st.session_state.authenticated:
    st.title("🔒 접근 제한")

    with st.form("password_form", clear_on_submit=True):  
        password_input = st.text_input("접근 비밀번호를 입력하세요", type="password", value="")
        submitted = st.form_submit_button("확인")  

    if submitted:
        try:
            password_json = load_temperament_dict_from_drive("1GRb3MVsb4TcaveVlGFZgCEPqmg5TBww6")
            correct_password = password_json.get("password", "")

            if password_input == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 일치하지 않습니다.")
        except Exception as e:
            st.error("🚨 비밀번호 로딩 중 오류 발생")
            st.text(str(e))

    st.stop()


if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "temp_paths" not in st.session_state:
    st.session_state.temp_paths = []
    
examiner = load_temperament_dict_from_drive("1n6VEjr0QBMOdmT-TG_VjP3VL3dxUS75o")
title = load_temperament_dict_from_drive("1h_jT9f5IJA4GVmG12ffzhrlaQNeSknmg")



def is_valid_filename(fname: str) -> tuple[bool, str]:
    """
    규칙:
    - 파일명(소문자 기준)에 wais, wisc, wppsi, tci, pat 중 하나가 포함되어야 함
    - wppsi 인 경우, 공백 제거한 파일명에 '4세이상' 또는 '4세미만'가 반드시 포함되어야 함
    """
    f = fname.lower()
    compact = f.replace(" ", "")
    kinds = ("wais", "wisc", "wppsi", "tci", "pat")

    if not any(k in f for k in kinds):
        return False, "파일명에 검사 종류(wais, wisc, wppsi, tci, pat)가 없습니다."

    if "wppsi" in f:
        if not ("4세이상" in compact or "4세미만" in compact):
            return False, "WPPSI는 파일명에 '4세이상' 또는 '4세미만' 문구가 포함되어야 합니다. (공백 허용)"

    return True, ""

print("=================================start==============================")
st.set_page_config(page_title=f"{title} 보고서 생성기", layout="centered")
st.title(f"📄 {title} 보고서 생성기")


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


uploaded_files = st.file_uploader(
    "📂 피검사자 PDF 업로드",
    type="pdf",
    accept_multiple_files=True,
    key="pdf_uploader"
)


if not uploaded_files:
    st.info("👆 먼저 피검사자 PDF 파일을 업로드해주세요.")
    st.stop()


valid_uploaded = []
invalid_reports = []
for f in uploaded_files:
    ok, reason = is_valid_filename(f.name)  
    if ok:
        valid_uploaded.append(f)
    else:
        invalid_reports.append(f"• {f.name} → {reason}")

if invalid_reports:
    st.error("다음 파일은 파일명 규칙을 만족하지 않아 제외됩니다:\n\n" + "\n".join(invalid_reports))


if not valid_uploaded:
    st.info("규칙에 맞는 파일이 없습니다. 파일명을 확인한 뒤 다시 업로드해 주세요.")
    st.stop()



temp_files = []
st.session_state.temp_paths = []  


for f in valid_uploaded:  
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(f.read())
    tmp.flush()
    temp_files.append({"path": tmp.name, "original_name": f.name})
    st.session_state.temp_paths.append(tmp.name)  


def generate_summary_text(score_data, score_category):
    index_scores = score_data["지표점수"]
    subtest_scores = score_data["소검사점수"]

    
    domain_map = {}
    for k in subtest_scores:
        if "_" not in k:
            continue
        domain, subtest = k.split("_", 1)
        domain_map.setdefault(domain, []).append(subtest)

    
    domain_order = list(score_category.keys())
    domain_order = [d for d in domain_order if d in index_scores]  
    if "전체IQ" in domain_order:
        domain_order.remove("전체IQ")
    if "전체 지능" in domain_order:
        domain_order.remove("전체 지능")
    domain_order = ["전체IQ"] + domain_order
    domain_title_desc = {}
    
    for domain in domain_order:
        if domain not in index_scores or domain not in domain_map:
            continue  
        desc_lines = []

        code = score_category.get(domain, "")
        score = index_scores[domain].get("지표점수", "")
        level = index_scores[domain].get("진단분류", "")

        subtexts = []
        for subtest in domain_map[domain]:
            full_key = f"{domain}_{subtest}"
            if full_key in subtest_scores:
                sub_score = subtest_scores[full_key]
                
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

def add_bullet(points: list[str]) -> str:
    """
    리스트의 각 항목 첫 줄 맨 앞에 '- ' 붙이고,
    전체를 줄바꿈으로 연결된 문자열로 반환
    """
    modified = []
    for item in points:
        lines = item.split("\n", 1)  
        first_line = "- " + lines[0].strip()  
        if len(lines) > 1:
            modified_item = "\n" + first_line + "\n" + lines[1]
        else:
            modified_item = first_line
        modified.append(modified_item.strip())
    return "\n".join(modified)



merged_info, warn_msgs = merge_examiner_info_from_files(temp_files)


INT_fileflag = 0
TCI_fileflag = 0
PAT_fileflag = 0



for file in temp_files:
    if ("wais" in file["original_name"].lower()) or ("wisc" in file["original_name"].lower()) or ("wppsi" in file["original_name"].lower()):
        INT_scores, INT_filename = INT_extract_all_scores(file["path"], original_name=file["original_name"])
        INT_fileflag = 1
        IntelligenceDomain = generate_summary_text(INT_scores, score_category)
        default_summary = {}
        for i in IntelligenceDomain.keys():
            default_summary[i] = IntelligenceDomain[i][4]

    elif "tci" in file["original_name"].lower():
        TCI_scores, TCI_filename = TCI_extract_all_scores(file["path"], original_name=file["original_name"])
        TCI_fileflag = 1

    elif "pat" in file["original_name"].lower():
        PAT_scores, PAT_filename = PAT_extract_all_scores(file["path"], original_name=file["original_name"])
        PAT_fileflag = 1
        
        PAT_scores['ideal'][1] = add_bullet(PAT_scores['ideal'][1])
        PAT_scores['ideal'][3] = add_bullet(PAT_scores['ideal'][3])



st.subheader("🙋‍♂️ 개발자 공지")
st.text_area(
    "",
    height=250,
    value="0. 파일을 업로드할 때는 항상 초기화 실행 후 업로드"
          "1. 현재 지능검사 WAIS의 경우 진단 분류 기준 확인 불가로 잘못 기재될 수 있음"
)


if "custom_pages" not in st.session_state:
    st.session_state.custom_pages = []

st.header("사용자 정의 PDF 페이지 생성")
st.write("아래 버튼을 눌러 원하는 만큼 페이지를 추가하고 내용을 입력해주세요.")

if st.button("새 페이지 추가"):
    st.session_state.custom_pages.append({
        "page_type": "텍스트 전용",
        "title": "",
        "subtitle": "",
        "summary_title": "",
        "summary_content": "",
        "image_path": None
    })
    st.rerun()

for i, page_data in enumerate(st.session_state.custom_pages):

    
    col1, col2, col3 = st.columns([5, 3, 10])
    with col1:
        st.subheader(f"추가 페이지 {i + 1}")
    with col2:
        if st.button("삭제", key=f"delete_{i}"):
            st.session_state.custom_pages.pop(i)
            st.rerun()
    with col3:
        st.markdown("")  

    
    page_data["page_type"] = st.radio(
        "페이지 유형을 선택하세요:",
        ["텍스트 전용 페이지", "그림 포함 페이지"],
        key=f"page_type_{i}",
        horizontal=True,
        index=0 if page_data["page_type"] == "텍스트 전용 페이지" else 1
    )

    page_data["title"] = st.text_input("제목 (예: 웩슬러 지능검사)", value=page_data["title"], key=f"title_{i}")
    page_data["subtitle"] = st.text_input("부제목 (예: Korean ~~)", value=page_data["subtitle"], key=f"subtitle_{i}")

    
    if page_data["page_type"] == "그림 포함 페이지":
        uploaded_image = st.file_uploader("그림 파일을 업로드해주세요 (JPG, PNG)", type=["jpg", "jpeg", "png"],
                                          key=f"image_uploader_{i}")
        if uploaded_image:
            import tempfile, os

            temp_dir = tempfile.gettempdir()
            image_path = os.path.join(temp_dir, uploaded_image.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_image.getbuffer())
            page_data["image_path"] = image_path
        else:
            page_data["image_path"] = None

    page_data["summary_title"] = st.text_input("본문 명칭 (예: 요약 및 제언)", value=page_data["summary_title"],
                                               key=f"sum_title_{i}")
    page_data["summary_content"] = st.text_area("본문 내용", value=page_data["summary_content"], key=f"sum_content_{i}")

    st.markdown("---")




with st.form("examiner_info_form"):
    st.subheader("👨‍⚕️ 검사자 정보")
    examiner = st.text_input("검사자", examiner)

    st.subheader("🙍‍♂️ 피검사자 정보")
    name = st.text_input("이름(성별,나이)", merged_info["이름"])
    birth = st.text_input("생년월일", merged_info["생년월일"])
    exam_date = st.text_input("검사일자", merged_info["검사일자"])
    education = st.text_input("교육", merged_info["교육"])
    tests = st.text_input("실시검사", merged_info["실시검사"])
    attitude = "※ 검사태도에 대한 정보가 입력되지 않았습니다."

    if INT_fileflag == 1:
        attitude = st.text_area("검사태도", merged_info.get("검사태도", ""))

        st.subheader("🧠 지능검사 (자동생성)")
        for i in default_summary.keys():
            default_summary[i] = st.text_area(f"{i} 요약", default_summary[i], height=120)

        
        final_summary = st.text_area(
            "지능검사 최종 요약 및 제언",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ..."
        )

    if TCI_fileflag == 1:
        
        st.subheader("🤓 기질 및 성격 검사 (자동 생성)")
        기질1 = st.text_area(
            "기질 1 (줄바꿈 2번 -> 선)",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ...",
            value=TCI_scores[3][0][4]
        )
        기질2 = st.text_area(
            "기질 2 (줄바꿈 2번 -> 선)",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ...",
            value=TCI_scores[3][1][4]
        )
        요약및제언1 = st.text_area(
            "기질 최적화 양육 방법1 (- -> 굵은 글씨)",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ...",
            value=TCI_scores[4][0][4]
        )
        요약및제언2 = st.text_area(
            "기질 최적화 양육 방법2 (- -> 굵은 글씨)",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ...",
            value=TCI_scores[4][1][4]
        )
        성격 = st.text_area(
            "성격 (줄바꿈 2번 -> 선)",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ...",
            value=TCI_scores[3][2][4]
        )
        요약및제언3 = st.text_area(
            "성숙한 성격 발달 방법 (비어있는 경우 미생성)",
            height=250,
            placeholder="예: 전반적으로 우수한 지능을 보이며, 특히 언어이해 영역에서 높은 수행을 보였습니다. ...",
            value=TCI_scores[4][2][4]
        )

    if PAT_fileflag == 1:
        
        st.subheader("👨👩 부모 양육태도 검사 (자동 생성)")
        부모_양육태도_이상 = st.text_area(
            "부모 양육태도 검사 - 이상적",
            height=250,
            placeholder="예: 아이의 성과나 수행에 대해 적절한 수준의 압력을 제공하고 있습니다. ...",
            value=PAT_scores['ideal'][1]
        )
        부모_양육태도_비이상 = st.text_area(
            "부모 양육태도 검사 - 비이상적",
            height=250,
            placeholder="예: 아이에게 애정, 지지나 격려의 표현을 적게 하는 편입니다. ...",
            value=PAT_scores['ideal'][3]
        )

    submit = st.form_submit_button("📄 PDF 리포트 생성")

if INT_fileflag == 1:
    for i in IntelligenceDomain.keys():
        IntelligenceDomain[i][4]=default_summary[i]


if submit:
    
    merged_info.update({
        "이름": name,
        "생년월일": birth,
        "검사일자": exam_date,
        "교육": education,
        "실시검사": tests,
        "검사태도": attitude  
    })
    def safe_get_index_value(index_scores, keys: list[str], field="지표점수", default=None):
        for key in keys:
            if key in index_scores:
                return index_scores[key].get(field, default)
        return default

    if INT_fileflag == 1:
        
        index_scores = INT_scores["지표점수"]

        
        fsiq_score = safe_get_index_value(index_scores, ["전체IQ", "전체검사"], field="지표점수", default=100)
        fsiq_percentile_raw = safe_get_index_value(index_scores, ["전체IQ", "전체검사"], field="백분위", default="50")
        confidence_interval_raw = safe_get_index_value(index_scores, ["전체IQ", "전체검사"], field="신뢰구간", default="")
        ci_min, ci_max = 100, 120  

        
        if isinstance(confidence_interval_raw, str):
            for delim in ['~', '-', '–']:  
                if delim in confidence_interval_raw:
                    try:
                        parts = confidence_interval_raw.split(delim)
                        ci_min = int(parts[0].strip())
                        ci_max = int(parts[1].strip())
                        break  
                    except Exception as e:
                        print("⚠️ 신뢰구간 파싱 실패:", e)
                        continue

        
        try:
            fsiq_percentile = 100 - int(fsiq_percentile_raw)
        except:
            fsiq_percentile = int(100 - float(fsiq_percentile_raw))

        
        subtest_keys = ["언어이해", "시공간", "유동추론", "지각추론", "작업기억", "처리속도"]

        
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
                continue  

        
        if "전체IQ" in index_scores:
            diagnosis_labels["전체IQ"] = index_scores["전체IQ"].get("진단분류", "")

        if valid_items:
            sorted_items = sorted(valid_items.items(), key=lambda x: x[1], reverse=True)
            strength_label = f"{sorted_items[0][0]} 지표"
            strength_score = sorted_items[0][1]
            weakness_label = f"{sorted_items[-1][0]} 지표"
            weakness_score = sorted_items[-1][1]
        else:
            
            strength_label = "언어이해 지표"
            strength_score = 100
            weakness_label = "처리속도 지표"
            weakness_score = 100

        
        sub_scores = {}
        for k in ["언어이해", "지각추론", "시공간", "유동추론", "작업기억", "처리속도"]:
            raw_percentile = index_scores.get(k, {}).get("백분위", "")

            try:
                val = float(str(raw_percentile).strip())
                sub_scores[k] = int(100 - val)
            except (ValueError, TypeError):
                
                continue

        
        all_index_scores = {}
        for key, value in INT_scores["지표점수"].items():
            try:
                all_index_scores[key] = int(value["지표점수"])
            except:
                continue

        INT_data = {
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
            "subtest_scores": INT_scores.get("소검사점수", {}),
            **{"index_scores_all": all_index_scores},  
            "IntelligenceDomain": IntelligenceDomain,
            "final_summary": final_summary,
            "INT_filename": INT_filename,
        }

    if TCI_fileflag == 1:
        TCI_scores[3][0][4] = 기질1
        TCI_scores[3][1][4] = 기질2
        TCI_scores[3][2][4] = 성격
        TCI_scores[4][0][4] = 요약및제언1
        TCI_scores[4][1][4] = 요약및제언2
        TCI_scores[4][2][4] = 요약및제언3

    if PAT_fileflag == 1:
        PAT_scores['ideal'][1] = 부모_양육태도_이상
        PAT_scores['ideal'][3] = 부모_양육태도_비이상


    output_path = os.path.join(tempfile.gettempdir(), "generated_report.pdf")
    try:
        generate_full_pdf(
            output_path=output_path,
            input_pdf_paths=[f["path"] for f in temp_files],
            manual_info=merged_info,
            INT_data=INT_data if INT_fileflag == 1 else None,
            TCI_scores=TCI_scores if TCI_fileflag == 1 else None,
            PAT_scores=PAT_scores if PAT_fileflag == 1 else None,
            TCI_filename=TCI_filename if TCI_fileflag == 1 else None,
            PAT_filename=PAT_filename if PAT_fileflag == 1 else None,
            custom_pages=st.session_state.custom_pages, 
            examiner=examiner,
        )
        with open(output_path, "rb") as f:
            st.success("✅ PDF 생성이 완료되었습니다!")
            st.download_button("📥 리포트 다운로드", f, file_name=f"{title}_리포트.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"🚨 PDF 생성 중 오류가 발생했습니다: {e}")
        st.text("🔍 전체 오류 내용:")
        st.text(traceback.format_exc())  


