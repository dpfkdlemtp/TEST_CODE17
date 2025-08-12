import json
import re
import pdfplumber
import os
import pdfplumber
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload  # ✅ 추가
from oauth2client.service_account import ServiceAccountCredentials
import io
import streamlit as st


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

    file_id = "1lbrWh85_80gZ8oBDq88-s-U2azXpFWkV"  # ✅ Google Drive 파일 ID

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)
# ---------------------------
# 1) TCI 백분위 H/M/L 추출
# ---------------------------
def extract_tci_percentiles(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

    lines = text.split("\n")

    tci_scales = [
        "자극추구", "위험회피", "사회적 민감성", "인내력",
        "자율성", "연대감", "자기초월", "자율성+연대감"
    ]
    tci_codes = ["NS", "HA", "RD", "PS", "SD", "CO", "ST", "SC"]

    percentiles = {}
    seen = set()

    for line in lines:
        for scale, code in zip(tci_scales, tci_codes):
            if (scale in line or code in line) and scale not in seen:
                nums = re.findall(r"\d+", line)
                if len(nums) >= 3:
                    oriScore = int(nums[0])
                    Tscore = int(nums[1])
                    p = int(nums[2])
                    level = "H" if p > 65 else "M" if p >= 35 else "L"
                    percentiles[scale] = {"percentile": p, "level": level, "oriScore": oriScore, "Tscore":Tscore}
                    seen.add(scale)
    return percentiles

# ---------------------------
# 2) TCI 하위척도 M(SD) 추출
# ---------------------------
def extract_tci_m_sd(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[1]
        text = page.extract_text()

    lines = text.split("\n")
    m_sd_result = {}
    pattern = re.compile(r"([A-Z]{2}\d)\s+\d+\s+([\d.]+)\s*\(([\d.]+)\)")

    for line in lines:
        match = pattern.search(line)
        if match:
            subscale = match.group(1)
            m_sd_result[subscale] = {"M": float(match.group(2)), "SD": float(match.group(3))}
    return m_sd_result



# ---------------------------
# 4) 사회적 민감성 보정 로직
# ---------------------------
def adjust_social_sensitivity(hml: dict, m_sd: dict) -> str:
    rd_level = hml["사회적 민감성"]
    # RD 하위척도가 없으면 그냥 level만 반환
    if rd_level == "H":
        rd3 = m_sd.get("RD3", {}).get("M", 0)
        rd4 = m_sd.get("RD4", {}).get("M", 0)
        if rd3 >= 11.6 + 3.3 and rd4 <= 9.4 - 2.6:
            return "H(친밀+독립)"
        elif rd4 >= 9.4 + 2.6 and rd3 <= 11.6 - 3.3:
            return "H(거리두기+의존)"
        else:
            return "H(친밀+의존)"
    elif rd_level == "L":
        rd1 = m_sd.get("RD1", {}).get("M", 0)
        if rd1 >= 11.1 - 2.9:
            return "L(높은/적절한 정서적 감수성)"
        else:
            return "L(typical)"
    return rd_level

# ---------------------------
# 5) 매칭 키 생성
# ---------------------------
def build_matching_Temperament_keys(hml: dict, m_sd: dict) -> dict:
    social_key = adjust_social_sensitivity(hml, m_sd)
    return {
        "기질1": f"자극추구{hml['자극추구']} 위험회피{hml['위험회피']} 인내력{hml['인내력']}",
        "기질2": f"자극추구{hml['자극추구']} 위험회피{hml['위험회피']} 사회적민감성{social_key}",
        "성격": f"자율성{hml['자율성']} 연대감{hml['연대감']}"
    }

def build_matching_Summary_keys(hml: dict, m_sd: dict) -> dict:
    social_key = adjust_social_sensitivity(hml, m_sd)
    return {
        "요약및제언1": f"자극추구{hml['자극추구']} 위험회피{hml['위험회피']} 인내력{hml['인내력']}",
        "요약및제언2": f"자극추구{hml['자극추구']} 위험회피{hml['위험회피']} 사회적민감성{social_key}",
        "요약및제언3": f"자율성{hml['자율성']} 연대감{hml['연대감']}"
    }

# ---------------------------
# 6) JSON 유사 키 탐색
# ---------------------------
def find_best_matching_key(search_key: str, data: dict) -> tuple:
    if search_key in data:
        return search_key, "✅ 완전 매칭"
    candidates = [key for key in data if search_key.replace(" ", "") in key.replace(" ", "")]
    if candidates:
        return candidates[0], "🔄 유사 매칭"
    return "", "❌ 매칭 실패"

# ---------------------------
# 7) 통합 실행
# ---------------------------

def load_temperament_dict(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(pdf_path: str, json_path: str):
    percentiles = extract_tci_percentiles(pdf_path)
    # print("\n▶ TCI-RS 백분위 (H/M/L 구분)")
    # for k, v in percentiles.items():
    #     print(f"{k} = {v['percentile']} ({v['level']})")

    m_sd = extract_tci_m_sd(pdf_path)
    # print("\n▶ TCI-RS 하위척도 M(SD)")
    # for k, v in m_sd.items():
    #     print(f"{k}: M={v['M']}, SD={v['SD']}")

    data = load_temperament_dict(json_path)

    hml_values = {
        "자극추구": percentiles.get("자극추구", {}).get("level", "M"),
        "위험회피": percentiles.get("위험회피", {}).get("level", "M"),
        "사회적 민감성": percentiles.get("사회적 민감성", {}).get("level", "M"),
        "인내력": percentiles.get("인내력", {}).get("level", "M"),
        "자율성": percentiles.get("자율성", {}).get("level", "M"),
        "연대감": percentiles.get("연대감", {}).get("level", "M"),
    }
    # print(f"\n▶ 추출된 H/M/L: {hml_values}")

    matching_keys = build_matching_Temperament_keys(hml_values, m_sd)
    # print(f"\n▶ 매칭 키: {matching_keys}")

    TempanswerList=[]
    # print("\n▶ 최종 결과")
    for part, key in matching_keys.items():
        summary_dict = data.get(f"{part}", {})
        matched_key, status = find_best_matching_key(key, data.get(part, {}))
        # print(f"\n[{part}]")
        # print(f"- 추출된 키: {key}")
        # print(f"- 매칭된 키: {matched_key if matched_key else '없음'}")
        # print(f"- 매칭 상태: {status}")
        if matched_key:
            TempanswerList.append([part,key,matched_key if matched_key else '없음',status,summary_dict[matched_key].replace("**", "")])
            print(f"- 설명:\n{summary_dict[matched_key]}")
        else:
            TempanswerList.append([part, key, matched_key if matched_key else '없음', status, '설명이 없습니다. 관리자에게 문의하세요.'])
            print("- 설명: ❌ 해당 키에 대한 설명이 없습니다.")

    matching_keys = build_matching_Summary_keys(hml_values, m_sd)
    print(f"\n▶ 매칭 키: {matching_keys}")

    SumanswerList=[]
    print("\n▶ 최종 결과")
    for part, key in matching_keys.items():
        summary_dict = data.get(f"{part}", {})
        matched_key, status = find_best_matching_key(key, data.get(part, {}))
        print(f"\n[{part}]")
        print(f"- 추출된 키: {key}")
        print(f"- 매칭된 키: {matched_key if matched_key else '없음'}")
        print(f"- 매칭 상태: {status}")
        if matched_key:
            SumanswerList.append([part,key,matched_key if matched_key else '없음',status,summary_dict[matched_key].replace("**", "")])
            print(f"- 설명:\n{summary_dict[matched_key]}")
        else:
            SumanswerList.append([part, key, matched_key if matched_key else '없음', status, '설명이 없습니다. 관리자에게 문의하세요.'])
            print("- 설명: ❌ 해당 키에 대한 설명이 없습니다.")


    return percentiles, m_sd, matching_keys, TempanswerList, SumanswerList


def TCI_extract_all_scores(pdf_path, original_name=None, json_file=None):
    filename = (original_name or os.path.basename(pdf_path)).upper()
    if "TCI" in filename:
        result = main(pdf_path,json_path="TCI.json")

    return result, filename

# ---------------------------
# 8) 실행 예시
# ---------------------------
if __name__ == "__main__":
    pdf_file = "TCI_아동.pdf"        # PDF 경로
    json_file = "temperament_categorized.json"  # JSON 경로

    with open("temperament_categorized.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("존재하는 기질1 키 목록:")
    for k in data.get("기질1", {}).keys():
        print("-", k)

    main(pdf_file, json_file)
