---
name: naver-blog-updater
description: 이미 발행된 네이버 블로그 글의 정보 최신화, AEO/GEO/스마트블록 최적화, 리텐션 강화를 위한 업데이트 skill. 사용자가 "블로그 업데이트", "블로그 글 수정", "기존 글 최신화", "블로그 리라이팅" 등을 요청할 때 이 skill을 사용한다.
allowed-tools: Bash(playwright-cli:*)
---

# Naver Blog Updater — 스크래핑 → 분석 → 6STEP → QA 파이프라인

## Overview

이 skill은 이미 발행된 네이버 블로그 글을 **정보 최신화, AEO/GEO/스마트블록 최적화, 리텐션 강화** 목적으로 업데이트한다. 기존 URL을 보존하면서 콘텐츠를 보강·재구성하는 것이 핵심이다.

**⚠️ 모델 지정:** 이 skill은 사실 정확성과 법률 검증의 신뢰도를 위해 **가장 최신·최상위 모델(claude-opus-4-6)**로 실행해야 한다.

**산출물 기준:** 업데이트된 본문 마크다운 파일 + before/after QA 비교 보고서 + Google Docs 업로드

**기존 `naver-blog-writer`와의 차이:**
- `naver-blog-writer`: 새 글 작성 (기획→리서치→작성→SEO→QA)
- `naver-blog-updater`: 기존 글 업데이트 (스크래핑→갭분석→6STEP→QA)

## Pipeline

### Step 1: 기존 글 스크래핑

playwright-cli로 네이버 블로그 URL에 접근하여 기존 글의 본문과 구조를 추출한다.

**절차:** `references/scraper-guide.md` 참조

```
입력: 네이버 블로그 URL
출력: 스크래핑 결과 (메타 정보, 글 구조 분석, 본문 전문, 이미지 위치)
```

1. 사용자에게 업데이트할 블로그 URL을 요청한다
2. `scraper-guide.md`의 절차(A→B→C→D)에 따라 스크래핑을 실행한다
3. 스크래핑 결과를 구조화된 형식으로 정리한다

→ 출력을 `scraped_content` 변수에 저장

### Step 2: 갭 분석

스크래핑 결과를 현행 최적화 기준과 대조하여 **9개 영역 점검 보고서**를 생성한다.

**점검 기준:**
- AEO 최적화: `naver-blog-writer/references/seo-guide.md`의 AEO 섹션
- GEO 최적화: `naver-blog-writer/references/seo-guide.md`의 GEO 섹션
- 스마트블록 최적화: `naver-blog-writer/references/seo-guide.md`의 스마트블록 섹션
- 광고규정 준수: `naver-blog-writer/references/qa-guide.md`의 변호사 광고규정 섹션
- 리텐션 장치: D.I.A+ 최적화 기준 (`naver-blog-writer/references/seo-guide.md`)

**9개 영역 점검표:**

| # | 영역 | 점검 내용 | 판정 |
|---|------|----------|------|
| 1 | Direct Answer | 도입부 첫 2~3줄에 핵심 답변이 있는가? | ✅ / ⚠️ |
| 2 | 소제목 구조 | 검색 의도별 H2/H3 구조화가 되어 있는가? | ✅ / ⚠️ |
| 3 | GEO 팩트 블록 | 법령·기한·수치 정리표가 있는가? | ✅ / ⚠️ |
| 4 | Q&A 블록 | 질문형 블록이 본문에 포함되어 있는가? | ✅ / ⚠️ |
| 5 | 리텐션 장치 | 훅/시각요소/내부링크/목차가 적절한가? | ✅ / ⚠️ |
| 6 | 법령 최신화 | 인용된 법률·판례·수치가 최신인가? | ✅ / ⚠️ |
| 7 | CTA 구조 | 3단 CTA가 적절히 배치되어 있는가? | ✅ / ⚠️ |
| 8 | 광고규정 | 금지 표현(승소율/결과보장/공포조장 등)이 없는가? | ✅ / ⚠️ |
| 9 | E-E-A-T | 실무 경험·실무 포인트 박스가 포함되어 있는가? | ✅ / ⚠️ |

```
입력: scraped_content
출력: 9개 영역 갭 분석 보고서 (현황 + 개선 필요 사항)
```

→ 출력을 `gap_report` 변수에 저장

### Step 3: 6STEP 업데이트 실행

`references/update-guide.md`의 STEP 1~6을 순차 적용한다. 각 STEP 적용 결과를 누적하여 최종 업데이트 본문을 완성한다.

```
입력: scraped_content + gap_report
처리: update-guide.md STEP 1→2→3→4→5→6 순차 적용
출력: 업데이트 완료 본문
```

**적용 순서:**
1. **STEP 1:** 도입부 리엔지니어링 (Direct Answer 삽입)
2. **STEP 2:** 본문 구조 재설계 (소제목 재편 + GEO 팩트 블록 + Q&A 블록)
3. **STEP 3:** 리텐션 강화 (훅 + 시각요소 + 내부링크 + 목차)
4. **STEP 4:** 법령·판례 최신화 (최신화 뱃지 + 변경이력 박스)
5. **STEP 5:** CTA 강화 (3단 CTA + 실무포인트 박스)
6. **STEP 6:** 스마트블록/AEO/GEO/리텐션 자가진단 체크

→ 출력을 `updated_content` 변수에 저장

### Step 4: QA 검수

업데이트 전후를 비교하는 **before/after 비교 보고서**를 생성한다.

**검수 기준:**
- 광고규정 준수: `naver-blog-writer/references/qa-guide.md`
- 사실 정확성: 법률 조항, 판례, 통계 검증
- 구조 개선: 갭 분석 보고서의 ⚠️ 항목이 해결되었는지 확인

**before/after 비교 보고서 형식:**

```
## QA 비교 보고서 (Before/After)

### 1. 갭 분석 해소 확인
| # | 영역 | Before | After | 판정 |
|---|------|--------|-------|------|
| 1 | Direct Answer | ⚠️ 없음 | ✅ 3줄 핵심답변 삽입 | 해결 |
| 2 | 소제목 구조 | ⚠️ 단순나열형 | ✅ 의도별 재편 | 해결 |
| ... | ... | ... | ... | ... |

### 2. 광고규정 검수 (변호사 광고에 관한 규정 2025.6.30 개정)
- 금지 표현 발견: 없음 ✅ / [발견된 표현 목록]
- 공포 조장 표현: 없음 ✅ / [발견된 표현 목록]
- 결과 보장 표현: 없음 ✅ / [발견된 표현 목록]
- 수임료 할인 표현: 없음 ✅ / [발견된 표현 목록]

### 3. 사실 정확성 검수
- 법률 인용 정확성: ✅ / ⚠️ [문제점]
- 판례 정확성: ✅ / ⚠️ [문제점]
- 통계 정확성: ✅ / ⚠️ [문제점]

### 4. 구조 변경 요약
| 항목 | Before | After |
|------|--------|-------|
| 총 글자수 | X자 | Y자 |
| H2 소제목 수 | X개 | Y개 |
| 팩트 블록 수 | X개 | Y개 |
| Q&A 블록 수 | X개 | Y개 |
| CTA 수 | X개 | Y개 |
| 내부 링크 수 | X개 | Y개 |

### 5. 종합 판정
- **최종 승인**: ✅ 승인 / ⚠️ 수정 필요
- **수정 필요 사항**: [있을 경우 구체적으로 기재]
```

```
입력: scraped_content (before) + updated_content (after) + gap_report
출력: before/after 비교 보고서
```

**QA 실패 시:**
- 경미한 수정 → 직접 수정 후 재검수
- 중대한 수정 → STEP 3(6STEP)으로 돌아가 해당 STEP만 재실행 (최대 1회)

→ QA 승인된 최종 본문을 `final_content` 변수에 저장

### Step 5: 파일 저장 + Google Docs 업로드

#### 5-1. 마크다운 파일 저장

**파일명 규칙:**
- 기존 파일명에 `_update_YYYYMMDD` 접미사를 붙인다
- 기존 파일이 없는 경우: 주제 키워드 기반으로 파일명을 생성한다

```
기존 파일: 교원징계_소청심사_blog_20260115.md
업데이트:  교원징계_소청심사_blog_20260115_update_20260221.md
```

**저장 경로:** 프로젝트 루트 디렉토리 (`C:\workspace\blog-post\`)

**파일 내용:**
- 업데이트된 본문 전체
- before/after QA 비교 보고서
- 업데이트 이력 (적용된 STEP, 변경 사항 요약)

#### 5-2. Google Docs 업로드

1. **도구 로드**: `ToolSearch({ query: "+google-docs create document" })`
2. **마크다운 → plain text 변환**: `naver-blog-writer/SKILL.md`의 Step 6-2 변환 규칙과 동일
   | 마크다운 문법 | 변환 | 예시 |
   |-------------|------|------|
   | `# `, `## `, `### ` | 제거 (텍스트만 유지) | `## 소제목` → `소제목` |
   | `**텍스트**` | `**` 제거 (텍스트만 유지) | `**중요**` → `중요` |
   | `*텍스트*` | `*` 제거 | `*강조*` → `강조` |
   | `---` (수평선) | 빈 줄로 대체 | |
   | `<!-- 주석 -->` | 그대로 유지 (이미지 배치 참고용) | |
   | `- ` (리스트) | 그대로 유지 | |
   | `1. ` (번호 리스트) | 그대로 유지 | |
   | 테이블 (`\| ... \|`) | 그대로 유지 | |
3. **문서 생성**: `mcp__google-docs__createDocument`로 새 문서 생성
   - title: `[업데이트] {블로그 글 제목}`
   - initialContent: 마크다운 문법을 제거한 plain text 버전
4. **완료 확인**: 생성된 Google Docs 문서 URL을 사용자에게 제공

**Google Docs 업로드 실패 시 fallback:**
- ToolSearch에서 google-docs 도구를 찾을 수 없는 경우 → 마크다운 파일 저장만 수행하고, "Google Docs 연동이 설정되지 않았습니다. 마크다운 파일만 저장되었습니다."라고 안내
- createDocument 호출이 실패한 경우 → 1회 재시도 후에도 실패하면, "Google Docs 업로드에 실패했습니다. 마크다운 파일은 정상 저장되었습니다."라고 안내
- Google Docs 업로드 실패가 전체 파이프라인의 실패를 의미하지는 않는다

## Resources

### 자체 references
- `references/scraper-guide.md` — 네이버 블로그 스크래핑 절차 (iframe 진입, 본문 추출, 에러 처리)
- `references/update-guide.md` — 6STEP 업데이트 가이드 (도입부→구조→리텐션→최신화→CTA→자가진단)

### 교차 참조 (naver-blog-writer)
- `naver-blog-writer/references/writer-guide.md` — 페르소나, 어조, E-E-A-T 기준
- `naver-blog-writer/references/seo-guide.md` — C-RANK/D.I.A+/SEO/AEO/GEO/스마트블록 기준
- `naver-blog-writer/references/qa-guide.md` — 변호사 광고에 관한 규정, 품질 체크리스트
