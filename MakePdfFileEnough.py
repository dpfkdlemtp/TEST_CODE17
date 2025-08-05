# -*- coding: utf-8 -*-

import streamlit as st
from pathlib import Path
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import HexColor
from math import pi, cos, sin
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from math import sin, cos, pi, exp
from reportlab.lib.colors import HexColor, red, white, black
from math import sin, cos, pi
import numpy as np
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT


from collections import defaultdict, Counter
from 검사자정보추출 import extract_info
from pathlib import Path


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

def merge_examiner_info_from_files(file_objs: list) -> tuple[dict, list]:
    from collections import defaultdict, Counter
    from 검사자정보추출 import extract_info

    field_values = defaultdict(list)
    for file_obj in file_objs:
        path = file_obj["path"]
        original_name = file_obj["original_name"]
        info = extract_info(path, original_name)
        info["파일명"] = original_name

        for field in ["이름", "성별", "나이", "생년월일", "검사일자", "교육", "실시검사"]:
            value = info.get(field, "").strip()
            if value:
                field_values[field].append(value)

    merged = {}
    warnings = []

    for field, values in field_values.items():
        if field == "실시검사":
            all_tests = []
            for v in values:
                all_tests.extend([x.strip() for x in v.split(",") if x.strip()])
            merged[field] = ", ".join(sorted(set(all_tests)))
            continue

        counter = Counter(values)
        most_common = counter.most_common()

        if len(most_common) == 1 or most_common[0][1] > most_common[1][1]:
            merged[field] = most_common[0][0]
        else:
            merged[field] = most_common[0][0]
            warnings.append(f"⚠️ [{field}] 필드에 여러 다른 값이 동일 빈도로 추출되었습니다: {dict(counter)}")

    for field in ["이름", "성별", "나이", "생년월일", "검사일자", "교육", "실시검사"]:
        if field not in merged:
            merged[field] = ""

    return merged, warnings


def generate_full_pdf(output_path="goodenough_full_report.pdf", input_pdf_paths=None, manual_info=None, wechsler_data=None,TCI_scores=None,PAT_scores=None):
    width, height = A4

    # 📌 Pretendard 폰트 등록 (경로를 환경에 맞게 수정)
    pdfmetrics.registerFont(TTFont('Pretendard-Bold', 'fonts/Pretendard-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Pretendard-SemiBold', 'fonts/Pretendard-SemiBold.ttf'))
    pdfmetrics.registerFont(TTFont('Pretendard-Regular', 'fonts/Pretendard-Regular.ttf'))

    c = canvas.Canvas(output_path, pagesize=A4)

    def draw_multiline_text(c, x, y, text, max_width, line_height=10, font_size=9, font_name="Pretendard-SemiBold"):
        c.setFont(font_name, font_size)
        c.setFillColor(HexColor("#000000"))

        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if stringWidth(test_line, font_name, font_size) <= max_width:
                    line = test_line
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
            lines.append("")  # paragraph space

        for i, line in enumerate(lines):
            c.drawString(x, y - i * line_height, line)

    ## PAGE 0 표지

    c.setFillColor(HexColor("#D3F6B3"))  # 연두색 배경
    c.rect(0, 0, width, height * 0.55, fill=1, stroke=0)

    # ✅ 초록색 막대 제거 → 로고 삽입
    try:

        # 현재 스크립트와 동일한 디렉토리의 logo.png 경로 지정
        logo = Path(__file__).parent / "logo.png"
        # 왼쪽 상단(초록색 바가 있던 위치)에 로고 배치
        c.drawImage(logo, 60, height - 120, width=70, height=70, mask='auto')
    except:
        print("⚠️ 로고 이미지를 불러오지 못했습니다. 경로를 확인하세요.")

    c.setFont("Pretendard-Bold", 54)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 190, "굿이너프")
    c.drawString(60, height - 250, "심리검사보고서")

    c.setFont("Pretendard-Regular", 14)
    c.setFillColor(HexColor("#333333"))
    c.drawString(60, height - 300, "Good Enough")
    c.drawString(60, height - 320, "Psychological Assessment report")

    c.showPage()

    ## PAGE 1 목차

    try:
        # 현재 스크립트와 동일한 디렉토리의 logoBack.png 경로 지정
        logoBack = Path(__file__).parent / "logoBack.png"
        # 배경 로고: 페이지 중앙에 반투명하게 배치
        # 실제 투명 처리는 ReportLab에서 직접 안 되므로, 미리 투명 처리된 PNG 사용
        logo_width = 300
        logo_height = 300
        c.drawImage(
            logoBack,
            (width - logo_width) / 2,
            (height - logo_height) / 2,
            width=logo_width,
            height=logo_height,
            mask='auto'
        )
    except:
        print("⚠️ 로고 배경 이미지를 불러오지 못했습니다. 경로를 확인하세요.")
    
    # 상단 연두색 줄
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)

    # 좌측 상단 제목
    c.setFont("Pretendard-SemiBold", 36)
    c.setFillColor(HexColor("#3DB419"))
    c.drawString(60, height - 80, "Report")
    c.drawString(60, height - 115, "Contents")

    # 항목 데이터
    items = [
        ("01", "웩슬러 지능검사", "Korean-Wechsler Intelligence Scale"),
        ("02", "기질 및 성격검사", "Temperament and Character Inventory"),
        ("03", "부모 양육태도 검사", "Parenting Attitude Test – Second Edition"),
    ]

    y = height - 350

    # 구분선 (최상단)
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1.5)
    c.line(170, y + 120, width - 60, y + 120)

    for num, title_kor, title_eng in items:
        # 번호 (투톤)
        c.setFont("Pretendard-SemiBold", 50)
        c.setFillColor(HexColor("#32CD32"))
        c.drawString(180, y+50, num)

        c.setFillColor(HexColor("#BFBFBF"))
        c.drawString(180, y+50, num[0])  # 첫 글자만 초록

        # 제목
        c.setFont("Pretendard-Bold", 32)
        c.setFillColor(HexColor("#000000"))
        c.drawString(180, y, title_kor)

        # 부제목
        c.setFont("Pretendard-Regular", 10)
        c.setFillColor(HexColor("#666666"))
        c.drawString(180, y - 22, title_eng)

        # 구분선 (아래쪽)
        c.setStrokeColor(HexColor("#DDDDDD"))
        c.setLineWidth(1.5)
        c.line(170, y - 50, width - 60, y - 50)

        y -= 160  # 다음 항목 위치

    # 하단 페이지 번호
    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "01")

    c.showPage()

    # --- ✅ 3페이지: 심리검사 소개 ---
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)

    # 제목
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 100, "심리검사 소개")

    sections = [
        {
            "title": " 웩슬러 지능검사",
            "content": (
                "웩슬러 지능검사는 개인의 인지기능을 평가하는 가장 공신력 있는 검사입니다.<br/>"
                "전체지능(FSIQ)뿐만 아니라 언어적 능력과 비언어적 능력, 작업기억력과 정보처리속도 등<br/>"
                "인지기능을 구성하는 세부적인 영역 각각에 대해 심층적으로 평가합니다.<br/>"
                "개인의 인지기능이 동일 연령 집단과 비교해 어느 위치에 있는지를 직관적으로 파악할 수 있으며<br/>"
                "개인의 고유한 강점과 약점에 대한 분석도 가능합니다.<br/>"
                "지능 프로파일을 토대로 아동은 학습 방향을 설정하고 적성을 계발할 수 있으며,<br/>"
                "성인의 경우에는 적합한 직무에 대한 의사결정을 할 수 있습니다."
            )
        },
        {
            "title": " TCI 기질 및 성격검사",
            "content": (
                "TCI 기질 및 성격검사는 개인의 선천적인 기질과 후천적으로 발달된 성격을 평가하는 검사입니다.<br/>"
                "외부 환경에 대한 자동적 정서반응인 기질과, 이러한 반응을 조율하는 성격을 포괄적으로로 평가하며,<br/>"
                "이러한 요인들이 어떻게 상호작용하면서 개인의 행동으로 나타나는지 분석합니다.<br/>"
                "기질에 가장 적합한 환경을 조성하고, 미흡한 성격 특성은 어떻게 발달시켜야 할 지 파악할 수 있습니다.<br/>"
            )
        },
        {
            "title": " PAT-2 부모 양육태도검사",
            "content": (
                "PAT-2 부모 양육태도검사는 양육의 핵심적인 8가지 차원에서 현재의 수준을 평가하는 검사입니다.<br/>"
                "각각의 차원이 아이의 정서 및 사회성 발달에 어떠한 영향을 미치는지 이해하고, <br/>"
                "현재 이상적인 양육은 유지하되, 과도하거나 미흡한 영역을 조율하여 최적의<br/>"
                "양육환경을 조성하도록 유도합니다. 또한 PAT-2 부모 양육태도검사는 일정한 간격을 두고<br/>"
                "재시행함으로써 양육태도의 개선 여부를 관찰하기 용이합니다."
            )
        }
    ]

    style_content = ParagraphStyle(
        name="content",
        fontName="Pretendard-SemiBold",
        fontSize=11.5,
        leading=24,
        textColor=HexColor("#000000"),
        alignment=TA_LEFT
    )

    y = height - 160
    cnt = 1
    for section in sections:
        # ✅ 회색 박스 배경
        c.setFillColor(HexColor("#F4F4F4"))
        c.rect(60, y - 10, width - 120, 30, fill=1, stroke=0)

        # ✅ 초록 세로 바
        c.setFillColor(HexColor("#80d167"))
        c.rect(60, y - 10, 5, 30, fill=1, stroke=0)

        # ✅ 제목
        c.setFont("Pretendard-Bold", 16)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(70, y, section["title"])

        # ✅ 본문 (Frame 높이 수정 → 글자 잘림 방지)
        para = Paragraph(section["content"], style_content)
        if cnt==1:
            text_height = 180  # 각 내용 박스 높이 (길이에 따라 늘리세요)
        elif cnt==2:
            text_height = 120  # 각 내용 박스 높이 (길이에 따라 늘리세요)
        else:
            text_height = 150  # 각 내용 박스 높이 (길이에 따라 늘리세요)
        cnt+=1
        frame = Frame(60, y - text_height - 20, width - 120, text_height, showBoundary=0)
        frame.addFromList([para], c)

        y -= text_height + 60  # 다음 박스로 이동

    # ✅ 페이지 번호
    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "02")

    c.showPage()

    ## PAGE 3 수검자 정보 및 검사태도 ---

    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)

    # 상단 제목
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 70, "수검자 정보 및 검사태도")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 90, width - 60, height - 90)

    # ✅ "수검자 정보" 소제목 (왼쪽 초록바)
    c.setFillColor(HexColor("#80D167"))
    c.rect(62, height - 130, 3, 16, fill=1, stroke=0)

    c.setFont("Pretendard-Bold", 16)
    c.setFillColor(HexColor("#000000"))
    c.drawString(70, height - 127, "수검자 정보")

    # ✅ 검사자 정보 추출
    merged_info = manual_info
    warn_msgs = []
    # input_pdf_paths = "C:/Users/HATAE/Downloads/PythonProject2\info_data"
    # if manual_info:
    #     merged_info = manual_info
    #     warn_msgs = []
    # elif input_pdf_paths:
    #     merged_info, warn_msgs = merge_examiner_info_from_files(input_pdf_paths)
    # else:
    #     merged_info, warn_msgs = merge_examiner_info_from_pdfs(input_pdf_paths)

    # print("🔎 통합 정보:")
    # for k, v in merged_info.items():
    #     print(f"{k}: {v}")
    #
    # if warn_msgs:
    #     print("\n🚨 경고:")
    #     for w in warn_msgs:
    #         print(w)

    # ✅ 검사자 정보 테이블
    table_data = [
        ["이름 (성별·연령)", merged_info["이름"], "생년월일", merged_info["생년월일"]],
        ["검사일자", merged_info["검사일자"], "교육", merged_info["교육"]],
        ["실시검사", merged_info["실시검사"], "", ""],
    ]

    table = Table(
        table_data,
        colWidths=[100, 150, 80, 130],  # ✅ 3열(교육) 크기를 조금 키움
        rowHeights=[28, 28, 28]
    )

    table.setStyle(TableStyle([
        # ✅ 폰트 스타일
        ("FONTNAME", (0, 0), (0, -1), "Pretendard-Bold"),  # 질문 1열
        ("FONTNAME", (2, 0), (2, -2), "Pretendard-Bold"),  # 질문 3열 (마지막 행 제외)
        ("FONTNAME", (1, 0), (1, -1), "Pretendard-SemiBold"),  # 답변 2열
        ("FONTNAME", (3, 0), (3, -2), "Pretendard-SemiBold"),  # 답변 4열 (마지막 행 제외)
        ("FONTNAME", (1, -1), (3, -1), "Pretendard-SemiBold"),  # 마지막 행 답변

        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#000000")),

        # ✅ 질문칸 색상
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#E0F4DA")),  # 1열
        ("BACKGROUND", (2, 0), (2, -2), HexColor("#E0F4DA")),  # 3열

        # ✅ 답변칸 색상
        ("BACKGROUND", (1, 0), (1, -1), HexColor("#F7FBF5")),  # 2열
        ("BACKGROUND", (3, 0), (3, -2), HexColor("#F7FBF5")),  # 4열
        ("BACKGROUND", (1, -1), (3, -1), HexColor("#F7FBF5")),  # 마지막 행 병합 영역

        # ✅ 마지막 행(2,3,4열 합치기)
        ("SPAN", (1, 2), (3, 2)),

        # ✅ 행 사이 여백 효과
        ("LINEBELOW", (0, 0), (-1, -1), 2.5, HexColor("#FFFFFF")),  # 얇은 흰색 라인

        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 60, height - 240)

    # 1. 제목: "검사 태도"
    c.setFillColor(HexColor("#80D167"))
    c.rect(62, height - 300, 3, 16, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 16)
    c.setFillColor(HexColor("#000000"))
    c.drawString(70, height - 297, "검사 태도")

    # 2. 회색 박스
    box_x = 60
    box_y = height - 740
    box_width = width - 120
    box_height = 410
    c.setFillColor(HexColor("#F5F5F5"))
    c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

    # 3. 텍스트 삽입
    summary_text = manual_info.get("검사태도") or "※ 검사태도에 대한 정보가 입력되지 않았습니다."

    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_width = 450

    draw_multiline_text(c, box_x + 20, box_y + 390, summary_text, max_width=text_width, font_size=11)

    # ✅ 페이지 번호
    # ✅ 페이지 번호
    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "03")

    c.showPage()

    ##########
    ## PAGE 04 지능검사 요약

    def draw_score_bars(c, base_x, base_y, gray_value, green_value):
        """
        회색(기준값: 116)과 초록색(가변값) 막대 그래프 그리기
        - base_x, base_y: 그래프 기준 좌측 하단 좌표
        - green_value: 초록 막대 값 (예: 105 ~ 130)
        """

        max_height = 80  # 기준값 116에 해당하는 픽셀 높이
        bar_width = 20
        spacing = 15

        # 비율 계산
        def calc_height(score):
            return max_height * (score / 116)

        gray_height = calc_height(gray_value)
        green_height = calc_height(green_value)

        # 좌표 설정
        gray_x = base_x
        green_x = base_x + bar_width + spacing

        # --- 회색 막대 ---
        c.setFillColor(HexColor("#B3B3B3"))
        c.rect(gray_x, base_y, bar_width, gray_height, fill=1, stroke=0)

        # 회색 점수 텍스트
        c.setFillColor(HexColor("#B3B3B3"))
        c.setFont("Pretendard-Regular", 11)
        c.drawCentredString(gray_x + bar_width / 2, base_y + gray_height + 5, str(gray_value))

        # --- 초록 막대 ---
        c.setFillColor(HexColor("#80D167"))
        c.rect(green_x, base_y, bar_width, green_height, fill=1, stroke=0)

        # 초록 점수 텍스트
        c.setFillColor(HexColor("#80D167"))
        c.drawCentredString(green_x + bar_width / 2, base_y + green_height + 5, str(green_value))

    def draw_badge(c, x, y, r, color, text="15"):
        """
        각진 듯 둥근 톱니형 배지 그리기 (디자인 참고 반영)
        """
        num_spikes = 10
        r_outer = r
        r_inner = r * 0.75  # 톱니 강조를 위한 차이 유지
        spike_roundness = 0.3  # 0~1, 곡선 부드러움 조절

        points = []
        for i in range(num_spikes * 2):
            angle = i * pi / num_spikes
            radius = r_outer if i % 2 == 0 else r_inner
            px = x + radius * cos(angle)
            py = y + radius * sin(angle)
            points.append((px, py))

        path = c.beginPath()

        for i in range(len(points)):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]

            # 중간점과 컨트롤 포인트
            mx1 = p0[0] + (p1[0] - p0[0]) * spike_roundness
            my1 = p0[1] + (p1[1] - p0[1]) * spike_roundness
            mx2 = p2[0] + (p1[0] - p2[0]) * spike_roundness
            my2 = p2[1] + (p1[1] - p2[1]) * spike_roundness

            if i == 0:
                path.moveTo(mx1, my1)

            path.curveTo(p1[0], p1[1], p1[0], p1[1], mx2, my2)

        path.close()
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.drawPath(path, fill=1, stroke=0)

        # 텍스트
        c.setFillColor("white")
        font_size = r * 0.7
        c.setFont("Pretendard-Bold", font_size)
        text_width = c.stringWidth(text, "Pretendard-Bold", font_size)
        c.drawString(x - text_width / 2 - 10, y - font_size * 0.35, text)
        c.setFont("Pretendard-Bold", font_size - 15)
        text_width = c.stringWidth(text, "Pretendard-Bold", font_size)
        c.drawString(x + 10, y - font_size * 0.35, "%")

    def draw_circle_gauge(c, x, y, radius, value, max_value=150, color=HexColor("#80D167")):
        """원형 게이지"""
        # 회색 배경 원
        c.setLineWidth(8)
        c.setStrokeColor(HexColor("#EAEAEA"))
        c.circle(x, y, radius, stroke=1, fill=0)
        # 초록색 게이지
        c.setStrokeColor(color)
        angle = 360 * int(value) / max_value
        c.arc(x - radius, y - radius, x + radius, y + radius, startAng=90, extent=-angle)
        # 중앙 숫자
        c.setFont("Pretendard-SemiBold", 32)
        c.setFillColor(color)
        c.drawCentredString(x, y - 11, str(value))

    def draw_wechsler_page(c, fsiq, percentile, strength_label, strength_score, weakness_label, weakness_score,
                           sub_scores, ci_min, ci_max):
        width, height = A4
        c.setFillColor(HexColor("#D3F6B3"))
        c.rect(0, height - 15, width, 15, fill=1, stroke=0)

        # 제목
        c.setFont("Pretendard-Bold", 28)
        c.setFillColor(HexColor("#000000"))
        c.drawString(60, height - 90, "웩슬러 지능검사")
        c.setFont("Pretendard-SemiBold", 12)
        c.setFillColor(HexColor("#555555"))
        c.drawString(250, height - 90, "Korean-Wechsler Intelligence Scale")

        # ✅ 구분선
        c.setStrokeColor(HexColor("#DDDDDD"))
        c.setLineWidth(1)
        c.line(60, height - 110, width - 60, height - 110)

        # 박스 그리기 함수
        def draw_box(x, y, w, h):
            c.setFillColor(HexColor("#FAFAFA"))  # 연한 회색 배경
            c.roundRect(x, y, w, h, 10, fill=1, stroke=0)
            c.setStrokeColor(HexColor("#E6E6E6"))
            c.setLineWidth(0.8)
            c.roundRect(x, y, w, h, 10, fill=0, stroke=1)

        # 1. 전체 지능 지수
        draw_box(65, height - 320, 215, 185)
        c.setFont("Pretendard-Bold", 20)
        c.setFillColor(HexColor("#000000"))
        c.drawString(110, height - 165, "전체 지능 지수")
        c.setFont("Pretendard-Regular", 12)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(130, height - 185, f"FSIQ {fsiq} [우수]")
        c.setStrokeColor(HexColor("#DDDDDD"))
        c.setLineWidth(1)
        c.line(80, height - 195, 265, height - 195)
        draw_circle_gauge(c, 170, height - 260, 45, fsiq)

        # 2. 지능 백분위
        draw_box(315, height - 320, 215, 185)
        c.setFont("Pretendard-Bold", 20)
        c.setFillColor(HexColor("#000000"))
        c.drawString(370, height - 165, "지능 백분위")
        c.setFont("Pretendard-Regular", 12)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(350, height - 185, "동일 연령 집단 100명 중 상위")
        c.setLineWidth(1)
        c.line(335, height - 195, 510, height - 195)
        draw_badge(c, x=420, y=height - 257, r=45, color=HexColor("#80D167"), text=str(percentile))

        # # 3. 인지적 강점
        draw_box(65, height - 530, 215, 185)
        c.setFont("Pretendard-Bold", 20)
        c.setFillColor(HexColor("#000000"))
        c.drawString(120, height - 370, "인지적 강점")

        c.setFont("Pretendard-Regular", 12)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(119, height - 390, str(strength_label)+" ["+score_category[strength_label[:4]] + "]")
        # c.drawString(135, height - 390, str(strength_label))

        c.setLineWidth(1)
        c.line(80, height - 400, 265, height - 400)

        # 인지적 강점 그래프
        draw_score_bars(c, base_x=140, base_y=height - 515, gray_value=int(fsiq), green_value=int(strength_score))

        # 4. 인지적 약점
        draw_box(315, height - 530, 215, 185)
        c.setFont("Pretendard-Bold", 20)
        c.setFillColor(HexColor("#000000"))
        c.drawString(370, height - 370, "인지적 약점")

        c.setFont("Pretendard-Regular", 12)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(369, height - 390, str(weakness_label)+" ["+score_category[weakness_label[:4]] + "]")
        #c.drawString(385, height - 390, str(weakness_label))

        c.setLineWidth(1)
        c.line(335, height - 400, 510, height - 400)

        # 인지적 약점 그래프
        draw_score_bars(c, base_x=390, base_y=height - 515, gray_value=int(fsiq), green_value=int(weakness_score))

        # 5. 세부 항목별 순위

        def draw_percentile_bars(c, x, y, sub_scores):
            draw_box(65, height - 740, 215, 185)
            c.setFont("Pretendard-Bold", 20)
            c.setFillColor(HexColor("#000000"))
            c.drawString(100, height - 585, "세부 항목별 백분위")
            c.setFont("Pretendard-Regular", 12)
            c.setFillColor(HexColor("#3DB419"))
            c.drawString(103, height - 605, "동일 연령 집단 100명 중 상위")

            c.setLineWidth(1)
            c.line(80, height - 615, 265, height - 615)

            y_bar = y + 100
            bar_total_width = 85

            for k, v in sub_scores.items():
                c.setFont("Pretendard-Bold", 12)
                c.setFillColor(HexColor("#666666"))
                c.drawString(x + 15, y_bar, f"{k}")

                # 회색 바 배경
                c.setFillColor(HexColor("#DDDDDD"))
                c.rect(x + 70, y_bar, bar_total_width, 10, fill=1, stroke=0)

                # 초록 막대: 높은 점수일수록 짧아야 함
                green_width = bar_total_width * (1 - v / 100)
                c.setFillColor(HexColor("#3DB419"))
                c.rect(x + 70, y_bar, green_width, 10, fill=1, stroke=0)

                # 오른쪽 % 텍스트
                c.setFont("Pretendard-SemiBold", 10)
                c.drawRightString(x + 75 + bar_total_width + 26, y_bar+2, f"{v}%")

                y_bar -= 22

        # draw_box(90, height - 750, 215, 185)
        draw_percentile_bars(c, x=65, y=height - 740, sub_scores=sub_scores)

        # 6. 신뢰구간

        def draw_normal_curve(c, x, y, w, h, ci_min, ci_max, mean=100, std=15, y_offset=10):
            """
            바닥선에서 정규분포를 띄워 그리고, 오프셋 아래 부분도 색으로 꽉 채움
            """
            import numpy as np
            from math import exp

            # 바닥선
            c.setStrokeColor(HexColor("#666666"))
            c.setLineWidth(1.5)
            c.line(x, y, x + w, y)

            # 곡선 좌표 계산 (y_offset 적용)
            iq_range = np.linspace(mean - 3 * std, mean + 3 * std, 101)
            points = []
            for i, iq in enumerate(iq_range):
                px = x + i * (w / 100)
                py = y + y_offset + h * exp(-((iq - mean) / std) ** 2)
                points.append((px, py))

            # 전체 회색 영역 (곡선부터 y까지)
            path_bg = c.beginPath()
            path_bg.moveTo(points[0][0], y)  # 바닥선에서 시작
            for px, py in points:
                path_bg.lineTo(px, py)
            path_bg.lineTo(points[-1][0], y)
            path_bg.close()
            c.setFillColor(HexColor("#DBDBDB"))
            c.drawPath(path_bg, fill=1, stroke=0)

            # 신뢰구간 연두색 영역 (곡선부터 y까지)
            ci_points = [(px, py) for (px, py), iq in zip(points, iq_range) if ci_min <= iq <= ci_max]
            if ci_points:
                path_ci = c.beginPath()
                path_ci.moveTo(ci_points[0][0], y)
                for px, py in ci_points:
                    path_ci.lineTo(px, py)
                path_ci.lineTo(ci_points[-1][0], y)
                path_ci.close()
                c.setFillColor(HexColor("#A3DD93"))
                c.drawPath(path_ci, fill=1, stroke=0)

            # 외곽선 곡선
            path_line = c.beginPath()
            path_line.moveTo(points[0][0], points[0][1])
            for px, py in points[1:]:
                path_line.lineTo(px, py)
            c.setStrokeColor(HexColor("#DBDBDB"))
            c.setLineWidth(1)
            c.drawPath(path_line, fill=0, stroke=1)

        draw_box(315, height - 740, 215, 185)
        c.setFont("Pretendard-Bold", 20)
        c.setFillColor(HexColor("#000000"))
        c.drawString(380, height - 585, "신뢰구간")

        c.setFont("Pretendard-Regular", 12)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(379, height - 605, " 신뢰구간 범위")

        c.setLineWidth(1)
        c.line(335, height - 615, 510, height - 615)

        draw_normal_curve(
            c,
            x=330, y=height - 690, w=180, h=50,
            ci_min=ci_min, ci_max=ci_max,
            y_offset=10  # 바닥에서 살짝 띄움
        )

        # 텍스트 출력
        c.setFont("Pretendard-Bold", 20)
        c.setFillColor(HexColor("#3DB419"))
        c.drawCentredString(420, height - 720, str(ci_min)+"~"+str(ci_max))

        # 페이지 번호
        # ✅ 페이지 번호
        c.setFont("Pretendard-Bold", 9)
        c.setFillColor(HexColor("#535353"))
        c.drawRightString(width - 60, 40, "굿이너프")

        c.setFont("Pretendard-Regular", 9)
        c.setFillColor(HexColor("#A9A9A9"))
        c.drawRightString(width - 47.5, 40, "04")

    #########
    ## PAGE 04 지능검사 요약 호출
    fsiq = wechsler_data["fsiq"]
    percentile = wechsler_data["percentile"]
    strength_label = wechsler_data["strength_label"]
    strength_score = wechsler_data["strength_score"]
    weakness_label = wechsler_data["weakness_label"]
    weakness_score = wechsler_data["weakness_score"]
    sub_scores = wechsler_data["sub_scores"]
    ci_min = wechsler_data["ci_min"]
    ci_max = wechsler_data["ci_max"]
    diagnosis_labels = wechsler_data["diagnosis_labels"]
    subtest_scores = wechsler_data["subtest_scores"]
    index_scores_all = wechsler_data.get("index_scores_all", {})
    IntelligenceDomain = wechsler_data["IntelligenceDomain"]
    final_summary = wechsler_data["final_summary"]

    if wechsler_data:
        draw_wechsler_page(
            c,
            fsiq=fsiq,
            percentile=percentile,
            strength_label=strength_label,
            strength_score=strength_score,
            weakness_label=weakness_label,
            weakness_score=weakness_score,
            sub_scores=sub_scores,
            ci_min=ci_min,
            ci_max=ci_max
        )
    else:
        draw_wechsler_page(
            c,
            fsiq=0,
            percentile=0,
            strength_label="",
            strength_score=0,
            weakness_label="",
            weakness_score=0,
            sub_scores={"언어이해": 10, "시공간": 15, "유동추론": 20, "작업기억": 23, "처리속도": 18},
            ci_min=1,
            ci_max=2
        )
    c.showPage()

    ###############################
    ## PAGE 05 지능검사 요약 2
    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "웩슬러 지능검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Korean-Wechsler Intelligence Scale")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    # 설명 박스
    c.setFillColor(HexColor("#DDF5D4"))
    c.rect(60, height - 160, width - 120, 28, fill=1, stroke=0)
    c.setFillColor(HexColor("#000000"))
    c.setFont("Pretendard-Bold", 9)
    c.drawString(95, height - 150, f"지능검사 결과, 전체 지능지수(FSIQ)는 {fsiq}, [{diagnosis_labels['전체IQ']}] 수준입니다. 동일 연령 집단 100명 중 상위 {percentile}%에 해당합니다.")

    # ✅ "지능지수 백분위 분포 그래프" 소제목 (왼쪽 초록바)
    c.setFillColor(HexColor("#80D167"))
    c.rect(62, height - 178, 3, 10, fill=1, stroke=0)

    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(70, height - 175, "지능지수 백분위 분포 그래프")

    # 정규분포 그리기
    def draw_normal_curve_2(c, x, y, w, h, score=116):
        import numpy as np
        from math import exp

        mean, std = 100, 15
        iq_range = np.linspace(mean - 3 * std, mean + 3 * std, 300)
        y_offset = 20

        # 폰트 지정
        title_font = "Pretendard-Bold"
        regular_font = "Pretendard-Regular"

        # 정규분포 곡선 좌표
        points = [(x + (iq - 55) / (90) * w,
                   y + y_offset + h * exp(-((iq - mean) ** 2) / (2 * std ** 2)))
                  for iq in iq_range]

        # 구간 설정
        sections = [
            (55, 70, "매우 낮음", "2.2%"),
            (70, 80, "낮음", "6.7%"),
            (80, 90, "평균 하", "16.1%"),
            (90, 110, "평균", "50%"),
            (110, 120, "평균 상", "16.1%"),
            (120, 130, "우수", "6.7%"),
            (130, 145, "매우 우수", "2.2%"),
        ]
        colors = ["#D8F1D1", "#BFE8B3", "#A6DF95", "#80D167", "#A6DF95", "#BFE8B3", "#D8F1D1"]

        for i, (start_iq, end_iq, label, percent) in enumerate(sections):
            start_x = x + (start_iq - 55) / 90 * w
            end_x = x + (end_iq - 55) / 90 * w

            # 정규분포 함수 (y 값 계산용)
            def gaussian_y(iq_val):
                return y + y_offset + h * exp(-((iq_val - mean) ** 2) / (2 * std ** 2))

            zone_pts = [(x + (iq - 55) / 90 * w, gaussian_y(iq)) for iq in iq_range if start_iq <= iq <= end_iq]

            # ✅ 시작/끝 곡선 좌표 강제 추가
            zone_pts.insert(0, (start_x, gaussian_y(start_iq)))
            zone_pts.append((end_x, gaussian_y(end_iq)))

            # 영역 채우기
            path = c.beginPath()
            path.moveTo(start_x, y)  # 왼쪽 아래
            for px, py in zone_pts:
                path.lineTo(px, py)  # 곡선 위
            path.lineTo(end_x, y)  # 오른쪽 아래
            path.close()

            c.setFillColor(HexColor(colors[i]))
            c.drawPath(path, fill=1, stroke=0)

            # 라벨 (구간명)
            mid_x = (start_x + end_x) / 2
            c.setFont(title_font, 8)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(mid_x, y + h + y_offset + 16, label)

            # 백분위
            c.setFont(title_font, 8)
            c.drawCentredString(mid_x, y + 7, percent)

            # 점선
            if i > 0:
                c.setStrokeColor(HexColor("#66BB6A"))
                c.setDash(1, 2)
                c.setLineWidth(0.6)
                c.line(start_x, y, start_x, y + h + y_offset + 22)
                c.setDash()

        # 바닥선
        c.setStrokeColor(HexColor("#7F7F7F"))
        c.setLineWidth(1)
        c.line(x, y, x + w, y)

        # x축 숫자 라벨
        x_labels = [0, 70, 80, 90, 110, 120, 130]
        for val in x_labels:
            if val == 0:
                c.setFont(regular_font, 6)
                c.setFillColor(HexColor("#000000"))
                c.drawCentredString(x, y - 12, str(val))
            px = x + (val - 55) / 90 * w
            c.setFont(regular_font, 6)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(px, y - 12, str(val))

        # 빨간 점선 (score 기준)
        score_x = x + (score - 55) / 90 * w
        score_y = y + y_offset + h * exp(-((score - mean) ** 2) / (2 * std ** 2))

        c.setDash(1, 2)
        c.setStrokeColor(HexColor("#FF3B30"))
        c.setLineWidth(1)
        c.line(score_x, y, score_x, score_y)
        c.line(x, score_y, score_x, score_y)
        c.setDash()

        # 흰색 원 + 빨간 테두리
        c.setFillColor(red)
        c.circle(score_x, score_y, 3, fill=1, stroke=0)
        c.setFillColor(white)
        c.circle(score_x, score_y, 2, fill=1, stroke=0)

        # 점수 텍스트
        # 빨간 점수 박스
        score_text = str(score)
        c.setFont(title_font, 9)
        text_width = c.stringWidth(score_text, title_font, 9)
        box_width = text_width + 6
        box_height = 12
        c.setFillColor(red)
        c.roundRect(score_x - box_width / 2, score_y + 10, box_width, box_height, 2, fill=1, stroke=0)
        c.setFillColor(white)
        c.drawCentredString(score_x, score_y + 12, score_text)

        # ✅ Y축 (좌/우) 실선 추가
        c.setStrokeColor(HexColor("#7F7F7F"))
        c.setLineWidth(1)
        c.line(x, y, x, y + h + y_offset + 25)  # 왼쪽 Y축
        c.line(x + w, y, x + w, y + h + y_offset + 25)  # 오른쪽 Y축

    draw_normal_curve_2(c, 65, height - 315, 460, 80, int(fsiq))

    # ✅ "지능지수 백분위 분포 그래프" 소제목 (왼쪽 초록바)
    c.setFillColor(HexColor("#80D167"))
    c.rect(62, height - 348, 3, 10, fill=1, stroke=0)

    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(70, height - 345, "지표별 주요 지능지수 점수")

    ##
    def draw_main_iq_bar_chart(c, x, y, width, scores):
        labels = list(scores.keys())
        max_score = 160
        bar_height = 10
        spacing = 30
        row_count = len(scores)

        label_area_width = 70
        label_area_x = x - label_area_width
        chart_height = row_count * spacing

        # ✅ 1. 점선 (흰배경 포함 전체 선 먼저)
        for tick in range(20, max_score + 1, 20):
            tick_x = x + (tick / max_score) * width
            c.setStrokeColor(HexColor("#AAAAAA"))  # 더 진하게
            c.setDash(1, 2)
            c.setLineWidth(0.4)
            c.line(tick_x, y - chart_height + bar_height, tick_x, y + bar_height)

        c.setDash()  # 점선 해제

        # ✅ 2. 회색 배경 (라벨 영역 포함)
        for i in range(row_count):
            y_pos = y - i * spacing
            c.setFillColor(HexColor("#EFEFEF"))
            c.rect(label_area_x, y_pos, width + label_area_width, bar_height, fill=1, stroke=0)

        # ✅ 3. 테두리 (상단 제외)
        c.setStrokeColor(HexColor("#888888"))
        c.setLineWidth(0.8)
        c.line(label_area_x, y - chart_height + bar_height, label_area_x, y + bar_height)
        c.line(x + width, y - chart_height + bar_height, x + width, y + bar_height)
        c.line(label_area_x, y - chart_height + bar_height, x + width, y - chart_height + bar_height)

        # ✅ 4. 막대 그래프 및 텍스트
        for i, (label, score) in enumerate(scores.items()):
            y_pos = y - i * spacing
            bar_width = (score / max_score) * width

            # 막대 색
            bar_color = HexColor("#80D167") if label.startswith("전체 지능") else HexColor("#C3F7B3")
            c.setFillColor(bar_color)
            c.rect(x, y_pos, bar_width, bar_height, fill=1, stroke=0)

            # ✅ 라벨 중앙 정렬 (왼쪽 y축과 막대 사이)
            c.setFillColor(HexColor("#000000"))
            c.setFont("Pretendard-Bold", 7)
            label_center_x = label_area_x + label_area_width / 2
            c.drawCentredString(label_center_x, y_pos + 3, label)

            # 점수 (막대 우측)
            c.setFillColor(HexColor("#3DB419"))
            c.setFont("Pretendard-Bold", 7)
            c.drawString(x + bar_width + 3, y_pos + 2, str(score))

        # ✅ 5. 숫자 눈금
        c.setFillColor(HexColor("#000000"))
        for tick in range(0, max_score + 1, 20):
            tick_x = x + (tick / max_score) * width
            c.setFont("Pretendard-Regular", 6)
            c.drawCentredString(tick_x, y - chart_height + bar_height - 12, str(tick))

    # 변환 및 정렬
    converted_scores = {}

    # 1. 전체 지능 먼저
    if "전체IQ" in index_scores_all:
        v = index_scores_all["전체IQ"]
        label = score_category["전체IQ"]
        converted_scores[f"전체 지능 ({label})"] = v

    # 2. 나머지 항목
    for k, v in index_scores_all.items():
        if k == "전체IQ":
            continue
        label = score_category.get(k)
        if label:
            converted_scores[f"{k} ({label})"] = v


    draw_main_iq_bar_chart(c, x=135, y=height - 375, width=390, scores=converted_scores)

    ##
    # ✅ "지능지수 백분위 분포 그래프" 소제목 (왼쪽 초록바)
    c.setFillColor(HexColor("#80D167"))
    c.rect(62, height - 580, 3, 10, fill=1, stroke=0)

    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(70, height - 577, "하위검사 점수 분포")


    # 하위검사 점수
    def draw_subtest_scores_final(c, domains, subtests, x, y):

        # 시각 요소
        bar_width = 10
        bar_gap = 30
        bar_unit = 9
        max_score = 19
        chart_height = max_score * bar_unit
        domain_label_margin = 19
        full_chart_height = chart_height + domain_label_margin

        label_x = x - 40  # 라벨 왼쪽까지 포함하는 영역

        ori_x = x
        # ✅ 3. 도메인명
        for i, (domain, idx_range) in enumerate(domains.items()):
            if i == 0:
                x += 40
            elif i == 1:
                x += 25
            elif i == 2:
                x += 25
            elif i== 3:
                x += 25
            elif i == 4:
                x += 15
            start_idx, end_idx = idx_range
            left_x = x + start_idx * bar_gap
            right_x = x + (end_idx + 1) * bar_gap
            center_x = (left_x + right_x - bar_gap) / 2

            c.setFont("Pretendard-Bold", 8)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(center_x, y + chart_height + domain_label_margin - 17, domain)
        x = ori_x

        # ✅ 4. 막대 및 아래축 라벨 및 세로젖ㅁ선
        for i, (label, score) in enumerate(subtests):

            if i % 2 == 0:
                x += 24
                # 세로 점선
                split_x = x + i * bar_gap - bar_gap / 2 + bar_width / 2
                c.setStrokeColor(HexColor("#B5B5B5"))
                c.setDash(1, 2)
                c.setLineWidth(0.5)
                c.line(split_x, y, split_x, y + full_chart_height - 5)

            bx = x + i * bar_gap + 9.5
            if i > 6:
                bx -= 1.5
            bh = score * bar_unit
            cx = bx + bar_width / 2

            c.setFillColor(HexColor("#80D167"))
            c.rect(bx, y, bar_width, bh, fill=1, stroke=0)

            c.setFont("Pretendard-Bold", 7)
            c.setFillColor(HexColor("#3DB419"))
            c.drawCentredString(cx, y + bh + 3, str(score))
            c.setFillColor(HexColor("#000000"))
            c.setFont("Pretendard-Regular", 7)
            c.drawCentredString(cx, y - 10, label)

        end_x = x + len(subtests) * bar_gap
        split_indices = [0, 2, 4, 6, 8]  # 공통성~어휘, 어휘~토막, ..., 동형찾기 이후는 생략

        # ✅ 1. 수평 점선 (수준 기준선 및 라벨)
        level_ranges = [
            (1, 4, "지체"),
            (5, 6, "경계선"),
            (7, 8, "평균하"),
            (9, 11, "평균"),
            (12, 13, "평균상"),
            (14, 15, "우수"),
            (16, 19, "최우수"),
        ]

        for start, end, label in level_ranges:
            bottom_y = y + (start - 1) * bar_unit
            top_y = y + end * bar_unit
            center_y = (bottom_y + top_y) / 2

            # 점선 그리기 (위쪽 라인)
            c.setStrokeColor(HexColor("#CCCCCC"))
            c.setDash(1, 2)
            c.setLineWidth(0.5)
            c.line(label_x, top_y, end_x, top_y)

            # 수준 텍스트 그리기 (중앙 라벨)
            c.setDash()
            c.setFont("Pretendard-Bold", 8)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(label_x + 28, center_y - 4, label)

        c.setDash()

        # ✅ 5. 테두리 (하단 + 좌측 + 우측만)
        c.setStrokeColor(HexColor("#888888"))
        c.setLineWidth(0.8)
        # 왼쪽: 수준 라벨 왼쪽까지 감싸기
        c.line(label_x, y, label_x, y + full_chart_height - 5)
        # 오른쪽
        c.line(end_x, y, end_x, y + full_chart_height - 5)
        # 아래쪽
        c.line(label_x, y, end_x, y)


    # # 도메인 정의
    # domains = {
    #     "언어이해": [0, 1],
    #     "시공간": [2, 3],
    #     "유동추론": [4, 5],
    #     "작업기억": [6, 7],
    #     "처리속도": [8, 9]
    # }
    #
    # subtests = [
    #     ("공통성", 11), ("어휘", 15), ("토막짜기", 12), ("퍼즐", 11),
    #     ("행렬추리", 15), ("무게비교", 14), ("숫자", 11), ("그림기억", 11),
    #     ("기호쓰기", 11), ("동형찾기", 11)
    # ]
    #

    # 도메인 순서 고정
    domain_order = ["언어이해", "시공간", "유동추론","지각추론", "작업기억", "처리속도"]

    # 변환 결과
    subtests = []
    domains = {}
    index = 0

    for domain in domain_order:
        domain_subtests = []
        for key, value in subtest_scores.items():
            if key.startswith(domain + "_"):
                name = key.split("_")[1]
                subtests.append((name, value))
                domain_subtests.append(index)
                index += 1
        if domain_subtests:  # ✅ 빈 도메인은 제외
            domains[domain] = domain_subtests


    draw_subtest_scores_final(c, domains, subtests, x=105, y=70)

    # 페이지 번호
    # ✅ 페이지 번호
    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "05")

    c.showPage()

    ################################
    ## PAGE 6 지능검사 요약 3 게이지

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "웩슬러 지능검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Korean-Wechsler Intelligence Scale")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    def draw_gauge_section(c, x, y, title, score, level, description):
        radius = 50  # ✅ 게이지 크기 증가
        cx = x + radius + 10
        cy = y + radius - 35  # 게이지 위치 조금 아래로
        gauge_thickness = 4
        pointer_length = radius - 5

        # ✅ 설명 박스 배경
        c.setFillColor(HexColor("#D9F1D1"))
        c.rect(x, y + 88, 450, 24, fill=1, stroke=0)

        # ✅ 초록 제목 (지표명만 초록)
        c.setFont("Pretendard-Bold", 10)
        c.setFillColor(HexColor("#3DB419"))
        c.drawString(x+12, y + 97, f"{title}")

        # ✅ 제목 설명 (검정)
        c.setFillColor(HexColor("#000000"))
        c.setFont("Pretendard-SemiBold", 9)
        c.drawString(x+105, y + 97, f"{title}는 {score}으로 [{level}] 수준입니다.")

        # ✅ 배경 반원
        c.setLineWidth(gauge_thickness)
        c.setStrokeColor(HexColor("#EEEEEE"))
        c.arc(cx - radius + 2, cy - radius - 3, cx + radius + 2, cy + radius - 3, 0, 180)

        # ✅ 게이지 채움 (노랑 → 초록)
        steps = int((score / 160) * 50)
        for i in range(steps):
            theta = pi - (pi * i / 50)
            px1 = cx + radius * cos(theta)
            py1 = cy + radius * sin(theta)
            px2 = cx + (radius - gauge_thickness) * cos(theta)
            py2 = cy + (radius - gauge_thickness) * sin(theta)

            r = int(255 - (255 - 128) * i / 50)
            g = int(215 + (209 - 215) * i / 50)
            b = int(0 + (103 - 0) * i / 50)
            c.setStrokeColor(HexColor(f"#{r:02X}{g:02X}{b:02X}"))
            c.setLineWidth(gauge_thickness)
            c.line(px1, py1, px2, py2)

        # ✅ 시계침 (삼각형)
        angle = pi - (pi * (score / 160))
        tip_x = cx + pointer_length * cos(angle)
        tip_y = cy + pointer_length * sin(angle)

        base_radius = 3
        left_x = cx + base_radius * cos(angle + pi / 2)
        left_y = cy + base_radius * sin(angle + pi / 2)
        right_x = cx + base_radius * cos(angle - pi / 2)
        right_y = cy + base_radius * sin(angle - pi / 2)

        # 삼각형 바늘
        c.setFillColor(HexColor("#000000"))
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(1)
        path = c.beginPath()
        path.moveTo(left_x, left_y)
        path.lineTo(right_x, right_y)
        path.lineTo(tip_x, tip_y)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

        # ✅ 둥근 시작점
        c.setFillColor(HexColor("#000000"))
        c.circle(cx, cy, 3, fill=1, stroke=0)

        # ✅ 시계침 끝 강조 (흰 배경 원 + 검정 테두리)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(0.8)
        c.circle(tip_x+2, tip_y+2, 3, fill=1, stroke=1)

        # ✅ 점수 라벨
        c.setFont("Pretendard-Bold", 8)
        c.setFillColor(HexColor("#000000"))
        c.drawCentredString(tip_x+15, tip_y + 5, str(score))

        # ✅ 눈금
        c.setFont("Pretendard-Regular", 7)
        c.drawString(cx - radius - 8, cy, "0")
        c.drawRightString(cx + radius + 15, cy, "160")

        # ✅ 오른쪽 설명 (모두 검정)
        c.setFont("Pretendard-SemiBold", 8)
        c.setFillColor(HexColor("#000000"))
        text_y = y + 60
        for i, line in enumerate(description.split("\n")):
            c.drawString(x + 165, text_y - i * 15, line)

    start_y = height - 250
    gap = 135

    labels=[]
    for i in IntelligenceDomain.keys():
        Intdomain=IntelligenceDomain[i][0] + " 지표(" + IntelligenceDomain[i][1] + ")"
        labels.append((Intdomain, int(IntelligenceDomain[i][2]), IntelligenceDomain[i][3], IntelligenceDomain[i][4]))
    # labels = [
    #     ("언어이해(VCI)", 116, "평균 상",
    #      "‘어휘’ 소검사의 수행이 [우수] 수준으로, 개별 어휘에 대해 이해를 토대로\n"
    #      "표현하는 능력이 뛰어납니다. ‘공통성’ 수행이 [평균] 수준으로\n"
    #      "언어적 지식을 활용하여 새로운 개념을 유추하는 능력도 양호합니다."),
    #
    #     ("시공간(VSI)", 111, "평균 상",
    #      "‘퍼즐’과 ‘토막짜기’ 소검사의 수행이 모두 [평균] 수준으로\n"
    #      "정신적 회전이나 물체의 조작 등을 통한 시공간적 구성 능력이 양호합니다."),
    #
    #     ("유동추론(FRI)", 114, "평균 상",
    #      "‘무게비교’ 소검사의 수행이 [우수] 수준으로, 숫자 개념에 대한 이해를 바탕으로\n"
    #      "문제의 규칙을 파악하는 능력이 탁월합니다. ‘행렬추리’ 수행이 [평균] 수준으로,\n"
    #      "가이드라인이 주어지지 않는 상태에서 다양한 정보를 가정하여 문제를 통해\n"
    #      "분석하는 능력도 양호합니다."),
    #
    #     ("작업기억(WMI)", 106, "평균",
    #      "‘숫자’와 ‘그림기억’ 소검사의 수행이 모두 [평균] 수준으로,\n"
    #      "청각적/시각적 작업기억력이 양호합니다."),
    #
    #     ("처리속도(PSI)", 105, "평균",
    #      "‘동형찾기’와 ‘기호쓰기’ 소검사의 수행이 모두 [평균] 수준으로\n"
    #      "시각적 탐색 및 처리 속도와 시간 효율 능력이 양호합니다.")
    # ]

    for i, (title, score, level, desc) in enumerate(labels):
        draw_gauge_section(c, x=65, y=start_y - i * gap, title=title, score=score, level=level, description=desc)

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "06")

    c.showPage()

    ################################

    ## PAGE 07 지능검사 요약 및 제언

    def draw_multiline_text(c, x, y, text, max_width, line_height=10, font_size=8.5, font_name="Pretendard-SemiBold"):
        c.setFont(font_name, font_size)
        c.setFillColor(HexColor("#000000"))

        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if stringWidth(test_line, font_name, font_size) <= max_width:
                    line = test_line
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
            lines.append("")  # paragraph space

        for i, line in enumerate(lines):
            c.drawString(x, y - i * line_height, line)

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "웩슬러 지능검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Korean-Wechsler Intelligence Scale")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#D9F1D1"))
    c.rect(60, height - 160, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 150, f"요약 및 제언")

    # summary_text = (
    #     "아동의 경우, 전체지능이 116, [평균상] 수준입니다. 모든 소검사에서 평균을 상회하거나 [평균상~우수]에 속하는 수행을 보이며\n"
    #     "학업적 성취에 필요한 제한 자원을 고르게 양호하게 갖춘 것으로 평가됩니다.\n\n\n"
    #     "특히, 토막에 비해 우수한 어휘력과 언어적 표현력이 아동의 인지적 강점입니다.\n"
    #     "자신이 보유한 어휘를 바탕으로 언어적 추론을 통해 상위 개념을 형성하는 능력도 양호하여,\n"
    #     "국어와 같이 언어를 매개로 하는 학업적 영역에서 준수한 성취가 기대됩니다.\n\n\n"
    #     "아이의 강점인 언어적 능력을 지속적으로 계발할 수 있도록 풍부한 언어적 자극과 상호작용을 제공하는 양육 환경을\n"
    #     "지속하는 것이 권장됩니다. 풍부한 언어적 표현력을 바탕으로 책 읽기, 이야기 만들기, 역할놀이, 자신의 생각을 말로 설명하기 등의\n"
    #     "언어 중심 활동을 자주 경험하게 함으로써 언어 능력을 사고력으로 확장해 볼 수 있겠습니다.\n\n\n"
    #     "더불어, 수리적 추론 능력 역시 아동의 뚜렷한 강점입니다. 수량 개념에 대한 이해를 바탕으로 한 양적 비교 능력이 탁월하여,\n"
    #     "수별, 비율 등을 다루는 수학 과목에서 우수한 성취가 기대됩니다. 기본 교과과정 외에도 사고력 수학 등 추론 과정을 강조하는\n"
    #     "심화 활동을 통해 아동의 인지적 강점을 더욱 강화할 수 있겠습니다."
    # )

    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 190  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, final_summary, max_width=text_width)

    c.showPage()

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "07")



    ################################
    ## PAGE 08 TCI - 유형 그래프

    def draw_circle_icon(c, center_x, center_y, text="L", color="#FFA800"):
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(1.5)
        c.setFillColor(HexColor("#FFFFFF"))
        c.circle(center_x, center_y, 15, fill=1, stroke=1)

        c.setFont("Pretendard-Bold", 15)
        c.setFillColor(HexColor(color))
        c.drawCentredString(center_x, center_y - 6, text)

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "기질 및 성격검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Temperament and Character Inventory")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)


    ###################TCI###################
    ans1 = TCI_scores[0]['자극추구']['level']
    ans2 = TCI_scores[0]['위험회피']['level']
    ans3 = TCI_scores[0]['사회적 민감성']['level']
    color1 = "#FFA800"
    color2 = "#FFA800"
    color3 = "#FFA800"
    if TCI_scores[0]['자극추구']['level'] == "M":
        color1 = "#FFA800"
    if TCI_scores[0]['위험회피']['level'] == "M":
        color2 = "#FFA800"
    if TCI_scores[0]['사회적 민감성']['level'] == "M":
        color3 = "#FFA800"

    # ✅ 연두색 요약 박스
    c.setFillColor(HexColor("#E5F6DD"))
    c.rect(60, height - 205, 475, 70, fill=1, stroke=0)

    c.setFont("Pretendard-SemiBold", 15)
    c.setFillColor(HexColor("#000000"))
    c.drawString(85, height - 175, "당신의 기질 유형은")


    c.setFont("Pretendard-Bold", 15)
    c.setFillColor(HexColor("#3DB419"))
    c.drawString(200, height - 175, ans1+ans2+ans3)

    c.setFont("Pretendard-SemiBold", 15)
    c.setFillColor(HexColor("#000000"))
    c.drawString(235, height - 175, "입니다.")



    # ✅ 아이콘 3개
    draw_circle_icon(c, 380, height - 165, ans1, color1)
    c.setFont("Pretendard-Bold", 8)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(380, height - 195, "자극추구")

    draw_circle_icon(c, 440, height - 165, ans2, color2)
    c.setFont("Pretendard-Bold", 8)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(440, height - 195, "위험회피")

    draw_circle_icon(c, 500, height - 165, ans3, color3)
    c.setFont("Pretendard-Bold", 8)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(500, height - 195, "사회적 민감성")

    # ✅ "지능지수 백분위 분포 그래프" 소제목 (왼쪽 초록바)
    c.setFillColor(HexColor("#80D167"))
    c.rect(62, height - 233, 3, 10, fill=1, stroke=0)

    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(70, height - 230, "소척도 그래프")

    def draw_tci_table():


        # 데이터
        tci_data = [
            ("기질", "자극추구 (NS)", TCI_scores[0]['자극추구']['oriScore'], TCI_scores[0]['자극추구']['Tscore'], TCI_scores[0]['자극추구']['percentile']),
            ("기질", "위험회피 (HA)", TCI_scores[0]['위험회피']['oriScore'], TCI_scores[0]['위험회피']['Tscore'], TCI_scores[0]['위험회피']['percentile']),
            ("기질", "사회적 민감성 (RD)", TCI_scores[0]['사회적 민감성']['oriScore'], TCI_scores[0]['사회적 민감성']['Tscore'], TCI_scores[0]['사회적 민감성']['percentile']),
            ("기질", "인내력 (PS)", TCI_scores[0]['인내력']['oriScore'], TCI_scores[0]['인내력']['Tscore'], TCI_scores[0]['인내력']['percentile']),
            ("성격", "자율성 (SD)", TCI_scores[0]['자율성']['oriScore'], TCI_scores[0]['자율성']['Tscore'], TCI_scores[0]['자율성']['percentile']),
            ("성격", "연대감 (CO)", TCI_scores[0]['연대감']['oriScore'], TCI_scores[0]['연대감']['Tscore'], TCI_scores[0]['연대감']['percentile']),
            ("성격", "자기초월 (ST)", TCI_scores[0]['자기초월']['oriScore'], TCI_scores[0]['자기초월']['Tscore'], TCI_scores[0]['자기초월']['percentile']),
            ("성격", "자율성+연대감 (SC)", TCI_scores[0]['자율성+연대감']['oriScore'], TCI_scores[0]['자율성+연대감']['Tscore'], TCI_scores[0]['자율성+연대감']['percentile']),
        ]

        # 좌표 설정
        start_x = 60
        start_y = height - 280
        row_height = 30
        col_width = 53
        col_widths = [col_width*1, col_width*2, col_width*1, col_width*1, col_width*1, col_width*3]
        col_titles = ["TCI-RS", "척도", "원점수", "T점수", "백분위", "백분위 그래프"]

        # 제목행
        c.setFillColor(HexColor("#EFEFEF"))
        c.rect(start_x, start_y, sum(col_widths), row_height, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Pretendard-Bold", 10)
        for i, title in enumerate(col_titles):
            c.drawCentredString(start_x + sum(col_widths[:i]) + col_widths[i] / 2, start_y + 10, title)

        # 기준 구간(L, M, H) 라벨행
        graph_x = start_x + sum(col_widths[:-1])
        y = start_y - row_height

        def draw_percentile_legend(c, graph_x, start_y, col_width):
            legend_y = start_y - 16  # 기준선 y 위치
            legend_height = 12
            legend_width = col_width - 16
            legend_x = graph_x + 8

            # 기준 퍼센트 위치 (0~100 기준)
            def percent_to_x(p):
                return legend_x + legend_width * (p / 100)

            # 기준점
            l_center = percent_to_x(17.5)
            m_center = percent_to_x(55)
            h_center = percent_to_x(92.5)

            # 화살표 그리기 함수
            def draw_arrow(c, x, y, direction="left"):
                size = 3
                if direction == "left":
                    points = [(x, y), (x + size, y + size), (x + size, y - size)]
                else:
                    points = [(x, y), (x - size, y + size), (x - size, y - size)]

                path = c.beginPath()
                path.moveTo(*points[0])
                path.lineTo(*points[1])
                path.lineTo(*points[2])
                path.close()

                c.setFillColor(HexColor("#666666"))
                c.setStrokeColor(HexColor("#666666"))
                c.drawPath(path, stroke=0, fill=1)

            # L, M, H 사각형 라벨 그리기
            def draw_label_box(c, x, y, label):
                box_size = 10
                c.setFillColor(HexColor("#DDDDDD"))
                c.roundRect(x - box_size / 2, y - box_size / 2, box_size, box_size, 2, fill=1, stroke=0)
                c.setFillColor(HexColor("#000000"))
                c.setFont("Pretendard-Bold", 6.5)
                c.drawCentredString(x, y - 2, label)

            # 기준선 점선 수직
            c.setDash(1, 2)
            c.setStrokeColor(HexColor("#AAAAAA"))
            c.setLineWidth(0.5)
            c.line(percent_to_x(35), legend_y - row_height * 8.5 , percent_to_x(35), legend_y - row_height / 2)
            c.line(percent_to_x(75), legend_y - row_height * 8.5 , percent_to_x(75), legend_y - row_height / 2)

            # 기준선 실선 수평
            c.setDash(1, 0)
            c.setStrokeColor(HexColor("#666666"))
            c.setLineWidth(0.5)
            c.line(l_center - 20, legend_y, l_center + 20, legend_y)
            c.line(m_center - 20, legend_y, m_center + 20, legend_y)
            c.line(h_center - 20, legend_y, h_center + 20, legend_y)

            # 화살표 + 라벨: L
            draw_arrow(c, l_center - 20, legend_y, direction="left")
            draw_arrow(c, l_center + 20, legend_y, direction="right")
            draw_label_box(c, l_center, legend_y, "L")

            # 화살표 + 라벨: M
            draw_arrow(c, m_center - 23, legend_y, direction="left")
            draw_arrow(c, m_center + 23, legend_y, direction="right")
            draw_label_box(c, m_center, legend_y, "M")

            # 화살표 + 라벨: H
            draw_arrow(c, h_center - 20, legend_y, direction="left")
            draw_arrow(c, h_center + 20, legend_y, direction="right")
            draw_label_box(c, h_center, legend_y, "H")

            # 기준 숫자: 35, 75
            c.setFont("Pretendard-Regular", 6)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(percent_to_x(35), legend_y-2, "35")
            c.drawCentredString(percent_to_x(75), legend_y-2, "75")

        # 본문 데이터
        for idx, (group, label, raw, t, per) in enumerate(tci_data):
            y = start_y - row_height * (idx + 2)
            is_temperament = group == "기질"
            graph_color = HexColor("#80D167") if is_temperament else HexColor("#F7A823")

            # 배경
            if group == "기질":
                c.setFillColor(HexColor("#F8FBF8"))
            else:
                c.setFillColor(HexColor("#FEFAF5"))
            c.rect(start_x, y, sum(col_widths), row_height, fill=1, stroke=0)

            # 텍스트 입력
            c.setFillColor(black)
            c.setFont("Pretendard-Bold", 10)
            values = [group if idx == 0 or tci_data[idx - 1][0] != group else "", label, str(raw), str(t), str(per)]
            for i, val in enumerate(values):
                if not(i==0):
                    c.drawCentredString(start_x + sum(col_widths[:i]) + col_widths[i] / 2, y + 12, val)

            # 백분위 그래프
            graph_center = graph_x + col_widths[-1] / 2
            bar_length = abs(per - 50) * 1.2  # 스케일 조정
            bar_y = y + 8
            if per < 50:
                bar_x = graph_center - bar_length
            else:
                bar_x = graph_center
            if label != "자율성+연대감 (SC)":
                c.setFillColor(graph_color)
                c.rect(bar_x, bar_y, bar_length, 14, fill=1, stroke=0)
                c.setFont("Pretendard-Bold", 9)
                abbr = label.split("(")[-1].replace(")", "")
                c.setFillColor(black)
                c.drawCentredString(graph_center, bar_y + 4, abbr)

        c.drawCentredString(start_x + col_widths[0] / 2, y + row_height * 6 - 5, "기질")
        c.drawCentredString(start_x + col_widths[0] / 2, y + row_height * 2 - 5, "성격")
        # 범례 그리기
        draw_percentile_legend(c, graph_x, start_y, col_widths[-1])

        # 외곽 테두리 및 굵은 선
        c.setStrokeColor("#7F7F7F")

        for i in range(len(tci_data) + 2):
            y = start_y - row_height * i
            # 제목행 하단, 최하단
            c.setLineWidth(2 if i in [0,9] else 0.5)
            # 제목행 상단
            if i==0:
                c.line(start_x, y+row_height, start_x + sum(col_widths), y+row_height)
            if i == 0 or i==1 or i == 5 or i == 9:
                c.line(start_x , y, start_x + sum(col_widths), y)
            else:
                c.line(start_x + col_widths[0], y, start_x + sum(col_widths), y)

        c.setLineWidth(0.5)
        x = start_x
        for i, w in enumerate(col_widths):
            if not(i==0):
                c.line(x, start_y - row_height, x, start_y - row_height * (len(tci_data) + 1))
            if i==5:
                c.setLineWidth(2)
                c.line(x, start_y, x, start_y - row_height * (len(tci_data) + 1))
            x += w

    # 실행
    draw_tci_table()

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "08")


    c.showPage()

    ###############################
    #PAGE 09 - 기질1 기질2

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "기질 및 성격검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Temperament and Character Inventory")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    ### 기질[타고난 특성]
    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#D9F1D1"))
    c.rect(60, height - 160, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 150, f"기질 [타고난 특성]")

    summary_text=TCI_scores[3][0][4]

    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 190  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, summary_text, max_width=text_width)

    ### 기질[대인관계 능력]
    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#D9F1D1"))
    c.rect(60, height - 460, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 450, f"기질 [대인관계 능력]")
    summary_text=TCI_scores[3][1][4]
    # summary_text = (
    #     "다른 사람의 감정을 파악할 수 있는 기질적 민감성을 적절히 가지고 있고,\n"
    #     "다른 사람과 친밀하게 감정을 공유하는 것에도 특별한 불편감이 없는 기질입니다.\n\n"
    #     "이러한 기질은 자신의 감정을 과도하게 드러내거나, 또는 다른 사람의 비난이나 거절에 지나치게 불안해하는\n"
    #     "일이 없는 안정적인 특성을 보입니다.\n"
    #     "즉, 필요한 순간에 적극적으로 자기주장을 할 수 있지만 감정의 조절이 필요한 순간에는 적절히 제어할 수 있다는 강점이 있습니다\n"
    # )

    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 490  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, summary_text, max_width=text_width)

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "09")


    c.showPage()

    ################################
    ##PAGE 10 - 기질 제언

    def draw_multiline_text(c, x, y, text, max_width, line_height=10, font_name="Pretendard-SemiBold", font_size=8.5):
        c.setFont(font_name, font_size)
        c.setFillColor(HexColor("#000000"))

        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if stringWidth(test_line, font_name, font_size) <= max_width:
                    line = test_line
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
            lines.append("")  # paragraph space

        for i, line in enumerate(lines):
            c.drawString(x, y - i * line_height, line)

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "기질 및 성격검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Temperament and Character Inventory")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    ### 기질[타고난 특성]
    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#D9F1D1"))
    c.rect(60, height - 160, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 150, f"기질 최적화 양육 방법")

    summary_text=TCI_scores[4][0][4]
    summary_text += "\n" + TCI_scores[4][1][4]


    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 190  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, summary_text, max_width=text_width)

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "10")


    c.showPage()


    ################################
    ## PAGE 11  - 성격
    def draw_multiline_text(c, x, y, text, max_width, line_height=10, font_name="Pretendard-SemiBold", font_size=8.5):
        c.setFont(font_name, font_size)
        c.setFillColor(HexColor("#000000"))

        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if stringWidth(test_line, font_name, font_size) <= max_width:
                    line = test_line
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
            lines.append("")  # paragraph space

        for i, line in enumerate(lines):
            c.drawString(x, y - i * line_height, line)

        # 제목

    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "기질 및 성격검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(250, height - 90, "Temperament and Character Inventory")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    ### 기질[타고난 특성]
    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#FEEED4"))
    c.rect(60, height - 160, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 150, f"성격")

    summary_text=TCI_scores[3][2][4]

    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 190  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, summary_text, max_width=text_width)


    ### 기질[타고난 특성]
    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#FEEED4"))
    c.rect(60, height - 360, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 350, f"성숙한 성격 발달 방법성격")

    summary_text=TCI_scores[4][2][4]

    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 390  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, summary_text, max_width=text_width)


    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "11")

    c.showPage()


    ################################
    ## PAGE 12 - 부모양육태도검사 1

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "부모 양육태도 검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(280, height - 90, "Parenting Attitude Test - Second Edition")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    def draw_parenting_graph(c, x=60, y=150, width=480, height=300):
        from reportlab.lib.colors import HexColor

        # 항목, 백분위, 결과
        items = [
            ("지지표현", 95, "지나침"),
            ("합리적 설명", 98, "지나침"),
            ("상취압력", 30, "미흡함"),
            ("간섭", 40, "이상적임"),
            ("처벌", 30, "이상적임"),
            ("감독", 95, "지나침"),
            ("과잉기대", 20, "이상적임"),
            ("비일관성", 30, "이상적임")
        ]

        num_items = len(items)
        bar_width = width / num_items
        bar_max_height = height
        label_font = "Pretendard-Regular"
        bold_font = "Pretendard-Bold"

        # 배경 그리드
        for i in range(0, 101, 20):
            grid_y = y + (i / 100) * bar_max_height
            c.setStrokeColor(HexColor("#DDDDDD"))
            c.setLineWidth(1)
            c.setDash(1, 2)
            c.line(x, grid_y, x + width, grid_y)

        # ✅ 항목별 이상적인 범위 배경과 점선
        ideal_ranges = {
            "지지표현": (65, 85),
            "합리적 설명": (65, 85),
            "상취압력": (50, 70),
            "간섭": (40, 60),
            "처벌": (30, 50),
            "감독": (30, 50),
            "과잉기대": (20, 40),
            "비일관성": (10, 30)
        }

        for i, (label, value, result) in enumerate(items):
            if label not in ideal_ranges:
                continue
            low, high = ideal_ranges[label]
            bx = x + i * bar_width + bar_width * 0.25
            bar_x_center = bx + bar_width * 0.5 / 2

            # 이상 범위 배경
            ideal_bottom = y + (low / 100) * bar_max_height
            ideal_top = y + (high / 100) * bar_max_height
            c.setFillColor(HexColor("#FFF3C8"))
            c.setLineWidth(0.5)
            c.setDash(1, 0)
            c.rect(bx-bar_width/4, ideal_bottom, bar_width, ideal_top - ideal_bottom, fill=1, stroke=0)

            # 상한선, 하한선 점선
            c.setStrokeColor(HexColor("#C9A100"))
            c.setLineWidth(0.5)
            c.setDash(1, 2)
            c.line(bx, ideal_bottom, bx + bar_width * 0.5, ideal_bottom)  # 하한
            c.line(bx, ideal_top, bx + bar_width * 0.5, ideal_top)        # 상한


        # ✅ 각 항목에 세로 점선 추가
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(1)
        c.setDash(1, 2)

        for i in range(num_items):
            bx = x + i * bar_width + bar_width * 0.75
            bar_center_x = bx + bar_width * 0.5 / 2
            c.line(bar_center_x, y, bar_center_x, y + bar_max_height)

        # 막대 그래프
        for i, (label, value, result) in enumerate(items):
            bx = x + i * bar_width + bar_width * 0.25
            bh = (value / 100) * bar_max_height
            by = y

            # 막대
            c.setFillColor(HexColor("#7CC344"))
            c.rect(bx, by, bar_width * 0.5, bh, fill=1, stroke=0)

        # Y축 기준선 및 백분위 숫자
        c.setFont(label_font, 7)
        c.setFillColor(HexColor("#666666"))
        for i in range(0, 101, 20):
            label_y = y + (i / 100) * bar_max_height - 3
            c.drawRightString(x - 5, label_y, str(i))

        # ========================
        # ✅ 아래쪽 표 추가하기
        # ========================
        cell_width = bar_width
        cell_height = 24
        table_y = y - 40  # 그래프 아래로 충분히 떨어뜨리기

        header_bg = HexColor("#F0FAEF")
        ideal_bg = HexColor("#FFF7D9")

        # 상단 제목행
        c.setFont("Pretendard-Bold", 9)
        for i, (label, _, _) in enumerate(items):
            cx = x + i * cell_width
            c.setFillColor(header_bg)
            c.rect(cx, table_y, cell_width, cell_height, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(cx + cell_width / 2, table_y + 6, label)

        # 백분위 행
        for i, (_, value, _) in enumerate(items):
            cx = x + i * cell_width
            cy = table_y - cell_height
            c.setFillColor(HexColor("#FFFFFF"))
            c.rect(cx, cy, cell_width, cell_height, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.setFont("Pretendard-Regular", 9)
            c.drawCentredString(cx + cell_width / 2, cy + 6, str(value))

        # 결과 행
        for i, (_, _, result) in enumerate(items):
            cx = x + i * cell_width
            cy = table_y - 2 * cell_height
            if "지나침" in result or "미흡" in result:
                text_color = HexColor("#D20000")
            else:
                text_color = HexColor("#000000")
            bg_color = ideal_bg if "이상적임" in result else HexColor("#FFFFFF")

            c.setFillColor(bg_color)
            c.rect(cx, cy, cell_width, cell_height, fill=1, stroke=0)
            c.setFillColor(text_color)
            c.setFont("Pretendard-Bold", 9)
            c.drawCentredString(cx + cell_width / 2, cy + 6, result)

        # 왼쪽 열: "백분위", "결과"
        left_titles = ["백분위", "결과"]
        c.setFont("Pretendard-Bold", 9)
        for i, label in enumerate(left_titles):
            cy = table_y - (i + 1) * cell_height
            c.setFillColor(HexColor("#DCEAD6"))
            c.rect(x - 60, cy, 60, cell_height, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(x - 30, cy + 6, label)
        # ✅ 오른쪽 위 범례 박스 추가
        legend_x = x + width + 20
        legend_y = y + height - 10
        legend_w = 100
        legend_h = 42

        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(legend_x, legend_y - legend_h, legend_w, legend_h, fill=1, stroke=0)

        # 색상 사각형 및 텍스트
        legend_items = [
            ("#FFF3C8", "이상적인 범위"),
            ("#7CC344", "자녀보고"),
            (None, "단위: 백분위(%ile)")
        ]

        c.setFont("Pretendard-Regular", 7)
        for i, (color, label) in enumerate(legend_items):
            lx = legend_x + 60 * i - legend_x / 3
            if color:
                c.setFillColor(HexColor(color))
                c.rect(lx + 2, legend_y+20, 8, 8, fill=1, stroke=0)
                c.setFillColor(HexColor("#000000"))
                c.drawString(lx + 14, legend_y+20, label)
            else:
                c.setFillColor(HexColor("#000000"))
                c.drawString(lx - 14, legend_y+20, label)

    draw_parenting_graph(c, x=120, y=500, width=410, height=200)  # 높이 약간 올림


    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#D9F1D1")) #FEEDD3
    c.rect(60, height - 470, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 460, f"요약 및 제언")

    print("PAT",PAT_scores)


    final_summary = "".join(PAT_scores['ideal'][1])
    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 490  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, final_summary, max_width=text_width)

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "12")

    c.showPage()


    ################################
    ## PAGE 13 - 부모양육태도검사 2

    # 제목
    c.setFillColor(HexColor("#D3F6B3"))
    c.rect(0, height - 15, width, 15, fill=1, stroke=0)
    c.setFont("Pretendard-Bold", 28)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60, height - 90, "부모 양육태도 검사")
    c.setFont("Pretendard-SemiBold", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(280, height - 90, "Parenting Attitude Test - Second Edition")

    # ✅ 구분선
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 60, height - 110)

    def draw_parenting_graph(c, x=60, y=150, width=480, height=300):
        from reportlab.lib.colors import HexColor

        # 항목, 백분위, 결과
        items = [
            ("지지표현", 95, "지나침"),
            ("합리적 설명", 98, "지나침"),
            ("상취압력", 30, "미흡함"),
            ("간섭", 40, "이상적임"),
            ("처벌", 30, "이상적임"),
            ("감독", 95, "지나침"),
            ("과잉기대", 20, "이상적임"),
            ("비일관성", 30, "이상적임")
        ]

        num_items = len(items)
        bar_width = width / num_items
        bar_max_height = height
        label_font = "Pretendard-Regular"
        bold_font = "Pretendard-Bold"

        # 배경 그리드
        for i in range(0, 101, 20):
            grid_y = y + (i / 100) * bar_max_height
            c.setStrokeColor(HexColor("#DDDDDD"))
            c.setLineWidth(1)
            c.setDash(1, 2)
            c.line(x, grid_y, x + width, grid_y)

        # ✅ 항목별 이상적인 범위 배경과 점선
        ideal_ranges = {
            "지지표현": (65, 85),
            "합리적 설명": (65, 85),
            "상취압력": (50, 70),
            "간섭": (40, 60),
            "처벌": (30, 50),
            "감독": (30, 50),
            "과잉기대": (20, 40),
            "비일관성": (10, 30)
        }

        for i, (label, value, result) in enumerate(items):
            if label not in ideal_ranges:
                continue
            low, high = ideal_ranges[label]
            bx = x + i * bar_width + bar_width * 0.25
            bar_x_center = bx + bar_width * 0.5 / 2

            # 이상 범위 배경
            ideal_bottom = y + (low / 100) * bar_max_height
            ideal_top = y + (high / 100) * bar_max_height
            c.setFillColor(HexColor("#FFF3C8"))
            c.setLineWidth(0.5)
            c.setDash(1, 0)
            c.rect(bx-bar_width/4, ideal_bottom, bar_width, ideal_top - ideal_bottom, fill=1, stroke=0)

            # 상한선, 하한선 점선
            c.setStrokeColor(HexColor("#C9A100"))
            c.setLineWidth(0.5)
            c.setDash(1, 2)
            c.line(bx, ideal_bottom, bx + bar_width * 0.5, ideal_bottom)  # 하한
            c.line(bx, ideal_top, bx + bar_width * 0.5, ideal_top)        # 상한


        # ✅ 각 항목에 세로 점선 추가
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(1)
        c.setDash(1, 2)

        for i in range(num_items):
            bx = x + i * bar_width + bar_width * 0.75
            bar_center_x = bx + bar_width * 0.5 / 2
            c.line(bar_center_x, y, bar_center_x, y + bar_max_height)

        # 막대 그래프
        for i, (label, value, result) in enumerate(items):
            bx = x + i * bar_width + bar_width * 0.25
            bh = (value / 100) * bar_max_height
            by = y

            # 막대
            c.setFillColor(HexColor("#7CC344"))
            c.rect(bx, by, bar_width * 0.5, bh, fill=1, stroke=0)

        # Y축 기준선 및 백분위 숫자
        c.setFont(label_font, 7)
        c.setFillColor(HexColor("#666666"))
        for i in range(0, 101, 20):
            label_y = y + (i / 100) * bar_max_height - 3
            c.drawRightString(x - 5, label_y, str(i))

        # ========================
        # ✅ 아래쪽 표 추가하기
        # ========================
        cell_width = bar_width
        cell_height = 24
        table_y = y - 40  # 그래프 아래로 충분히 떨어뜨리기

        header_bg = HexColor("#F0FAEF")
        ideal_bg = HexColor("#FFF7D9")

        # 상단 제목행
        c.setFont("Pretendard-Bold", 9)
        for i, (label, _, _) in enumerate(items):
            cx = x + i * cell_width
            c.setFillColor(header_bg)
            c.rect(cx, table_y, cell_width, cell_height, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(cx + cell_width / 2, table_y + 6, label)

        # 백분위 행
        for i, (_, value, _) in enumerate(items):
            cx = x + i * cell_width
            cy = table_y - cell_height
            c.setFillColor(HexColor("#FFFFFF"))
            c.rect(cx, cy, cell_width, cell_height, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.setFont("Pretendard-Regular", 9)
            c.drawCentredString(cx + cell_width / 2, cy + 6, str(value))

        # 결과 행
        for i, (_, _, result) in enumerate(items):
            cx = x + i * cell_width
            cy = table_y - 2 * cell_height
            if "지나침" in result or "미흡" in result:
                text_color = HexColor("#D20000")
            else:
                text_color = HexColor("#000000")
            bg_color = ideal_bg if "이상적임" in result else HexColor("#FFFFFF")

            c.setFillColor(bg_color)
            c.rect(cx, cy, cell_width, cell_height, fill=1, stroke=0)
            c.setFillColor(text_color)
            c.setFont("Pretendard-Bold", 9)
            c.drawCentredString(cx + cell_width / 2, cy + 6, result)

        # 왼쪽 열: "백분위", "결과"
        left_titles = ["백분위", "결과"]
        c.setFont("Pretendard-Bold", 9)
        for i, label in enumerate(left_titles):
            cy = table_y - (i + 1) * cell_height
            c.setFillColor(HexColor("#DCEAD6"))
            c.rect(x - 60, cy, 60, cell_height, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            c.drawCentredString(x - 30, cy + 6, label)
        # ✅ 오른쪽 위 범례 박스 추가
        legend_x = x + width + 20
        legend_y = y + height - 10
        legend_w = 100
        legend_h = 42

        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(legend_x, legend_y - legend_h, legend_w, legend_h, fill=1, stroke=0)

        # 색상 사각형 및 텍스트
        legend_items = [
            ("#FFF3C8", "이상적인 범위"),
            ("#7CC344", "자녀보고"),
            (None, "단위: 백분위(%ile)")
        ]

        c.setFont("Pretendard-Regular", 7)
        for i, (color, label) in enumerate(legend_items):
            lx = legend_x + 60 * i - legend_x / 3
            if color:
                c.setFillColor(HexColor(color))
                c.rect(lx + 2, legend_y+20, 8, 8, fill=1, stroke=0)
                c.setFillColor(HexColor("#000000"))
                c.drawString(lx + 14, legend_y+20, label)
            else:
                c.setFillColor(HexColor("#000000"))
                c.drawString(lx - 14, legend_y+20, label)

    draw_parenting_graph(c, x=120, y=500, width=410, height=200)  # 높이 약간 올림


    # ✅ 설명 박스 배경
    c.setFillColor(HexColor("#FEEDD3")) #FEEDD3
    c.rect(60, height - 470, 450, 24, fill=1, stroke=0)

    # ✅ 초록 제목 (지표명만 초록)
    c.setFont("Pretendard-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(60 + 12, height - 460, f"요약 및 제언")

    print("PAT",PAT_scores)


    final_summary = "".join(PAT_scores['ideal'][3])
    # 글자 출력 시작 좌표 (요약 박스 아래)
    text_x = 72
    text_y = height - 490  # 요약 박스보다 살짝 아래
    text_width = 450

    draw_multiline_text(c, text_x, text_y, final_summary, max_width=text_width)

    c.setFont("Pretendard-Bold", 9)
    c.setFillColor(HexColor("#535353"))
    c.drawRightString(width - 60, 40, "굿이너프")

    c.setFont("Pretendard-Regular", 9)
    c.setFillColor(HexColor("#A9A9A9"))
    c.drawRightString(width - 47.5, 40, "13")

    c.showPage()


    ################################
    ## PAGE 14 - 부모양육태도검사 3

    # c.showPage()


    ################################


    c.save()
    print(f"📄 전체 PDF 생성 완료: {output_path}")

if __name__ == "__main__":
    generate_full_pdf()


