import fitz  # pip install pymupdf
from pathlib import Path
import pandas as pd
import re
from datetime import datetime

# ✅ Pandas 출력 옵션 (터미널에서 표 안 짤리게)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 2000)

def extract_info_fitz_lines(pdf_path):
    """모든 PDF의 첫 페이지 lines 추출"""
    doc = fitz.open(pdf_path)
    lines = [line.strip() for line in doc[0].get_text().split("\n") if line.strip()]
    return lines

def extract_info(pdf_path, original_name=""):
    filename = original_name
    lines = extract_info_fitz_lines(pdf_path)

    info = {
        "파일명": Path(pdf_path).name,
        "이름": "",
        "성별": "",
        "생년월일": "",
        "검사일자": "",
        "교육": "",  # ✅ 기본값은 빈 값
        "실시검사": ""
    }

    # ✅ WAIS
    if "WAIS" in filename:
        name = ""
        gender = ""
        age = ""
        birth_fmt = ""
        test_fmt = ""
        education = ""
        test_name = "K-WAIS-IV"

        try:
            name_raw = lines[3].strip()
            gender_full = lines[4].strip()
            gender = gender_full[0] if gender_full else ""
            birth_raw = lines[5].strip().split()[0].replace("-", "/")
            test_date_raw = lines[2].strip().replace("-", "/")

            def format_date(date_str):
                try:
                    y, m, d = map(int, date_str.split("/"))
                    return f"{y}년 {m}월 {d}일"
                except:
                    return ""

            def calculate_age(birth_str, test_str):
                try:
                    birth = datetime.strptime(birth_str, "%Y/%m/%d")
                    test = datetime.strptime(test_str, "%Y/%m/%d")
                    return test.year - birth.year - ((test.month, test.day) < (birth.month, birth.day))
                except:
                    return ""

            age_int = calculate_age(birth_raw, test_date_raw)
            age = f"{age_int}세" if age_int != "" else ""

            birth_fmt = format_date(birth_raw)
            test_fmt = format_date(test_date_raw)

            name = f"{name_raw} ({gender}, {age})" if gender and age else f"{name_raw} ({gender})"

        except:
            pass

        info.update({
            "이름": name,
            "성별": gender,
            "나이": age,
            "생년월일": birth_fmt,
            "검사일자": test_fmt,
            "교육": "",
            "실시검사": test_name
        })

    # ✅ WISC
    elif "WISC" in filename:
        name = ""
        gender = ""
        age = ""
        birth_fmt = ""
        test_fmt = ""
        education = ""
        test_name = "K-WISC-V"

        try:
            name_raw = lines[1].strip()
            gender_full = lines[2].strip()
            gender = gender_full[0] if gender_full else ""
            test_date_raw = lines[3].strip().replace("-", "/")
            birth_raw = lines[4].split("(")[1].replace(")", "") if "(" in lines[4] else lines[4]
            birth_raw = birth_raw.replace("-", "/")

            def format_date(date_str):
                try:
                    y, m, d = map(int, date_str.split("/"))
                    return f"{y}년 {m}월 {d}일"
                except:
                    return ""

            def calculate_age(birth_str, test_str):
                try:
                    birth = datetime.strptime(birth_str, "%Y/%m/%d")
                    test = datetime.strptime(test_str, "%Y/%m/%d")
                    return test.year - birth.year - ((test.month, test.day) < (birth.month, birth.day))
                except:
                    return ""

            age_int = calculate_age(birth_raw, test_date_raw)
            age = f"{age_int}세" if age_int != "" else ""

            birth_fmt = format_date(birth_raw)
            test_fmt = format_date(test_date_raw)

            name = f"{name_raw} ({gender}, {age})" if gender and age else f"{name_raw} ({gender})"

        except:
            pass

        info.update({
            "이름": name,
            "성별": gender,
            "나이": age,
            "생년월일": birth_fmt,
            "검사일자": test_fmt,
            "교육": "",
            "실시검사": test_name
        })


    # ✅ WPPSI

    elif "WPPSI" in filename:

        name = ""

        gender = ""

        age = ""

        birth_fmt = ""

        test_fmt = ""

        education = ""

        test_name = "K-WPPSI-IV"

        try:

            name_raw = lines[0].strip()

            gender_full = lines[2].strip()

            gender = gender_full[0] if gender_full else ""

            birth_raw = lines[3].strip().replace("-", "/")

            test_date_raw = lines[4].strip().replace("-", "/")

            # 생년월일에 숫자가 없으면 칸 밀림 보정

            if not any(char.isdigit() for char in birth_raw):
                birth_raw = test_date_raw

                test_date_raw = lines[5].strip().replace("-", "/")

            def format_date(date_str):

                try:

                    y, m, d = map(int, date_str.split("/"))

                    return f"{y}년 {m}월 {d}일"

                except:

                    return ""

            def calculate_age(birth_str, test_str):

                try:

                    birth = datetime.strptime(birth_str, "%Y/%m/%d")

                    test = datetime.strptime(test_str, "%Y/%m/%d")

                    return test.year - birth.year - ((test.month, test.day) < (birth.month, birth.day))

                except:

                    return ""

            age_int = calculate_age(birth_raw, test_date_raw)

            age = f"{age_int}세" if age_int != "" else ""

            birth_fmt = format_date(birth_raw)

            test_fmt = format_date(test_date_raw)

            name = f"{name_raw} ({gender}, {age})" if gender and age else f"{name_raw} ({gender})"


        except:

            pass

        info.update({

            "이름": name,

            "성별": gender,

            "나이": age,

            "생년월일": birth_fmt,

            "검사일자": test_fmt,

            "교육": "",

            "실시검사": test_name

        })



    # ✅ PAT (교육만 추출)
    elif "PAT" in filename:
        name = ""
        gender = ""
        age = ""
        birth_fmt = ""
        test_fmt = ""
        education = ""
        test_name = "PAT"

        try:
            name_raw = lines[2].strip()
            birth_raw = lines[3].strip().replace("-", "/")
            gender_full = lines[4].strip()
            gender = gender_full[0] if gender_full else ""
            test_date_raw = lines[1].strip().replace("-", "/")
            education_raw = lines[5].strip()

            # 🎯 날짜 포맷 변환
            def format_date(date_str):
                try:
                    y, m, d = map(int, date_str.split("/"))
                    return f"{y}년 {m}월 {d}일"
                except:
                    return ""

            # ✅ 나이 계산을 위해 날짜 파싱 시도
            def calculate_age(birth_str, test_str):
                try:
                    birth = datetime.strptime(birth_str, "%Y/%m/%d")
                    test = datetime.strptime(test_str, "%Y/%m/%d")
                    return test.year - birth.year - ((test.month, test.day) < (birth.month, birth.day))
                except Exception as e:
                    print("⚠️ 나이 계산 실패:", birth_str, test_str, e)
                    return ""

            age_int = calculate_age(birth_raw, test_date_raw)
            age = f"{age_int}세" if age_int != "" else ""

            birth_fmt = format_date(birth_raw)
            test_fmt = format_date(test_date_raw)

            # 교육 필터링 및 정규화
            if "/" in education_raw:
                education = education_raw.split("/")[-1].strip()
            else:
                education = education_raw.strip()

            if "학교" not in education:
                education = ""

            name = f"{name_raw} ({gender}, {age})" if gender and age else f"{name_raw} ({gender})"

        except Exception as e:
            print("⚠️ PAT 파싱 오류:", e)

        info.update({
            "이름": name,
            "성별": gender,
            "나이": age,
            "생년월일": birth_fmt,
            "검사일자": test_fmt,
            "교육": education,
            "실시검사": test_name
        })



    # ✅ TCI (교육은 항상 빈 값 유지)
    elif "TCI" in filename:
        name = ""
        gender = ""
        age = ""
        birth_fmt = ""
        test_fmt = ""
        education = ""  # TCI는 교육 없음
        test_name = "TCI"

        try:
            for line in lines:
                if "이름" in line:
                    name = line.split(":")[-1].strip()
                elif "성별" in line:
                    gender_full = line.split(":")[-1].strip()
                    gender = gender_full[0]
                elif "연령" in line:
                    age_digits = re.findall(r"\d+", line)
                    if age_digits:
                        age = f"{age_digits[0]}세"
                elif "검사일" in line:
                    raw = line.split(":")[-1].strip()
                    if len(raw) == 8 and raw.isdigit():  # 예: 20250407
                        y, m, d = int(raw[:4]), int(raw[4:6]), int(raw[6:])
                        test_fmt = f"{y}년 {m}월 {d}일"

        except Exception:
            pass

        # 이름 최종 조합
        name_full = f"{name} ({gender}, {age})" if name and gender and age else f"{name} ({gender})"

        info.update({
            "이름": name_full,
            "성별": gender,
            "나이": age,
            "생년월일": "",
            "검사일자": test_fmt,
            "교육": "",
            "실시검사": test_name
        })

    return info

def extract_all_pdfs(folder_path="."):
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    results = [extract_info(pdf) for pdf in pdf_files]
    df = pd.DataFrame(results)

    # # ✅ 표 출력
    # print(df)
    #
    # # ✅ 엑셀 저장
    # output_file = Path(folder_path) / "pdf_extraction_result.xlsx"
    # df.to_excel(output_file, index=False)
    # print(f"\n✅ 엑셀 저장 완료: {output_file}")
    return df

# ✅ 실행

if __name__ == "__main__":
    extract_all_pdfs("C:/Users/HATAE/Downloads/PythonProject2")
