import pdfplumber
import re
import json
import pdfplumber
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload  # ✅ 추가
from oauth2client.service_account import ServiceAccountCredentials
import io

def load_google_service_account_key():
    return st.secrets["gcp"]

@st.cache_resource(ttl=3000, show_spinner=False)
def get_drive_service():
    scope = ['https://www.googleapis.com/auth/drive']
    key_dict = load_google_service_account_key()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    return build('drive', 'v3', credentials=creds)

@st.cache_data(ttl=3000, show_spinner=False)
def load_temperament_dict_from_drive():
    service = get_drive_service()

    file_id = "15ekhcGi28YNnSR6nBF-bKulkVNLwZs9g"  # ✅ Google Drive 파일 ID

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)
# ✅ 이상적 범위 (기존 유지)
ideal_ranges = {
    "지지표현": (65, 85),
    "합리적 설명": (65, 85),
    "성취압력": (50, 70),
    "간섭": (40, 60),
    "처벌": (30, 50),
    "감독": (30, 50),
    "과잉기대": (20, 40),
    "비일관성": (10, 30)
}
factors_order = list(ideal_ranges.keys())

def evaluate_results(percentiles):
    results = []
    for i, value in enumerate(percentiles):
        low, high = ideal_ranges[factors_order[i]]
        if value < low:
            results.append("미흡함")
        elif value > high:
            results.append("지나침")
        else:
            results.append("이상적임")
    return results

# ✅ PDF에서 백분위 추출 (텍스트 기반)
def extract_pat_percentiles(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[2]  # ✅ 기존 page_num=2 유지
        text = page.extract_text()

    seq_match = re.search(r"(\d+\s+){7}\d+", text)
    numbers = []
    if seq_match:
        numbers = [int(n) for n in re.findall(r"\d+", seq_match.group()) if 10 <= int(n) <= 100]

    evaluated = evaluate_results(numbers) if len(numbers) == 8 else []
    return {"백분위": numbers, "결과": evaluated}


explain_data = load_temperament_dict_from_drive()

# ✅ 최종 출력
def print_result_with_explain(evaluated):
    ideal_titles, ideal_contents = [], []
    non_ideal_titles, non_ideal_contents = [], []

    for key, value in zip(factors_order, evaluated):
        if value == "이상적임":
            ideal_titles.append(key)
            ideal_contents.append(explain_data[key]["이상적임"])
        elif value == "미흡함":
            non_ideal_titles.append(key)
            non_ideal_contents.append(explain_data[key]["미흡함"])
        elif value == "지나침":
            non_ideal_titles.append(key)
            non_ideal_contents.append(explain_data[key]["지나침"])

    print(f"[이상적임] 영역 설명 - {', '.join(ideal_titles)}")
    for text in ideal_contents:
        print(text + "\n")

    print(f"[미흡함 또는 지나침] 영역 설명 - {', '.join(non_ideal_titles)}")
    for text in non_ideal_contents:
        print(text + "\n")

    return  [ideal_titles, ideal_contents, non_ideal_titles, non_ideal_contents]

def PAT_extract_all_scores(pdf_path, original_name=None, json_file=None):
    filename = (original_name or os.path.basename(pdf_path)).upper()
    if "PAT" in filename:
        result = extract_pat_percentiles(pdf_path)
        result['ideal'] = print_result_with_explain(result["결과"])

    return result, filename
if __name__ == "__main__":
    # ✅ 실행
    pdf_files = ["PAT-1.pdf", "PAT-2.pdf"]

    for pdf in pdf_files:
        data = extract_pat_percentiles(pdf)
        # print(f"\n▶ {pdf} 최종 개선 결과")
        # print("data",data)
        # print("백분위:", data["백분위"])
        # print("결과:", data["결과"])
        # print_result_with_explain(data["결과"])
