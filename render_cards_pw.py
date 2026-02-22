#!/usr/bin/env python3
"""
카드뉴스 렌더링: HTML 생성 → Playwright 스크린샷 (WeasyPrint 대체)
Windows 환경에서 GTK 없이 동작
"""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# 테마
# ──────────────────────────────────────────────

THEMES = {
    "dark_professional": {
        "bg": "linear-gradient(160deg, #0c1220 0%, #1a2744 40%, #0f3460 100%)",
        "accent": "#e94560",
        "accent_sub": "#e94560",
        "t1": "#ffffff",
        "t2": "#8899aa",
        "t3": "#445566",
        "badge_bg": "rgba(233,69,96,0.15)",
        "badge_bd": "rgba(233,69,96,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.05)",
        "card_bd": "rgba(255,255,255,0.08)",
        "num_color": "rgba(233,69,96,0.12)",
        "glass_bg": "rgba(255,255,255,0.05)",
        "glass_bd": "rgba(255,255,255,0.10)",
        "glass_blur": "12px",
    },
    "aegis_brand": {
        # 배경: 딥 네이비 그라디언트 (CTA 배너 톤 계승)
        "bg": "linear-gradient(160deg, #0f1923 0%, #1B2B48 45%, #1a3a5c 100%)",
        # 액센트: 브랜드 골드
        "accent": "#D4AF37",
        # 서브 액센트: 로즈골드
        "accent_sub": "#C9956B",
        # 텍스트
        "t1": "#FFFFFF",
        "t2": "#A0B4C8",       # 실버블루 (Pantone 877C 톤 반영)
        "t3": "#5A7088",
        # 뱃지
        "badge_bg": "rgba(212,175,55,0.12)",
        "badge_bd": "rgba(212,175,55,0.30)",
        # 디바이더 & 카드
        "divider": "rgba(255,255,255,0.06)",
        "card_bg": "rgba(255,255,255,0.04)",
        "card_bd": "rgba(212,175,55,0.10)",
        # 넘버 워터마크
        "num_color": "rgba(212,175,55,0.08)",
        # 글래스모피즘
        "glass_bg": "rgba(255,255,255,0.06)",
        "glass_bd": "rgba(255,255,255,0.12)",
        "glass_blur": "12px",
    },
}


# ──────────────────────────────────────────────
# 이미지 헬퍼
# ──────────────────────────────────────────────

def _img_to_base64(img_path: str) -> str:
    if not img_path or not os.path.exists(img_path):
        return ""
    ext = os.path.splitext(img_path)[1].lower().lstrip(".")
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    mime_type = mime_map.get(ext, "image/png")
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _resolve_image(path_or_name: str, assets_dir: str = "") -> str:
    if not path_or_name:
        return ""
    if os.path.isabs(path_or_name) and os.path.exists(path_or_name):
        return path_or_name
    if assets_dir:
        candidate = os.path.join(assets_dir, path_or_name)
        if os.path.exists(candidate):
            return candidate
    if os.path.exists(path_or_name):
        return path_or_name
    return ""


def _is_dark_theme(theme: dict) -> bool:
    bg = theme.get("bg", "")
    for s in ["#f8", "#ff", "#fe", "#e9"]:
        if s in bg[:50].lower():
            return False
    return True


def _nl(text: str) -> str:
    return text.replace("\\n", "<br>").replace("\n", "<br>")


def _dot_indicator(current: int, total: int) -> str:
    """우하단 도트 페이지 인디케이터 HTML"""
    if total <= 0:
        return ""
    dots = []
    for i in range(1, total + 1):
        cls = "dot active" if i == current else "dot"
        dots.append(f'<div class="{cls}"></div>')
    return f'<div class="dot-indicator">{"".join(dots)}</div>'


def _logo_html(data: dict, theme: dict) -> str:
    """좌상단 로고 HTML"""
    logo_b64 = data.get("_logo_b64", "")
    if not logo_b64:
        return ""
    dark = _is_dark_theme(theme)
    logo_class = "logo-img-light" if dark else ""
    return f'<img class="logo-img {logo_class}" src="{logo_b64}" />'


def _footer_html(data: dict, theme: dict) -> str:
    """브랜드 푸터 (방패 아이콘 포함)"""
    name = data.get('footer_name', '')
    handle = data.get('footer_handle', '')
    return f"""<div class="footer"><div class="footer-flex">
        <div class="footer-brand"><span class="footer-shield"></span><span>{name}</span></div>
        <span>{handle}</span>
    </div></div>"""


# ──────────────────────────────────────────────
# 공통 CSS
# ──────────────────────────────────────────────

def _base_css(theme: dict, current_page: int = 0, total_pages: int = 0) -> str:
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    glass_bg = theme.get('glass_bg', 'rgba(255,255,255,0.06)')
    glass_bd = theme.get('glass_bd', 'rgba(255,255,255,0.12)')
    glass_blur = theme.get('glass_blur', '12px')

    # 도트 인디케이터 HTML용 CSS
    dots_css = ""
    if total_pages > 0:
        dots_css = f"""
    .dot-indicator {{
        position: absolute; bottom: 78px; right: 80px;
        display: flex; gap: 8px; align-items: center; z-index: 10;
    }}
    .dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {theme['t3']}; opacity: 0.4;
        transition: all 0.3s;
    }}
    .dot.active {{
        width: 24px; border-radius: 4px;
        background: linear-gradient(90deg, {accent}, {accent_sub});
        opacity: 1;
    }}"""

    return f"""
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html {{
        width: 1080px; height: 1080px;
        overflow: hidden;
    }}
    body {{
        width: 1080px; height: 1080px;
        font-family: 'Pretendard', 'Pretendard Variable', 'Malgun Gothic', 'NanumGothic', 'Noto Sans KR', sans-serif;
        background: {theme['bg']};
        color: {theme['t1']};
        padding: 80px;
        position: relative;
        overflow: hidden;
        word-break: keep-all;
        overflow-wrap: break-word;
    }}
    .accent {{ color: {accent}; }}
    .gold-underline {{
        text-decoration: none;
        background-image: linear-gradient(90deg, {accent}, {accent_sub});
        background-position: 0 88%;
        background-size: 100% 6px;
        background-repeat: no-repeat;
        padding-bottom: 4px;
    }}
    .gold-marker {{
        background: linear-gradient(180deg, transparent 55%, rgba(212,175,55,0.25) 55%);
        padding: 0 2px;
    }}
    .badge {{
        display: inline-block;
        background: {theme['badge_bg']};
        color: {accent};
        padding: 10px 24px;
        border-radius: 8px;
        font-size: 22px;
        border: 1px solid {theme['badge_bd']};
        font-weight: bold;
        letter-spacing: 1px;
        box-shadow: 0 0 20px rgba(212,175,55,0.15);
    }}
    .badge::before {{
        content: '\u25C6';
        margin-right: 8px;
        font-size: 14px;
        opacity: 0.7;
    }}
    .page-num {{
        position: absolute; top: 50px; right: 60px;
        font-size: 18px; color: {theme['t3']};
        letter-spacing: 2px;
    }}
    .footer {{
        position: absolute; bottom: 40px; left: 80px; right: 80px;
        border-top: 1px solid {theme['divider']};
        padding-top: 16px;
        font-size: 16px; color: {theme['t3']};
    }}
    .footer-flex {{
        display: flex; justify-content: space-between; align-items: center;
    }}
    .footer-brand {{
        display: flex; align-items: center; gap: 8px;
    }}
    .footer-shield {{
        display: inline-block;
        width: 16px; height: 18px;
        background: linear-gradient(180deg, {accent}, {accent_sub});
        clip-path: polygon(50% 0%, 100% 20%, 100% 70%, 50% 100%, 0% 70%, 0% 20%);
        opacity: 0.35;
    }}
    .top-line {{
        width: 56px; height: 4px;
        background: linear-gradient(90deg, {accent}, {accent_sub});
        margin-bottom: 36px;
        border-radius: 2px;
    }}
    .divider-line {{
        height: 1px;
        background: linear-gradient(90deg, {accent}, transparent);
        opacity: 0.3;
    }}
    .card-box {{
        background: {theme['card_bg']};
        border: 1px solid {theme['card_bd']};
        border-radius: 16px;
        padding: 36px 40px;
    }}
    .glass {{
        background: {glass_bg};
        border: 1px solid {glass_bd};
        border-radius: 16px;
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
    }}
    .glass-chip {{
        display: inline-block;
        background: {glass_bg};
        border: 1px solid {glass_bd};
        border-radius: 40px;
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
        padding: 10px 24px;
    }}
    .logo-img {{
        position: absolute;
        top: 48px;
        left: 80px;
        height: 44px;
        opacity: 0.85;
    }}
    .logo-img-light {{
        filter: brightness(0) invert(1);
    }}
    {dots_css}
    """


# ──────────────────────────────────────────────
# 슬라이드 HTML 생성
# ──────────────────────────────────────────────

def slide_cover(data, theme, page_info):
    badge = data.get("badge", "")
    title = _nl(data.get("title", ""))
    subtitle = _nl(data.get("subtitle", ""))
    highlight = data.get("highlight", "")
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    cur, total = data.get("_page_cur", 0), data.get("_page_total", 0)

    # 하이라이트: 골드 언더라인 스타일
    if highlight and highlight in title:
        title = title.replace(highlight, f'<span class="gold-underline">{highlight}</span>')

    profile_b64 = data.get("_profile_b64", "")

    profile_html = ""
    if profile_b64:
        profile_html = f"""
        <div class="cover-profile">
            <img src="{profile_b64}" />
        </div>
        <div class="cover-profile-info">
            <div class="glass-chip cp-chip">
                <div class="cp-name">{data.get('profile_name', '')}</div>
                <div class="cp-title">{data.get('profile_title', '')}</div>
            </div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    {_base_css(theme, cur, total)}
    /* 방패 워터마크 */
    body::after {{
        content: '';
        position: absolute;
        right: -40px; bottom: -40px;
        width: 400px; height: 460px;
        background: linear-gradient(180deg, {accent}, {accent_sub});
        clip-path: polygon(50% 0%, 100% 20%, 100% 70%, 50% 100%, 0% 70%, 0% 20%);
        opacity: 0.04;
        z-index: 0;
    }}
    .content {{
        margin-top: 120px;
        max-width: 600px;
        position: relative;
        z-index: 2;
    }}
    h1 {{
        font-size: 52px; line-height: 1.35; margin-bottom: 32px;
        letter-spacing: -1.5px; font-weight: 900;
    }}
    .sub {{ font-size: 28px; line-height: 1.75; color: {theme['t2']}; letter-spacing: 0.3px; }}
    .cover-profile {{
        position: absolute;
        right: -30px;
        bottom: 80px;
        width: 520px;
        z-index: 1;
    }}
    .cover-profile img {{
        width: 100%;
        height: auto;
        object-fit: contain;
    }}
    .cover-profile-info {{
        position: absolute;
        bottom: 100px;
        right: 80px;
        z-index: 3;
        text-align: right;
    }}
    .cp-chip {{
        text-align: right;
    }}
    .cp-name {{
        font-size: 24px;
        font-weight: bold;
        color: {theme['t1']};
    }}
    .cp-title {{
        font-size: 15px;
        color: {theme['t2']};
        margin-top: 4px;
    }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    {profile_html}
    <div class="content">
        <div class="top-line"></div>
        <div class="badge">{badge}</div>
        <h1 style="margin-top:36px;">{title}</h1>
        <p class="sub">{subtitle}</p>
    </div>
    {_footer_html(data, theme)}
    {_dot_indicator(cur, total)}
    </body></html>"""


def slide_problem(data, theme, page_info):
    emoji = data.get("emoji", "")
    main_text = _nl(data.get("main_text", ""))
    sub_text = _nl(data.get("sub_text", ""))
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    cur, total = data.get("_page_cur", 0), data.get("_page_total", 0)

    # 핵심 키워드 골드 하이라이트
    highlight = data.get("highlight", "")
    if highlight and highlight in main_text:
        main_text = main_text.replace(highlight, f'<span class="gold-marker">{highlight}</span>')

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    {_base_css(theme, cur, total)}
    .content {{ margin-top: 200px; text-align: center; }}
    .emoji-container {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 120px; height: 120px;
        border-radius: 50%;
        background: {theme.get('glass_bg', 'rgba(255,255,255,0.06)')};
        border: 1px solid {theme.get('glass_bd', 'rgba(255,255,255,0.12)')};
        backdrop-filter: blur({theme.get('glass_blur', '12px')});
        -webkit-backdrop-filter: blur({theme.get('glass_blur', '12px')});
        margin-bottom: 40px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }}
    .emoji {{ font-size: 56px; }}
    h2 {{
        font-size: 44px; line-height: 1.45; margin-bottom: 32px;
        font-weight: 900; letter-spacing: -1.5px;
    }}
    .sub {{ font-size: 28px; line-height: 1.75; color: {theme['t2']}; letter-spacing: 0.3px; }}
    .swipe-hint {{
        position: absolute;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        display: flex; align-items: center; gap: 8px;
        color: {theme['t3']};
        font-size: 16px;
        letter-spacing: 1px;
    }}
    .swipe-arrow {{
        display: inline-block;
        width: 24px; height: 2px;
        background: linear-gradient(90deg, {accent}, transparent);
        position: relative;
    }}
    .swipe-arrow::after {{
        content: '';
        position: absolute; right: 0; top: -4px;
        border: solid {accent};
        border-width: 0 2px 2px 0;
        padding: 3px;
        transform: rotate(-45deg);
    }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="emoji-container"><span class="emoji">{emoji}</span></div>
        <h2>{main_text}</h2>
        <p class="sub">{sub_text}</p>
    </div>
    <div class="swipe-hint">
        <span>\u2192 \uc2a4\uc640\uc774\ud504\ud574\uc11c \ud655\uc778\ud558\uc138\uc694</span>
    </div>
    {_footer_html(data, theme)}
    {_dot_indicator(cur, total)}
    </body></html>"""


def slide_point(data, theme, page_info):
    number = data.get("number", "01")
    heading = _nl(data.get("heading", ""))
    body = _nl(data.get("body", ""))
    highlight = data.get("highlight", "")
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    cur, total = data.get("_page_cur", 0), data.get("_page_total", 0)

    # 하이라이트: 골드 마커
    if highlight and highlight in heading:
        heading = heading.replace(highlight, f'<span class="gold-marker">{highlight}</span>')

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    {_base_css(theme, cur, total)}
    .content {{ margin-top: 180px; position: relative; }}
    .num-watermark {{
        color: {theme.get('num_color', 'rgba(212,175,55,0.08)')};
        font-size: 180px; font-weight: 900;
        position: absolute; top: -60px; right: 20px;
        line-height: 1; z-index: 0;
        font-variant-numeric: tabular-nums;
    }}
    .point-header {{
        display: flex; align-items: center; gap: 20px;
        margin-bottom: 36px;
        position: relative; z-index: 1;
    }}
    .point-number {{
        font-size: 56px; font-weight: 900;
        color: {accent};
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }}
    .point-number-line {{
        width: 1px; height: 48px;
        background: linear-gradient(180deg, {accent}, transparent);
    }}
    h2 {{
        font-size: 44px; line-height: 1.35; margin-bottom: 28px;
        letter-spacing: -1.5px; font-weight: 900;
        position: relative; z-index: 1;
    }}
    .body-card {{
        position: relative; z-index: 1;
        padding: 32px 36px;
        border-radius: 16px;
        background: {theme.get('glass_bg', 'rgba(255,255,255,0.06)')};
        border: 1px solid {theme.get('glass_bd', 'rgba(255,255,255,0.12)')};
        backdrop-filter: blur({theme.get('glass_blur', '12px')});
        -webkit-backdrop-filter: blur({theme.get('glass_blur', '12px')});
        border-left: 4px solid {accent};
    }}
    .body {{ font-size: 28px; line-height: 1.75; color: {theme['t2']}; letter-spacing: 0.3px; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="num-watermark">{number}</div>
        <div class="point-header">
            <div class="point-number">{number}</div>
            <div class="point-number-line"></div>
            <div class="badge">POINT {number}</div>
        </div>
        <h2>{heading}</h2>
        <div class="body-card">
            <p class="body">{body}</p>
        </div>
    </div>
    {_footer_html(data, theme)}
    {_dot_indicator(cur, total)}
    </body></html>"""


def slide_comparison(data, theme, page_info):
    left_label = data.get("left_label", "")
    right_label = data.get("right_label", "")
    left_items = data.get("left_items", [])
    right_items = data.get("right_items", [])
    title = _nl(data.get("title", ""))
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    cur, total = data.get("_page_cur", 0), data.get("_page_total", 0)

    left_html = "".join(
        f'<div class="item"><span class="item-num">{i+1}</span>{_nl(v)}</div>'
        for i, v in enumerate(left_items)
    )
    right_html = "".join(
        f'<div class="item"><span class="item-num">{i+1}</span>{_nl(v)}</div>'
        for i, v in enumerate(right_items)
    )

    glass_bg = theme.get('glass_bg', 'rgba(255,255,255,0.06)')
    glass_bd = theme.get('glass_bd', 'rgba(255,255,255,0.12)')
    glass_blur = theme.get('glass_blur', '12px')

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    {_base_css(theme, cur, total)}
    .content {{ margin-top: 100px; }}
    h2 {{
        font-size: 40px; margin-bottom: 44px; text-align: center;
        font-weight: 900; letter-spacing: -1.5px;
    }}
    .columns {{ display: flex; gap: 20px; position: relative; }}
    .col {{ flex: 1; }}
    /* VS 디바이더 */
    .vs-divider {{
        position: absolute;
        left: 50%; top: 50%;
        transform: translate(-50%, -50%);
        width: 48px; height: 48px;
        background: linear-gradient(135deg, {accent}, {accent_sub});
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; font-weight: 900; color: #0f1923;
        z-index: 5;
        box-shadow: 0 4px 20px rgba(212,175,55,0.3);
    }}
    .col-header {{
        font-size: 24px; font-weight: bold; padding: 16px 0;
        text-align: center; margin-bottom: 18px; border-radius: 12px;
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
    }}
    .col-left .col-header {{
        background: rgba(100,149,237,0.10);
        color: #7EB3FF;
        border: 1px solid rgba(100,149,237,0.20);
    }}
    .col-right .col-header {{
        background: {theme['badge_bg']};
        color: {accent};
        border: 1px solid {theme['badge_bd']};
    }}
    .col-left .item {{
        background: rgba(100,149,237,0.06);
        border: 1px solid rgba(100,149,237,0.12);
    }}
    .col-right .item {{
        background: rgba(212,175,55,0.06);
        border: 1px solid rgba(212,175,55,0.12);
    }}
    .item {{
        font-size: 24px; line-height: 1.6; padding: 16px 20px;
        margin-bottom: 10px; border-radius: 12px;
        color: {theme['t2']};
        display: flex; align-items: flex-start; gap: 12px;
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
    }}
    .col-right .item {{ color: {theme['t1']}; }}
    .item-num {{
        min-width: 24px; height: 24px;
        border-radius: 6px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 800;
        flex-shrink: 0; margin-top: 2px;
    }}
    .col-left .item-num {{
        background: rgba(100,149,237,0.15);
        color: #7EB3FF;
    }}
    .col-right .item-num {{
        background: rgba(212,175,55,0.15);
        color: {accent};
    }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="top-line" style="margin: 0 auto 36px auto;"></div>
        <h2>{title}</h2>
        <div class="columns">
            <div class="col col-left">
                <div class="col-header">{left_label}</div>
                {left_html}
            </div>
            <div class="vs-divider">\u2192</div>
            <div class="col col-right">
                <div class="col-header">{right_label}</div>
                {right_html}
            </div>
        </div>
    </div>
    {_footer_html(data, theme)}
    {_dot_indicator(cur, total)}
    </body></html>"""


def slide_summary(data, theme, page_info):
    title = _nl(data.get("title", ""))
    items = data.get("items", [])
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    cur, total = data.get("_page_cur", 0), data.get("_page_total", 0)
    glass_bg = theme.get('glass_bg', 'rgba(255,255,255,0.06)')
    glass_bd = theme.get('glass_bd', 'rgba(255,255,255,0.12)')
    glass_blur = theme.get('glass_blur', '12px')

    items_html = ""
    for i, item in enumerate(items, 1):
        items_html += f"""
        <div class="check-item">
            <div class="check-badge">{i:02d}</div>
            <div class="check-content">
                <span class="check-icon">\u2713</span>
                <span class="check-text">{_nl(item)}</span>
            </div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    {_base_css(theme, cur, total)}
    .content {{ margin-top: 100px; }}
    h2 {{
        font-size: 42px; margin-bottom: 40px;
        font-weight: 900; letter-spacing: -1.5px;
    }}
    .check-item {{
        display: flex; align-items: flex-start; gap: 18px;
        padding: 20px 24px; margin-bottom: 10px; border-radius: 14px;
        background: {glass_bg};
        border: 1px solid {glass_bd};
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
    }}
    .check-badge {{
        min-width: 36px; height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, {accent}, {accent_sub});
        color: #0f1923;
        font-size: 15px; font-weight: 900;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        font-variant-numeric: tabular-nums;
    }}
    .check-content {{
        display: flex; align-items: flex-start; gap: 10px;
        padding-top: 4px;
    }}
    .check-icon {{
        color: {accent};
        font-size: 18px;
        font-weight: 900;
        flex-shrink: 0;
        margin-top: 2px;
    }}
    .check-text {{
        font-size: 26px; line-height: 1.6;
        color: {theme['t1']};
        letter-spacing: 0.3px;
    }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="content">
        <div class="top-line"></div>
        <h2>{title}</h2>
        {items_html}
    </div>
    {_footer_html(data, theme)}
    {_dot_indicator(cur, total)}
    </body></html>"""


def slide_cta(data, theme, page_info):
    message = _nl(data.get("message", ""))
    contact = data.get("contact", "")
    handle = data.get("handle", "")
    name = data.get("name", "")
    sub_message = _nl(data.get("sub_message", ""))
    accent = theme['accent']
    accent_sub = theme.get('accent_sub', accent)
    cur, total = data.get("_page_cur", 0), data.get("_page_total", 0)

    profile_b64 = data.get("_profile_b64", "")

    glass_bg = theme.get('glass_bg', 'rgba(255,255,255,0.06)')
    glass_bd = theme.get('glass_bd', 'rgba(255,255,255,0.12)')
    glass_blur = theme.get('glass_blur', '12px')

    if profile_b64:
        profile_html = f"""
        <div class="cta-profile-cutout">
            <img src="{profile_b64}" />
        </div>"""
        contact_section = f"""
        <div class="cta-right">
            <h2>{message}</h2>
            <p class="sub-msg">{sub_message}</p>
            <div class="cta-contact-box">
                <div class="cta-name">{name}</div>
                <div class="cta-phone-btn">
                    <span class="phone-icon">\u260E</span>
                    <span>{contact}</span>
                </div>
                <div class="cta-handle">{handle}</div>
            </div>
        </div>"""
    else:
        profile_html = ""
        contact_section = f"""
        <div class="cta-center">
            <h2>{message}</h2>
            <p class="sub-msg">{sub_message}</p>
            <div class="cta-contact-box-center">
                <div class="cta-name">{name}</div>
                <div class="cta-phone-btn">
                    <span class="phone-icon">\u260E</span>
                    <span>{contact}</span>
                </div>
                <div class="cta-handle">{handle}</div>
            </div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    {_base_css(theme, cur, total)}
    /* 방패 워터마크 */
    body::after {{
        content: '';
        position: absolute;
        right: -40px; bottom: -40px;
        width: 360px; height: 420px;
        background: linear-gradient(180deg, {accent}, {accent_sub});
        clip-path: polygon(50% 0%, 100% 20%, 100% 70%, 50% 100%, 0% 70%, 0% 20%);
        opacity: 0.03;
        z-index: 0;
    }}
    .cta-layout {{
        display: flex;
        align-items: center;
        height: 920px;
        position: relative;
    }}
    .cta-profile-cutout {{
        position: absolute;
        left: -40px;
        bottom: 10px;
        width: 540px;
        z-index: 10;
    }}
    .cta-profile-cutout img {{
        width: 100%;
        height: auto;
    }}
    .cta-right {{
        margin-left: 450px;
        z-index: 2;
        max-width: 540px;
    }}
    .cta-right h2 {{
        font-size: 38px;
        line-height: 1.45;
        margin-bottom: 24px;
        font-weight: 900;
        letter-spacing: -1.5px;
    }}
    .cta-right .sub-msg {{
        font-size: 24px;
        color: {theme['t2']};
        margin-bottom: 36px;
        line-height: 1.75;
        letter-spacing: 0.3px;
    }}
    .cta-contact-box {{
        background: {glass_bg};
        border: 1px solid rgba(212,175,55,0.20);
        border-radius: 16px;
        padding: 28px 36px;
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
    }}
    .cta-name {{
        font-size: 22px; color: {theme['t2']}; margin-bottom: 16px;
    }}
    .cta-phone-btn {{
        display: inline-flex; align-items: center; gap: 12px;
        background: linear-gradient(135deg, rgba(212,175,55,0.15), rgba(212,175,55,0.08));
        border: 1px solid rgba(212,175,55,0.30);
        border-radius: 12px;
        padding: 16px 28px;
        margin-bottom: 12px;
    }}
    .cta-phone-btn span {{
        font-size: 30px; font-weight: 900; color: {accent};
        letter-spacing: 1px;
    }}
    .phone-icon {{
        font-size: 24px !important;
    }}
    .cta-handle {{
        font-size: 18px; color: {accent_sub};
        font-weight: 600;
    }}
    .cta-center {{
        width: 100%;
        text-align: center;
        margin-top: 160px;
    }}
    .cta-center h2 {{
        font-size: 42px;
        line-height: 1.45;
        margin-bottom: 28px;
        font-weight: 900;
        letter-spacing: -1.5px;
    }}
    .cta-center .sub-msg {{
        font-size: 22px;
        color: {theme['t2']};
        margin-bottom: 48px;
        line-height: 1.75;
    }}
    .cta-contact-box-center {{
        background: {glass_bg};
        border: 1px solid rgba(212,175,55,0.20);
        border-radius: 16px;
        padding: 32px 48px;
        display: inline-block;
        backdrop-filter: blur({glass_blur});
        -webkit-backdrop-filter: blur({glass_blur});
    }}
    .cta-contact-box-center .cta-name {{ font-size: 22px; color: {theme['t2']}; margin-bottom: 16px; }}
    .cta-contact-box-center .cta-phone-btn {{ margin-bottom: 12px; }}
    .cta-contact-box-center .cta-handle {{ font-size: 20px; color: {accent_sub}; }}
    </style></head><body>
    {_logo_html(data, theme)}
    <div class="page-num">{page_info}</div>
    <div class="cta-layout">
        {profile_html}
        {contact_section}
    </div>
    <div class="footer" {'style="left:520px;"' if profile_b64 else ''}><div class="footer-flex">
        <div class="footer-brand"><span class="footer-shield"></span><span>{name}</span></div>
        <span>{handle}</span>
    </div></div>
    {_dot_indicator(cur, total)}
    </body></html>"""


RENDERERS = {
    "cover": slide_cover,
    "problem": slide_problem,
    "point": slide_point,
    "comparison": slide_comparison,
    "summary": slide_summary,
    "cta": slide_cta,
}


# ──────────────────────────────────────────────
# 메인 파이프라인
# ──────────────────────────────────────────────

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    slides_path = sys.argv[1] if len(sys.argv) > 1 else "부당전보_카드뉴스_slides.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output/부당전보_카드뉴스"

    with open(slides_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    slides = data.get("slides", data) if isinstance(data, dict) else data
    theme_name = data.get("theme", "dark_professional") if isinstance(data, dict) else "dark_professional"
    theme = THEMES.get(theme_name, THEMES["dark_professional"])
    prefix = data.get("prefix", "card") if isinstance(data, dict) else "card"
    footer_name = data.get("footer_name", "") if isinstance(data, dict) else ""
    footer_handle = data.get("footer_handle", "") if isinstance(data, dict) else ""
    assets_dir = data.get("assets_dir", "") if isinstance(data, dict) else ""
    profile_image = data.get("profile_image", "") if isinstance(data, dict) else ""
    logo_image = data.get("logo_image", "") if isinstance(data, dict) else ""
    profile_name = data.get("profile_name", "") if isinstance(data, dict) else ""
    profile_title = data.get("profile_title", "") if isinstance(data, dict) else ""

    # 프로필/로고 base64
    profile_b64_map = {}
    if isinstance(profile_image, dict):
        for key, path in profile_image.items():
            resolved = _resolve_image(path, assets_dir)
            if resolved:
                profile_b64_map[key] = _img_to_base64(resolved)

    logo_b64 = ""
    if logo_image:
        resolved = _resolve_image(logo_image, assets_dir)
        if resolved:
            logo_b64 = _img_to_base64(resolved)

    total = len(slides)
    os.makedirs(output_dir, exist_ok=True)

    html_dir = os.path.join(output_dir, "_html")
    os.makedirs(html_dir, exist_ok=True)

    html_files = []
    png_files = []

    for idx, slide in enumerate(slides):
        slide_type = slide.get("type", "point")
        renderer = RENDERERS.get(slide_type, RENDERERS["point"])

        if footer_name and "footer_name" not in slide:
            slide["footer_name"] = footer_name
        if footer_handle and "footer_handle" not in slide:
            slide["footer_handle"] = footer_handle

        # 페이지 메타데이터 주입 (도트 인디케이터용)
        slide["_page_cur"] = idx + 1
        slide["_page_total"] = total

        # 모든 슬라이드에 로고 주입
        if logo_b64 and "_logo_b64" not in slide:
            slide["_logo_b64"] = logo_b64

        if slide_type in ("cover", "cta"):
            if slide_type in profile_b64_map and "_profile_b64" not in slide:
                slide["_profile_b64"] = profile_b64_map[slide_type]
            if profile_name and "profile_name" not in slide:
                slide["profile_name"] = profile_name
            if profile_title and "profile_title" not in slide:
                slide["profile_title"] = profile_title

        page_info = f"{idx + 1} / {total}"
        html_str = renderer(slide, theme, page_info)

        filename_base = f"{prefix}_{idx + 1:02d}_{slide_type}"
        html_path = os.path.join(html_dir, f"{filename_base}.html")
        png_path = os.path.join(output_dir, f"{filename_base}.png")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_str)

        html_files.append(os.path.abspath(html_path))
        png_files.append(os.path.abspath(png_path))
        print(f"  [{idx+1}/{total}] HTML: {filename_base}.html")

    print(f"\nPlaywright screenshot...")


if __name__ == "__main__":
    main()
