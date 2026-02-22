#!/usr/bin/env python3
"""
인스타그램 카드뉴스 렌더링 엔진
HTML/CSS → PDF → PNG (1080×1080) 파이프라인

사용법:
  python3 render_cards.py --slides slides.json --output-dir ./output
  python3 render_cards.py --slides slides.json --theme warm_trust --prefix "학폭대응"
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
import argparse
from pathlib import Path

try:
    from weasyprint import HTML
    from PIL import Image
except ImportError:
    print("필수 패키지 설치 중...")
    subprocess.run([sys.executable, "-m", "pip", "install",
                    "weasyprint", "pillow", "koreanize-matplotlib",
                    "--break-system-packages", "-q"], check=True)
    from weasyprint import HTML
    from PIL import Image


# ──────────────────────────────────────────────
# 테마 정의
# ──────────────────────────────────────────────

THEMES = {
    "dark_professional": {
        "bg": "linear-gradient(160deg, #0c1220 0%, #1a2744 40%, #0f3460 100%)",
        "accent": "#e94560",
        "t1": "#ffffff",
        "t2": "#8899aa",
        "t3": "#445566",
        "badge_bg": "rgba(233,69,96,0.15)",
        "badge_bd": "rgba(233,69,96,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.05)",
        "card_bd": "rgba(255,255,255,0.08)",
        "num_color": "rgba(233,69,96,0.12)",
    },
    "warm_trust": {
        "bg": "linear-gradient(160deg, #1a1a2e 0%, #2d1b3d 50%, #461959 100%)",
        "accent": "#ff9f43",
        "t1": "#ffffff",
        "t2": "#c4a9d4",
        "t3": "#7a6188",
        "badge_bg": "rgba(255,159,67,0.15)",
        "badge_bd": "rgba(255,159,67,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.05)",
        "card_bd": "rgba(255,255,255,0.08)",
        "num_color": "rgba(255,159,67,0.10)",
    },
    "clean_light": {
        "bg": "linear-gradient(160deg, #f8f9fa 0%, #e9ecef 100%)",
        "accent": "#2563eb",
        "t1": "#1a1a2e",
        "t2": "#4a5568",
        "t3": "#a0aec0",
        "badge_bg": "rgba(37,99,235,0.10)",
        "badge_bd": "rgba(37,99,235,0.20)",
        "divider": "rgba(0,0,0,0.08)",
        "card_bg": "rgba(0,0,0,0.03)",
        "card_bd": "rgba(0,0,0,0.06)",
        "num_color": "rgba(37,99,235,0.08)",
    },
    "nature_green": {
        "bg": "linear-gradient(160deg, #0a1f0a 0%, #1a3a2a 40%, #0d4a3a 100%)",
        "accent": "#4ade80",
        "t1": "#ffffff",
        "t2": "#88bbaa",
        "t3": "#446655",
        "badge_bg": "rgba(74,222,128,0.15)",
        "badge_bd": "rgba(74,222,128,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.04)",
        "card_bd": "rgba(255,255,255,0.08)",
        "num_color": "rgba(74,222,128,0.10)",
    },
    "coral_soft": {
        "bg": "linear-gradient(160deg, #fff5f5 0%, #ffe4e6 50%, #fecdd3 100%)",
        "accent": "#e11d48",
        "t1": "#1c1917",
        "t2": "#57534e",
        "t3": "#a8a29e",
        "badge_bg": "rgba(225,29,72,0.10)",
        "badge_bd": "rgba(225,29,72,0.20)",
        "divider": "rgba(0,0,0,0.06)",
        "card_bg": "rgba(0,0,0,0.03)",
        "card_bd": "rgba(0,0,0,0.06)",
        "num_color": "rgba(225,29,72,0.08)",
    },
}


# ──────────────────────────────────────────────
# 이미지 헬퍼
# ──────────────────────────────────────────────

# 프로필 사진 매핑 (용도별 추천 사진)
PROFILE_PHOTOS = {
    "cover": "profile1_nobg.png",      # 정면 정자세 (커버용, 누끼)
    "cta": "profile4_nobg.png",        # 손 모은 자세 (CTA 신뢰감, 누끼)
    "side": "profile2_nobg.png",       # 측면 포즈 (누끼)
    "smile": "profile3_nobg.png",      # 팔짱 활짝 웃음 (누끼)
}

LOGO_FILE = "aegis logo.png"


def _img_to_base64(img_path: str) -> str:
    """이미지 파일을 base64 data URI로 변환"""
    if not img_path or not os.path.exists(img_path):
        return ""
    ext = os.path.splitext(img_path)[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}
    mime_type = mime.get(ext.lstrip("."), "image/png")
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _resolve_image(path_or_name: str, assets_dir: str = "") -> str:
    """이미지 경로를 해석: 절대경로/상대경로/파일이름 → 실제 경로"""
    if not path_or_name:
        return ""
    # 이미 절대경로
    if os.path.isabs(path_or_name) and os.path.exists(path_or_name):
        return path_or_name
    # assets_dir 기준
    if assets_dir:
        candidate = os.path.join(assets_dir, path_or_name)
        if os.path.exists(candidate):
            return candidate
    # 현재 디렉토리
    if os.path.exists(path_or_name):
        return path_or_name
    return ""


def _profile_css(theme: dict, position: str = "bottom-right") -> str:
    """커버/CTA에 사용되는 프로필 이미지 관련 CSS"""
    return f"""
    .profile-section {{
        display: flex;
        align-items: center;
        gap: 20px;
        margin-top: 40px;
    }}
    .profile-circle {{
        width: 100px;
        height: 100px;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid {theme['accent']};
        flex-shrink: 0;
    }}
    .profile-circle img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center top;
    }}
    .profile-info {{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}
    .profile-name {{
        font-size: 22px;
        font-weight: bold;
        color: {theme['t1']};
    }}
    .profile-title {{
        font-size: 16px;
        color: {theme['t2']};
    }}
    .logo-img {{
        position: fixed;
        top: 55px;
        left: 80px;
        height: 44px;
        opacity: 0.85;
    }}
    .logo-img-light {{
        filter: brightness(0) invert(1);
    }}
    .logo-img-dark {{
        /* 밝은 테마에서는 원본 사용 */
    }}
    .cta-profile-section {{
        display: flex;
        align-items: center;
        gap: 28px;
        margin-top: 40px;
        justify-content: center;
    }}
    .cta-profile-circle {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid {theme['accent']};
        flex-shrink: 0;
    }}
    .cta-profile-circle img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center top;
    }}
    .cta-contact-info {{
        text-align: left;
    }}
    .cta-contact-info .name {{
        font-size: 24px;
        font-weight: bold;
        color: {theme['t1']};
        margin-bottom: 8px;
    }}
    .cta-contact-info .phone {{
        font-size: 30px;
        font-weight: bold;
        color: {theme['accent']};
        margin-bottom: 6px;
        letter-spacing: 1px;
    }}
    .cta-contact-info .handle {{
        font-size: 18px;
        color: {theme['t3']};
    }}
    """


def _is_dark_theme(theme: dict) -> bool:
    """테마가 어두운 배경인지 판단"""
    bg = theme.get("bg", "")
    # 밝은 테마: clean_light, coral_soft
    light_starts = ["#f8", "#ff", "#fe", "#e9"]
    for s in light_starts:
        if s in bg[:50].lower():
            return False
    return True


def _logo_html(data: dict, theme: dict) -> str:
    """좌상단 로고 HTML"""
    logo_b64 = data.get("_logo_b64", "")
    if not logo_b64:
        return ""
    dark = _is_dark_theme(theme)
    logo_class = "logo-img-light" if dark else "logo-img-dark"
    return f'<img class="logo-img {logo_class}" src="{logo_b64}" />'


def _base_css(theme: dict) -> str:
    """모든 슬라이드에 적용되는 기본 CSS"""
    return f"""
    @page {{ size: 1080px 1080px; margin: 0; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        width: 1080px; height: 1080px;
        font-family: NanumGothic, 'Noto Sans KR', sans-serif;
        background: {theme['bg']};
        color: {theme['t1']};
        padding: 80px;
        position: relative;
        overflow: hidden;
    }}
    .accent {{ color: {theme['accent']}; }}
    .badge {{
        display: inline-block;
        background: {theme['badge_bg']};
        color: {theme['accent']};
        padding: 10px 24px;
        border-radius: 8px;
        font-size: 22px;
        border: 1px solid {theme['badge_bd']};
    }}
    .page-num {{
        position: fixed; top: 70px; right: 80px;
        font-size: 18px; color: {theme['t3']};
        letter-spacing: 2px;
    }}
    .footer {{
        position: fixed; bottom: 55px; left: 80px; right: 80px;
        border-top: 1px solid {theme['divider']};
        padding-top: 18px;
        font-size: 16px; color: {theme['t3']};
    }}
    .footer-flex {{
        display: flex; justify-content: space-between; align-items: center;
    }}
    .top-line {{
        width: 56px; height: 4px; background: {theme['accent']};
        margin-bottom: 44px;
    }}
    .card-box {{
        background: {theme['card_bg']};
        border: 1px solid {theme['card_bd']};
        border-radius: 16px;
        padding: 36px 40px;
    }}
    .big-num {{
        font-size: 160px;
        font-weight: 900;
        color: {theme['num_color']};
        position: absolute;
        top: 40px; right: 60px;
        line-height: 1;
    }}
    """


def _nl(text: str) -> str:
    """\\n을 <br>로 변환"""
    return text.replace("\\n", "<br>").replace("\n", "<br>")


# ──────────────────────────────────────────────
# 슬라이드 타입별 HTML 생성
# ──────────────────────────────────────────────

def slide_cover(data: dict, theme: dict, page_info: str) -> str:
    badge = data.get("badge", "")
    title = _nl(data.get("title", ""))
    subtitle = _nl(data.get("subtitle", ""))
    footer_name = data.get("footer_name", "")
    footer_handle = data.get("footer_handle", "")

    # 프로필/로고 이미지
    profile_b64 = data.get("_profile_b64", "")
    logo_b64 = data.get("_logo_b64", "")
    profile_name = data.get("profile_name", "")
    profile_title_text = data.get("profile_title", "")
    dark = _is_dark_theme(theme)

    # 타이틀에서 highlight 키워드를 accent 색상으로 표시
    highlight = data.get("highlight", "")
    if highlight and highlight in title:
        title = title.replace(highlight, f'<span class="accent">{highlight}</span>')

    # 프로필 섹션 HTML
    profile_html = ""
    if profile_b64:
        profile_html = f"""
        <div class="profile-section">
            <div class="profile-circle">
                <img src="{profile_b64}" />
            </div>
            <div class="profile-info">
                <div class="profile-name">{profile_name}</div>
                <div class="profile-title">{profile_title_text}</div>
            </div>
        </div>"""

    return f"""<html><head><meta charset="utf-8"><style>
    {_base_css(theme)}
    {_profile_css(theme)}
    .content {{ margin-top: {'120px' if profile_b64 else '160px'}; }}
    h1 {{ font-size: 54px; line-height: 1.4; margin-bottom: 36px; letter-spacing: -1px; }}
    .sub {{ font-size: 28px; line-height: 1.8; color: {theme['t2']}; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="top-line"></div>
        <div class="badge">{badge}</div>
        <h1 style="margin-top:40px;">{title}</h1>
        <p class="sub">{subtitle}</p>
        {profile_html}
    </div>
    <div class="footer"><div class="footer-flex">
        <span>{footer_name}</span><span>{footer_handle}</span>
    </div></div>
    </body></html>"""


def slide_problem(data: dict, theme: dict, page_info: str) -> str:
    emoji = data.get("emoji", "⚠️")
    main_text = _nl(data.get("main_text", ""))
    sub_text = _nl(data.get("sub_text", ""))

    return f"""<html><head><meta charset="utf-8"><style>
    {_base_css(theme)}
    .content {{ margin-top: 200px; text-align: center; }}
    .emoji {{ font-size: 72px; margin-bottom: 40px; }}
    h2 {{ font-size: 44px; line-height: 1.5; margin-bottom: 32px; }}
    .sub {{ font-size: 28px; line-height: 1.8; color: {theme['t2']}; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="emoji">{emoji}</div>
        <h2>{main_text}</h2>
        <p class="sub">{sub_text}</p>
    </div>
    <div class="footer"><div class="footer-flex">
        <span>{data.get('footer_name','')}</span><span>{data.get('footer_handle','')}</span>
    </div></div>
    </body></html>"""


def slide_point(data: dict, theme: dict, page_info: str) -> str:
    number = data.get("number", "01")
    heading = _nl(data.get("heading", ""))
    body = _nl(data.get("body", ""))
    highlight = data.get("highlight", "")

    if highlight and highlight in heading:
        heading = heading.replace(highlight, f'<span class="accent">{highlight}</span>')

    return f"""<html><head><meta charset="utf-8"><style>
    {_base_css(theme)}
    .content {{ margin-top: 180px; position: relative; }}
    .num {{ font-size: 120px; font-weight: 900; color: {theme['num_color']};
            line-height: 1; margin-bottom: 20px; }}
    .num-accent {{ color: {theme['accent']}; font-size: 120px; font-weight: 900; opacity: 0.15;
                   position: absolute; top: -30px; left: -10px; }}
    h2 {{ font-size: 46px; line-height: 1.45; margin-bottom: 28px; letter-spacing: -0.5px; }}
    .body {{ font-size: 28px; line-height: 1.8; color: {theme['t2']}; }}
    .accent-line {{ width: 48px; height: 4px; background: {theme['accent']};
                    margin-top: 40px; margin-bottom: 30px; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="num-accent">{number}</div>
        <div style="position:relative; z-index:1;">
            <div class="badge" style="margin-bottom:36px;">POINT {number}</div>
            <h2>{heading}</h2>
            <div class="accent-line"></div>
            <p class="body">{body}</p>
        </div>
    </div>
    <div class="footer"><div class="footer-flex">
        <span>{data.get('footer_name','')}</span><span>{data.get('footer_handle','')}</span>
    </div></div>
    </body></html>"""


def slide_comparison(data: dict, theme: dict, page_info: str) -> str:
    """비교형 카드: left_label, left_items[], right_label, right_items[]"""
    left_label = data.get("left_label", "✕")
    right_label = data.get("right_label", "○")
    left_items = data.get("left_items", [])
    right_items = data.get("right_items", [])
    title = _nl(data.get("title", ""))

    left_html = "".join(f'<div class="item">{_nl(i)}</div>' for i in left_items)
    right_html = "".join(f'<div class="item">{_nl(i)}</div>' for i in right_items)

    return f"""<html><head><meta charset="utf-8"><style>
    {_base_css(theme)}
    .content {{ margin-top: 100px; }}
    h2 {{ font-size: 40px; margin-bottom: 44px; text-align: center; }}
    .columns {{ display: flex; gap: 28px; }}
    .col {{ flex: 1; }}
    .col-header {{ font-size: 28px; font-weight: bold; padding: 18px 0;
                   text-align: center; margin-bottom: 20px; border-radius: 12px; }}
    .col-bad .col-header {{ background: rgba(239,68,68,0.12); color: #ef4444;
                            border: 1px solid rgba(239,68,68,0.2); }}
    .col-good .col-header {{ background: {theme['badge_bg']}; color: {theme['accent']};
                             border: 1px solid {theme['badge_bd']}; }}
    .item {{ font-size: 24px; line-height: 1.6; padding: 14px 20px;
             margin-bottom: 12px; border-radius: 10px;
             background: {theme['card_bg']}; border: 1px solid {theme['card_bd']}; }}
    .col-bad .item {{ color: {theme['t2']}; }}
    .col-good .item {{ color: {theme['t1']}; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <h2>{title}</h2>
        <div class="columns">
            <div class="col col-bad">
                <div class="col-header">{left_label}</div>
                {left_html}
            </div>
            <div class="col col-good">
                <div class="col-header">{right_label}</div>
                {right_html}
            </div>
        </div>
    </div>
    <div class="footer"><div class="footer-flex">
        <span>{data.get('footer_name','')}</span><span>{data.get('footer_handle','')}</span>
    </div></div>
    </body></html>"""


def slide_summary(data: dict, theme: dict, page_info: str) -> str:
    title = _nl(data.get("title", "정리하면"))
    items = data.get("items", [])

    items_html = ""
    for i, item in enumerate(items, 1):
        items_html += f"""
        <div class="check-item">
            <div class="check-num" style="color:{theme['accent']}">{i:02d}</div>
            <div class="check-text">{_nl(item)}</div>
        </div>"""

    return f"""<html><head><meta charset="utf-8"><style>
    {_base_css(theme)}
    .content {{ margin-top: 100px; }}
    h2 {{ font-size: 42px; margin-bottom: 44px; }}
    .check-item {{ display: flex; align-items: flex-start; gap: 20px;
                   padding: 22px 28px; margin-bottom: 14px; border-radius: 14px;
                   background: {theme['card_bg']}; border: 1px solid {theme['card_bd']}; }}
    .check-num {{ font-size: 22px; font-weight: 900; min-width: 36px; padding-top: 2px; }}
    .check-text {{ font-size: 26px; line-height: 1.6; color: {theme['t1']}; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="top-line"></div>
        <h2>{title}</h2>
        {items_html}
    </div>
    <div class="footer"><div class="footer-flex">
        <span>{data.get('footer_name','')}</span><span>{data.get('footer_handle','')}</span>
    </div></div>
    </body></html>"""


def slide_cta(data: dict, theme: dict, page_info: str) -> str:
    message = _nl(data.get("message", ""))
    contact = data.get("contact", "")
    handle = data.get("handle", "")
    name = data.get("name", "")
    sub_message = _nl(data.get("sub_message", "저장🔖하고 필요할 때 꺼내보세요"))

    # 프로필 이미지
    profile_b64 = data.get("_profile_b64", "")

    # 프로필 + 연락처 통합 섹션
    if profile_b64:
        contact_section = f"""
        <div class="cta-profile-section">
            <div class="cta-profile-circle">
                <img src="{profile_b64}" />
            </div>
            <div class="cta-contact-info">
                <div class="name">{name}</div>
                <div class="phone">{contact}</div>
                <div class="handle">{handle}</div>
            </div>
        </div>"""
    else:
        contact_section = f"""
        <div class="contact-box">
            <div class="contact-name">{name}</div>
            <div class="contact-num">{contact}</div>
            <div class="contact-handle">{handle}</div>
        </div>"""

    return f"""<html><head><meta charset="utf-8"><style>
    {_base_css(theme)}
    {_profile_css(theme)}
    .content {{ margin-top: 200px; text-align: center; }}
    h2 {{ font-size: 42px; line-height: 1.5; margin-bottom: 36px; }}
    .sub-msg {{ font-size: 24px; color: {theme['t2']}; margin-bottom: 50px; line-height: 1.7; }}
    .contact-box {{ background: {theme['card_bg']}; border: 1px solid {theme['card_bd']};
                    border-radius: 16px; padding: 36px 48px; display: inline-block; }}
    .contact-name {{ font-size: 22px; color: {theme['t2']}; margin-bottom: 12px; }}
    .contact-num {{ font-size: 32px; font-weight: bold; color: {theme['accent']};
                    margin-bottom: 8px; letter-spacing: 1px; }}
    .contact-handle {{ font-size: 20px; color: {theme['t3']}; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <h2>{message}</h2>
        <p class="sub-msg">{sub_message}</p>
        {contact_section}
    </div>
    <div class="footer"><div class="footer-flex">
        <span>{name}</span><span>{handle}</span>
    </div></div>
    </body></html>"""


# 슬라이드 타입 → 렌더 함수 매핑
RENDERERS = {
    "cover": slide_cover,
    "problem": slide_problem,
    "point": slide_point,
    "comparison": slide_comparison,
    "summary": slide_summary,
    "cta": slide_cta,
}


# ──────────────────────────────────────────────
# 렌더링 파이프라인
# ──────────────────────────────────────────────

def ensure_fonts():
    """한글 폰트가 fontconfig에 등록되어 있는지 확인하고, 없으면 설치"""
    result = subprocess.run(["fc-list"], capture_output=True, text=True)
    if "NanumGothic" in result.stdout:
        return True

    try:
        import koreanize_matplotlib
        import shutil
        src = os.path.dirname(koreanize_matplotlib.__file__) + "/fonts"
        dst = os.path.expanduser("~/.fonts")
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            if f.endswith(".ttf"):
                shutil.copy2(os.path.join(src, f), dst)
        subprocess.run(["fc-cache", "-f", dst], check=True)
        print("✅ NanumGothic 폰트 설치 완료")
        return True
    except Exception as e:
        print(f"⚠️ 폰트 설치 실패: {e}")
        print("pip install koreanize-matplotlib --break-system-packages")
        return False


def render_single_card(html_str: str, output_png: str, size: int = 1080):
    """단일 HTML → PNG 렌더링"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name

    try:
        HTML(string=html_str).write_pdf(pdf_path)

        png_base = output_png.replace(".png", "")
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", "-singlefile", pdf_path, png_base],
            check=True, capture_output=True,
        )

        raw_png = png_base + ".png"
        img = Image.open(raw_png)
        if img.size != (size, size):
            img = img.resize((size, size), Image.LANCZOS)
            img.save(raw_png, quality=95)

        return raw_png
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def render_card_news(
    slides: list,
    output_dir: str,
    theme: str = "dark_professional",
    prefix: str = "card",
    footer_name: str = "",
    footer_handle: str = "",
    size: int = 1080,
    profile_image: str = "",
    logo_image: str = "",
    assets_dir: str = "",
    profile_name: str = "",
    profile_title: str = "",
) -> list:
    """
    카드뉴스 전체 렌더링

    Args:
        slides: 슬라이드 데이터 리스트
        output_dir: 출력 디렉토리
        theme: 테마 이름 (THEMES 키)
        prefix: 출력 파일 접두어
        footer_name: 전체 슬라이드 공통 푸터 이름
        footer_handle: 전체 슬라이드 공통 푸터 핸들
        size: 출력 이미지 크기 (정사각형)
        profile_image: 프로필 사진 경로/파일명 (cover/cta에 자동 삽입)
                      "cover:파일명" 또는 "cta:파일명"으로 슬라이드별 지정 가능
                      또는 PROFILE_PHOTOS 키 (cover, cta, side, smile)
        logo_image: 로고 이미지 경로/파일명
        assets_dir: 이미지 파일이 있는 디렉토리
        profile_name: 프로필 이름 (커버 하단 표시)
        profile_title: 프로필 직함 (커버 하단 표시)

    Returns:
        생성된 PNG 파일 경로 리스트
    """
    ensure_fonts()

    os.makedirs(output_dir, exist_ok=True)

    theme_data = THEMES.get(theme, THEMES["dark_professional"])
    total = len(slides)
    output_files = []

    # 프로필/로고 이미지 미리 base64 인코딩
    # profile_image가 딕셔너리 형태 {"cover": "path", "cta": "path"} 또는 단일 문자열
    profile_b64_map = {}
    if isinstance(profile_image, dict):
        for key, path in profile_image.items():
            resolved = _resolve_image(path, assets_dir)
            if not resolved and path in PROFILE_PHOTOS:
                resolved = _resolve_image(PROFILE_PHOTOS[path], assets_dir)
            if resolved:
                profile_b64_map[key] = _img_to_base64(resolved)
    elif profile_image:
        # 단일 문자열: PROFILE_PHOTOS 키 또는 경로
        if profile_image in PROFILE_PHOTOS:
            # 기본 키 → cover/cta 각각 매핑
            for stype in ["cover", "cta"]:
                photo_file = PROFILE_PHOTOS.get(stype, PROFILE_PHOTOS.get("cover", ""))
                resolved = _resolve_image(photo_file, assets_dir)
                if resolved:
                    profile_b64_map[stype] = _img_to_base64(resolved)
        else:
            resolved = _resolve_image(profile_image, assets_dir)
            if resolved:
                b64 = _img_to_base64(resolved)
                profile_b64_map["cover"] = b64
                profile_b64_map["cta"] = b64

    # "auto" 모드: assets_dir에서 자동 탐색
    if profile_image == "auto" and assets_dir:
        for stype, filename in PROFILE_PHOTOS.items():
            resolved = _resolve_image(filename, assets_dir)
            if resolved:
                profile_b64_map[stype] = _img_to_base64(resolved)

    logo_b64 = ""
    if logo_image:
        resolved = _resolve_image(logo_image, assets_dir)
        if not resolved:
            resolved = _resolve_image(LOGO_FILE, assets_dir)
        if resolved:
            logo_b64 = _img_to_base64(resolved)
    elif logo_image == "" and assets_dir:
        # assets_dir에 기본 로고가 있으면 자동 사용 (명시적 빈 문자열이 아닌 None 체크)
        pass

    for idx, slide in enumerate(slides):
        slide_type = slide.get("type", "point")
        renderer = RENDERERS.get(slide_type)

        if not renderer:
            print(f"⚠️ 알 수 없는 슬라이드 타입: {slide_type}, point로 대체")
            renderer = RENDERERS["point"]

        # 공통 푸터 정보 주입
        if footer_name and "footer_name" not in slide:
            slide["footer_name"] = footer_name
        if footer_handle and "footer_handle" not in slide:
            slide["footer_handle"] = footer_handle

        # 모든 슬라이드에 로고 주입
        if logo_b64 and "_logo_b64" not in slide:
            slide["_logo_b64"] = logo_b64

        # cover/cta 슬라이드에 프로필 이미지 주입
        if slide_type in ("cover", "cta"):
            if slide_type in profile_b64_map and "_profile_b64" not in slide:
                slide["_profile_b64"] = profile_b64_map[slide_type]
            if profile_name and "profile_name" not in slide:
                slide["profile_name"] = profile_name
            if profile_title and "profile_title" not in slide:
                slide["profile_title"] = profile_title

        page_info = f"{idx + 1} / {total}"
        html_str = renderer(slide, theme_data, page_info)

        filename = f"{prefix}_{idx + 1:02d}_{slide_type}.png"
        output_path = os.path.join(output_dir, filename)

        render_single_card(html_str, output_path, size)
        output_files.append(output_path)
        print(f"  ✅ [{idx + 1}/{total}] {filename}")

    print(f"\n🎉 카드뉴스 {total}장 생성 완료 → {output_dir}")
    return output_files


# ──────────────────────────────────────────────
# CLI 진입점
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="인스타그램 카드뉴스 생성기")
    parser.add_argument("--slides", required=True, help="슬라이드 JSON 파일 경로")
    parser.add_argument("--output-dir", default="./output", help="출력 디렉토리")
    parser.add_argument("--theme", default="dark_professional",
                        choices=list(THEMES.keys()), help="컬러 테마")
    parser.add_argument("--prefix", default="card", help="출력 파일 접두어")
    parser.add_argument("--footer-name", default="", help="공통 푸터 이름")
    parser.add_argument("--footer-handle", default="", help="공통 푸터 핸들")
    parser.add_argument("--size", type=int, default=1080, help="이미지 크기 (px)")
    parser.add_argument("--profile-image", default="", help="프로필 사진 경로 또는 'auto'")
    parser.add_argument("--logo-image", default="", help="로고 이미지 경로")
    parser.add_argument("--assets-dir", default="", help="이미지 파일 디렉토리")
    parser.add_argument("--profile-name", default="", help="프로필 이름")
    parser.add_argument("--profile-title", default="", help="프로필 직함")

    args = parser.parse_args()

    with open(args.slides, "r", encoding="utf-8") as f:
        data = json.load(f)

    # JSON에서 설정 읽기 (CLI 인자 우선)
    slides = data.get("slides", data) if isinstance(data, dict) else data
    theme = args.theme or data.get("theme", "dark_professional")
    prefix = args.prefix or data.get("prefix", "card")

    render_card_news(
        slides=slides,
        output_dir=args.output_dir,
        theme=theme,
        prefix=prefix,
        footer_name=args.footer_name or data.get("footer_name", ""),
        footer_handle=args.footer_handle or data.get("footer_handle", ""),
        size=args.size,
        profile_image=args.profile_image or data.get("profile_image", ""),
        logo_image=args.logo_image or data.get("logo_image", ""),
        assets_dir=args.assets_dir or data.get("assets_dir", ""),
        profile_name=args.profile_name or data.get("profile_name", ""),
        profile_title=args.profile_title or data.get("profile_title", ""),
    )


if __name__ == "__main__":
    main()
