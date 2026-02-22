---
name: instagram-card-news
description: |
  블로그 글을 인스타그램 카드뉴스(캐러셀)로 자동 변환하는 스킬. HTML/CSS로 각 슬라이드를 디자인한 뒤 WeasyPrint + pdftoppm으로 1080×1080 PNG 이미지로 추출한다. 블로그 글을 카드뉴스로 만들어달라는 요청, 인스타그램용 콘텐츠 제작, SNS용 인포그래픽 카드 만들기, 카드뉴스 이미지 생성 등의 요청이 들어올 때 이 스킬을 사용한다. "카드뉴스", "인스타그램", "캐러셀", "슬라이드 이미지", "SNS 콘텐츠" 등의 키워드가 포함된 요청에도 반드시 이 스킬을 참조한다.
---

# 인스타그램 카드뉴스 자동 생성 스킬

## 개요

블로그 글(또는 긴 텍스트 콘텐츠)을 인스타그램 캐러셀 형식의 카드뉴스 이미지 세트로 변환한다.
최종 산출물은 **1080×1080px PNG 파일 7~10장**이다.

## 핵심 파이프라인

```
블로그 글 입력
    ↓
콘텐츠 분석 & 슬라이드 분할 (이 스킬의 프롬프트 가이드를 따름)
    ↓
슬라이드별 HTML/CSS 작성 (이 스킬의 디자인 시스템 + 템플릿 활용)
    ↓
scripts/render_cards.py 실행 → PDF → PNG 1080×1080
    ↓
워크스페이스에 이미지 저장
```

---

## 1단계: 환경 준비

카드 렌더링을 시작하기 전에 아래를 확인하고, 없으면 설치한다.

```bash
# 필수 패키지
pip install weasyprint pillow koreanize-matplotlib fonttools --break-system-packages -q

# 한글 폰트 등록 (koreanize-matplotlib에 NanumGothic이 포함되어 있음)
python3 -c "
import os, shutil, subprocess
src = os.path.dirname(__import__('koreanize_matplotlib').__file__) + '/fonts'
dst = os.path.expanduser('~/.fonts')
os.makedirs(dst, exist_ok=True)
for f in os.listdir(src):
    if f.endswith('.ttf'):
        shutil.copy2(os.path.join(src, f), dst)
subprocess.run(['fc-cache', '-f', dst], check=True)
print('Korean fonts ready')
"

# pdftoppm 확인 (poppler-utils, 보통 기본 설치됨)
which pdftoppm || echo "pdftoppm 필요: apt install poppler-utils"
```

---

## 2단계: 블로그 글 → 카드뉴스 콘텐츠 변환

### 인스타그램 vs 블로그 — 톤앤매너 차이

블로그 글을 그대로 옮기면 안 된다. 인스타그램은 완전히 다른 매체이므로 아래 변환 규칙을 적용한다.

| 항목 | 블로그 | 인스타그램 카드뉴스 |
|------|--------|------------------|
| 글자 수 | 2000~5000자 | 슬라이드당 30~80자 (핵심만) |
| 문체 | 설명적, 정보 전달 | 짧고 임팩트 있는 선언형 |
| 구조 | 서론-본론-결론 | 훅 → 핵심 포인트 → CTA |
| 시각 비중 | 텍스트 70% + 이미지 30% | 텍스트 40% + 시각 디자인 60% |
| 호칭 | "~입니다", "~합니다" (격식체) | "~예요", "~해요" 또는 "~하세요" (친근체) |
| 제목 | SEO 키워드 중심 | 감정 자극 + 궁금증 유발 |
| 정보 밀도 | 높음 (법령 조항, 판례 인용) | 낮음 (핵심 숫자 1~2개만) |

### 슬라이드 구조 (7~10장 권장)

| 슬라이드 | 역할 | 콘텐츠 가이드 |
|----------|------|-------------|
| **1. 커버** | 스크롤 멈춤 (Hook) | 강렬한 한 줄 제목 + 부제 + 카테고리 뱃지 |
| **2. 문제 제기** | 공감 유도 | "이런 상황, 겪어보셨나요?" 형태의 상황 묘사 |
| **3~6. 핵심 포인트** | 정보 전달 (1장 1포인트) | 번호 + 핵심 문장 + 보충 1줄 (시각 요소 필수) |
| **7. 요약/정리** | 복습 | 포인트 전체를 체크리스트나 넘버링으로 한눈에 |
| **8. CTA** | 전환 유도 | "저장해두세요", "프로필 링크에서 상담", 계정 정보 |

### 콘텐츠 변환 프롬프트

블로그 글을 카드뉴스로 변환할 때 아래 프롬프트 구조를 따른다:

```
[입력] 블로그 글 전체 텍스트

[변환 지시]
1. 블로그 글에서 핵심 메시지 3~5개를 추출하세요
2. 각 메시지를 30~80자 이내의 카드뉴스 문구로 재작성하세요
3. 인스타그램 톤앤매너를 적용하세요:
   - 격식체 → 친근체 ("~합니다" → "~해요", "~예요")
   - 법률 전문용어 → 쉬운 일상 표현 (괄호 안에 원래 용어 병기 가능)
   - 긴 설명 → 핵심 수치 하나 + 짧은 해석
4. 커버 슬라이드용 훅 문장을 만드세요 (15자 이내 임팩트 제목)
5. CTA 슬라이드 문구를 작성하세요

[출력 형식]
슬라이드 1 (커버): { badge, title, subtitle }
슬라이드 2 (문제제기): { icon/emoji, main_text, sub_text }
슬라이드 3~6 (포인트): { number, heading, body, highlight_keyword }
슬라이드 7 (요약): { items[] }
슬라이드 8 (CTA): { message, contact_info, handle }
```

---

## 3단계: 디자인 시스템

### 컬러 팔레트

6가지 프리셋 테마를 제공한다. 블로그 브랜드나 글의 톤에 맞는 것을 선택한다.

> **추천**: 염용주 변호사 / 법률사무소 이지스 콘텐츠는 `aegis_brand` 테마를 기본으로 사용한다.

```python
THEMES = {
    "aegis_brand": {
        # 법률사무소 이지스 브랜딩 전용 (네이비+골드)
        # 딥 네이비 그라디언트 배경 + Brand Gold 액센트
        # 글래스모피즘, 방패 워터마크, 골드 그라디언트 요소 포함
        "bg_gradient": "linear-gradient(160deg, #0f1923 0%, #1B2B48 45%, #1a3a5c 100%)",
        "accent": "#D4AF37",          # Brand Gold
        "accent_sub": "#C9956B",      # Rose Gold (보조)
        "text_primary": "#FFFFFF",
        "text_secondary": "#A0B4C8",  # Silver Blue (Pantone 877C)
        "text_muted": "#5A7088",
        "badge_bg": "rgba(212,175,55,0.12)",
        "badge_border": "rgba(212,175,55,0.30)",
        "divider": "rgba(255,255,255,0.06)",
        "card_bg": "rgba(255,255,255,0.04)",
        "card_border": "rgba(212,175,55,0.10)",
        "glass_bg": "rgba(255,255,255,0.06)",
        "glass_border": "rgba(255,255,255,0.12)",
    },
    "dark_professional": {
        "bg_gradient": "linear-gradient(160deg, #0c1220 0%, #1a2744 40%, #0f3460 100%)",
        "accent": "#e94560",
        "text_primary": "#ffffff",
        "text_secondary": "#8899aa",
        "text_muted": "#445566",
        "badge_bg": "rgba(233,69,96,0.15)",
        "badge_border": "rgba(233,69,96,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.04)",
    },
    "warm_trust": {
        "bg_gradient": "linear-gradient(160deg, #1a1a2e 0%, #2d1b3d 50%, #461959 100%)",
        "accent": "#ff9f43",
        "text_primary": "#ffffff",
        "text_secondary": "#c4a9d4",
        "text_muted": "#7a6188",
        "badge_bg": "rgba(255,159,67,0.15)",
        "badge_border": "rgba(255,159,67,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.05)",
    },
    "clean_light": {
        "bg_gradient": "linear-gradient(160deg, #f8f9fa 0%, #e9ecef 100%)",
        "accent": "#2563eb",
        "text_primary": "#1a1a2e",
        "text_secondary": "#4a5568",
        "text_muted": "#a0aec0",
        "badge_bg": "rgba(37,99,235,0.1)",
        "badge_border": "rgba(37,99,235,0.2)",
        "divider": "rgba(0,0,0,0.08)",
        "card_bg": "rgba(0,0,0,0.03)",
    },
    "nature_green": {
        "bg_gradient": "linear-gradient(160deg, #0a1f0a 0%, #1a3a2a 40%, #0d4a3a 100%)",
        "accent": "#4ade80",
        "text_primary": "#ffffff",
        "text_secondary": "#88bbaa",
        "text_muted": "#446655",
        "badge_bg": "rgba(74,222,128,0.15)",
        "badge_border": "rgba(74,222,128,0.3)",
        "divider": "rgba(255,255,255,0.08)",
        "card_bg": "rgba(255,255,255,0.04)",
    },
    "coral_soft": {
        "bg_gradient": "linear-gradient(160deg, #fff5f5 0%, #ffe4e6 50%, #fecdd3 100%)",
        "accent": "#e11d48",
        "text_primary": "#1c1917",
        "text_secondary": "#57534e",
        "text_muted": "#a8a29e",
        "badge_bg": "rgba(225,29,72,0.1)",
        "badge_border": "rgba(225,29,72,0.2)",
        "divider": "rgba(0,0,0,0.06)",
        "card_bg": "rgba(0,0,0,0.03)",
    },
}
```

### 이지스 브랜딩 가이드 (`aegis_brand`)

| 용도 | 색상 | 헥스 | 의미 |
|------|------|------|------|
| 배경 | Deep Navy | #0f1923 → #1B2B48 | 신뢰, 전문성 (기존 CTA 배너 계승) |
| 주 액센트 | Brand Gold | #D4AF37 | 권위, 프리미엄 (이지스 브랜드 골드) |
| 보조 액센트 | Rose Gold | #C9956B | 따뜻함, 접근성 |
| 본문 보조 | Silver Blue | #A0B4C8 | Pantone 877C 실버 반영 |
| 카드 보더 | Gold Tint | rgba(212,175,55,0.10) | 은은한 골드 프레임 |

**디자인 요소:**
- 글래스모피즘 카드 (`backdrop-filter: blur(12px)`)
- 방패 워터마크 (커버/CTA 슬라이드)
- 골드 그라디언트 top-line, 디바이더
- 도트 페이지 인디케이터 (우하단)
- 뱃지 골드 글로우 효과
- 프로필 사진 골드 글로우

### 타이포그래피 규칙

```css
/* 기본 폰트 스택 — NanumGothic이 설치되어 있어야 한다 */
font-family: NanumGothic, 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
```

| 요소 | 크기 | 두께 | 자간 |
|------|------|------|------|
| 커버 제목 | 52~60px | ExtraBold | -1px |
| 포인트 제목 | 40~48px | Bold | -0.5px |
| 본문 텍스트 | 24~28px | Regular | 0 |
| 부제/설명 | 20~24px | Regular/Light | 0.5px |
| 뱃지/레이블 | 18~22px | Bold | 1px |
| 푸터/카드번호 | 16~18px | Regular | 0 |

### 레이아웃 원칙

- **안전 영역(Safe Zone)**: 상하좌우 80px 패딩 (인스타그램 프로필 썸네일에서 잘리는 영역 고려)
- **시각적 무게중심**: 콘텐츠를 수직 기준 40~60% 지점에 배치 (상단 여백 > 하단 여백)
- **한 슬라이드 한 메시지**: 포인트 카드에 2개 이상의 주제를 넣지 않는다
- **시각 요소 비중**: 텍스트만으로 채우지 않고, 아이콘/숫자/박스/라인 등으로 시각적 변화를 준다
- **스와이프 유도**: 각 카드 우하단에 "→ 스와이프" 힌트 또는 페이지 인디케이터

---

## 4단계: HTML 슬라이드 타입별 템플릿

`scripts/render_cards.py`에서 아래 템플릿 함수를 활용한다.
각 슬라이드 HTML은 1080×1080px 고정 크기이며, `@page { size: 1080px 1080px; margin: 0; }` 스타일을 반드시 포함해야 한다.

### 템플릿 목록

참고: `scripts/render_cards.py`에 아래 6가지 슬라이드 타입이 모두 구현되어 있다.

1. **cover** — 커버 슬라이드 (훅 제목 + 부제 + 뱃지)
2. **problem** — 문제 제기 (이모지 + 공감 문구)
3. **point** — 핵심 포인트 (큰 숫자 + 제목 + 설명)
4. **comparison** — 비교형 (Before/After 또는 ✕/○ 대비)
5. **summary** — 요약/체크리스트 (번호 목록)
6. **cta** — CTA/마무리 (행동 유도 + 연락처)

각 템플릿의 HTML/CSS 구현은 `scripts/render_cards.py`의 `SLIDE_TEMPLATES` 딕셔너리에서 확인할 수 있다.

---

## 5단계: 렌더링 실행

### 기본 사용법

```python
# render_cards.py를 직접 실행하는 대신, 함수를 import하여 사용
from render_cards import render_card_news

slides = [
    {"type": "cover", "badge": "교육법 핵심정리", "title": "학교폭력 대응,\n골든타임을 놓치지 마세요", "subtitle": "부모가 반드시 알아야 할 5가지"},
    {"type": "problem", "emoji": "😰", "main_text": "아이가 학폭 가해자로\n통보받으셨나요?", "sub_text": "갑작스러운 통보에 대부분의 부모님이\n어떻게 대응해야 할지 모릅니다"},
    {"type": "point", "number": "01", "heading": "72시간 내\n서면 의견서 제출", "body": "학폭 통보를 받으면 72시간이\n골든타임이에요", "highlight": "72시간"},
    # ... 나머지 슬라이드
    {"type": "cta", "message": "전문가의 도움이 필요하시면\n편하게 연락 주세요", "contact": "070-4149-1332", "handle": "@lawyer_yongjours", "name": "염용주 변호사 · 교육법 쌀롱"},
]

# 이미지 생성
render_card_news(
    slides=slides,
    output_dir="/path/to/output",
    theme="dark_professional",   # 테마 선택
    prefix="학폭대응",            # 파일명 접두어
)
# → 학폭대응_01_cover.png, 학폭대응_02_problem.png, ... 생성
```

### 프로필 사진 & 로고 삽입

커버(cover)와 CTA(cta) 슬라이드에 변호사 프로필 사진과 로고를 자동 삽입할 수 있다.
이미지 파일이 있는 디렉토리를 `assets_dir`로 지정하면 된다.

```python
from render_cards import render_card_news

render_card_news(
    slides=slides,
    output_dir="/path/to/output",
    theme="dark_professional",
    prefix="학폭대응",
    # ─── 이미지 관련 파라미터 ───
    profile_image="auto",          # "auto": 기본 매핑 사용 (cover→정면, cta→손모은포즈)
    logo_image="aegis logo.png",   # 로고 파일명 (assets_dir 기준)
    assets_dir="/path/to/이미지폴더",  # 프로필/로고가 있는 디렉토리
    profile_name="염용주 대표변호사",     # 커버 하단 프로필 이름
    profile_title="법률사무소 이지스 · 교육법 전문",  # 커버 하단 직함
)
```

#### 프로필 사진 매핑

`profile_image="auto"`를 사용하면 아래 파일명 매핑에 따라 슬라이드별 다른 사진이 적용된다:

| 슬라이드 | 파일명 | 포즈 설명 |
|---------|--------|---------|
| cover | `profile1_nobg.png` | 정면 정자세 (누끼) |
| cta | `profile4_nobg.png` | 손 모은 자세 (누끼, 신뢰감) |
| side | `profile2_nobg.png` | 측면 포즈 (누끼) |
| smile | `profile3_nobg.png` | 팔짱 + 활짝 웃음 (누끼) |

직접 경로를 지정할 수도 있다:
```python
# 딕셔너리로 슬라이드별 다른 사진 지정
profile_image={"cover": "/path/to/정면.jpg", "cta": "/path/to/웃음.jpg"}

# 단일 경로: cover, cta 모두 같은 사진 사용
profile_image="/path/to/profile.jpg"
```

#### 결과물 예시

커버 슬라이드에는 좌측 하단에 원형 프로필 + 이름/직함이, CTA에는 중앙에 원형 프로필 + 연락처가 배치된다. 로고는 좌측 상단에 표시되며, 어두운 테마에서는 자동으로 흰색 반전 처리된다.

### CLI 사용법

```bash
python3 scripts/render_cards.py \
  --slides slides.json \
  --output-dir ./output \
  --theme dark_professional \
  --prefix "학폭대응" \
  --profile-image auto \
  --logo-image "aegis logo.png" \
  --assets-dir "/path/to/이미지폴더" \
  --profile-name "염용주 대표변호사" \
  --profile-title "법률사무소 이지스 · 교육법 전문"
```

`slides.json` 형식:
```json
{
  "theme": "dark_professional",
  "prefix": "학폭대응",
  "profile_image": "auto",
  "logo_image": "aegis logo.png",
  "assets_dir": "/path/to/이미지폴더",
  "profile_name": "염용주 대표변호사",
  "profile_title": "법률사무소 이지스 · 교육법 전문",
  "slides": [
    {"type": "cover", "badge": "교육법 핵심정리", "title": "학교폭력 대응,\n골든타임을 놓치지 마세요", "subtitle": "부모가 반드시 알아야 할 5가지"},
    ...
  ]
}
```

---

## 6단계: 인스타그램 캡션 & 해시태그

카드뉴스와 함께 사용할 캡션도 함께 생성한다.

### 캡션 구조

```
[첫 줄 — 훅] 임팩트 있는 한 줄 (카드뉴스 제목과 다른 표현)
.
[본문 2~4줄] 이 카드뉴스의 핵심을 요약. 스와이프 유도 포함.
.
[CTA] 저장🔖 & 공유 부탁드려요
도움이 필요하시면 프로필 링크에서 상담 예약 가능합니다.
.
[해시태그 — 최대 15개]
#교육법 #학교폭력 #학폭대응 #변호사상담 #교육법변호사
#학부모필독 #학폭가해자 #학폭피해자 #교원징계
#염용주변호사 #법률상담 #교육법쌀롱
```

### 해시태그 전략

- 대형 태그 (50만+): 3~4개 → 노출 기회
- 중형 태그 (1만~50만): 5~6개 → 주력 경쟁
- 소형/니치 태그 (<1만): 3~4개 → 상위 노출 용이
- 브랜드 태그: 1~2개 → #염용주변호사 #교육법쌀롱

---

## 변호사 광고 규정 주의사항

인스타그램 카드뉴스도 변호사 광고에 해당하므로 아래를 반드시 준수한다:

- ❌ "승소율 OO%" 등 성과 보장 표현 금지
- ❌ "무료 상담", "수임료 할인" 표현 금지 (2025년 개정 규정)
- ❌ "기각 시 100% 환불" 금지
- ✅ "교육법 분야 9년 경력" — 사실 기반 경력 기재 가능
- ✅ "전문 변호사와 상담하세요" — 일반적 상담 유도 가능
- ✅ 법률 정보 제공 목적의 콘텐츠는 광고 규정의 직접 적용 대상이 아니나, 안전하게 운영

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| 한글이 □로 표시 | NanumGothic 미설치 | `pip install koreanize-matplotlib` 후 환경 준비 스크립트 재실행 |
| 이미지 크기가 1080이 아님 | pdftoppm DPI 설정 | `-r 150`이 기본, 정확한 1080px은 Pillow resize로 보정 |
| gradient가 안 나옴 | WeasyPrint CSS 제한 | linear-gradient만 지원, radial-gradient는 사용 불가 |
| 텍스트가 잘림 | 글자 수 초과 | 슬라이드당 80자 이내 엄수, font-size 조정 |
| PDF 생성 실패 | WeasyPrint 버전 | v60+ 권장, `write_png` 대신 `write_pdf` + pdftoppm 사용 |
