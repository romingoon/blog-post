# 네이버 블로그 스크래핑 가이드

## 네이버 블로그 페이지 구조

네이버 블로그는 iframe 기반 구조로 되어 있다. 본문 콘텐츠는 메인 페이지가 아닌 `iframe#mainFrame` 안에 존재한다.

### SmartEditor 3 (SE3) 구조

| 요소 | 셀렉터 | 설명 |
|------|--------|------|
| iframe | `iframe#mainFrame` | 본문이 담긴 iframe |
| 콘텐츠 컨테이너 | `div.se-main-container` | SE3 본문 전체 영역 |
| 텍스트 컴포넌트 | `div.se-component.se-text` | 텍스트 블록 |
| 이미지 컴포넌트 | `div.se-component.se-image` | 이미지 블록 |
| 인용구 컴포넌트 | `div.se-component.se-quotation` | 인용구 블록 |
| 구분선 컴포넌트 | `div.se-component.se-horizontalLine` | 구분선 |
| 텍스트 내용 | `p.se-text-paragraph > span` | 실제 텍스트 |
| 제목 | `div.se-module-text.se-title-text` 또는 `div.pcol1 .se-fs-` | 글 제목 |

### SmartEditor 2 (SE2) Fallback 구조

구형 에디터를 사용한 글은 iframe 구조가 다르다.

| 요소 | 셀렉터 | 설명 |
|------|--------|------|
| 본문 영역 | `div#postViewArea` | SE2 본문 전체 영역 |
| 텍스트 | `div#postViewArea p, div#postViewArea span` | 텍스트 요소 |

---

## 스크래핑 절차 (4단계)

### A. 브라우저 열기 + URL 이동

```bash
playwright-cli open --browser=chrome
playwright-cli goto {blog_url}
```

- `{blog_url}`을 사용자로부터 받은 네이버 블로그 URL로 대체한다
- 페이지 로드를 위해 충분히 대기한다

### B. iframe 진입 + 본문 추출

`run-code`를 사용하여 iframe에 진입하고 본문을 추출한다.

```bash
playwright-cli run-code "async page => {
  // 1. iframe 진입
  const mainFrame = page.locator('iframe#mainFrame').contentFrame();

  // 2. 본문 로드 대기 (SE3)
  let isSE3 = true;
  try {
    await mainFrame.waitForSelector('div.se-main-container', { timeout: 10000 });
  } catch (e) {
    isSE3 = false;
  }

  // 3. SE2 Fallback
  if (!isSE3) {
    try {
      await mainFrame.waitForSelector('div#postViewArea', { timeout: 5000 });
    } catch (e) {
      return { error: 'CONTENT_NOT_FOUND', message: '본문 컨테이너를 찾을 수 없습니다.' };
    }
  }

  // 4. 제목 추출
  const title = await mainFrame.locator('.se-title-text, .pcol1 .se-fs-, #content-area h3.se_textarea').first().textContent().catch(() => '');

  // 5. SE3 본문 추출
  if (isSE3) {
    const components = await mainFrame.locator('div.se-main-container div.se-component').all();
    const sections = [];
    let order = 1;

    for (const comp of components) {
      const classList = await comp.getAttribute('class');

      if (classList.includes('se-text')) {
        const text = await comp.locator('p.se-text-paragraph').allTextContents();
        const combined = text.join('\n').trim();
        if (combined) {
          // H2/H3 감지
          const hasTitle = await comp.locator('.se-text-paragraph.se-text-paragraph-align- .se-fs32, .se-text-paragraph.se-text-paragraph-align- .se-fs28, .se-text-paragraph.se-text-paragraph-align- .se-fs24').count();
          const type = hasTitle > 0 ? 'heading' : 'text';
          sections.push({ order: order++, type, content: combined, charCount: combined.replace(/\\s/g, '').length });
        }
      } else if (classList.includes('se-image')) {
        const img = await comp.locator('img').first();
        const src = await img.getAttribute('src').catch(() => '');
        const alt = await img.getAttribute('alt').catch(() => '');
        sections.push({ order: order++, type: 'image', src, alt });
      } else if (classList.includes('se-quotation')) {
        const text = await comp.textContent();
        sections.push({ order: order++, type: 'quotation', content: text.trim() });
      } else if (classList.includes('se-horizontalLine')) {
        sections.push({ order: order++, type: 'divider' });
      }
    }

    return { title, editorType: 'SE3', sections };
  }

  // 6. SE2 본문 추출
  const postArea = mainFrame.locator('div#postViewArea');
  const text = await postArea.textContent();
  return { title, editorType: 'SE2', sections: [{ order: 1, type: 'text', content: text.trim() }] };
}"
```

**주요 추출 항목:**
- 글 제목
- 에디터 유형 (SE3 / SE2)
- 섹션별 구조: 순서, 타입(text/heading/image/quotation/divider), 내용, 글자수
- 이미지: src, alt

### C. 레이지 로딩 처리

네이버 블로그 이미지는 레이지 로딩을 사용한다. 모든 이미지를 로드하려면 스크롤이 필요하다.

```bash
playwright-cli run-code "async page => {
  const mainFrame = page.locator('iframe#mainFrame').contentFrame();

  // 스크롤 다운으로 레이지 로딩 트리거
  await mainFrame.evaluate(async () => {
    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
    const container = document.querySelector('div.se-main-container') || document.querySelector('div#postViewArea');
    if (!container) return;

    let lastHeight = 0;
    let currentHeight = container.scrollHeight;

    while (lastHeight !== currentHeight) {
      window.scrollTo(0, currentHeight);
      await delay(500);
      lastHeight = currentHeight;
      currentHeight = container.scrollHeight;
    }
  });

  // 이미지 정보 수집
  const images = await mainFrame.locator('div.se-component.se-image img, div#postViewArea img').all();
  const imageData = [];
  let idx = 1;

  for (const img of images) {
    const src = await img.getAttribute('data-lazy-src') || await img.getAttribute('src') || '';
    const alt = await img.getAttribute('alt') || '';
    imageData.push({ number: idx++, src, alt });
  }

  return imageData;
}"
```

### D. 브라우저 종료 + 결과 정리

```bash
playwright-cli close
```

B, C 단계의 결과를 종합하여 아래 출력 형식으로 정리한다.

---

## 스크래핑 출력 형식

```
## 스크래핑 결과

### 메타 정보
- URL: {url}
- 제목: {title}
- 에디터 유형: {SE3 / SE2}
- 스크래핑 일시: {YYYY-MM-DD HH:mm}

### 글 구조 분석
| 순서 | 타입 | 내용 요약 | 글자 수 |
|------|------|----------|--------|
| 1 | text (서론) | ... | X자 |
| 2 | image | [alt 텍스트] | - |
| 3 | heading (H2) | 소제목 텍스트 | - |
| 4 | text (본론) | ... | X자 |
| ... | ... | ... | ... |

### 본문 전문 (섹션별)
#### 서론
{text}

#### {H2 제목 1}
{text}

#### {H2 제목 2}
{text}

...

### 이미지 위치
| 번호 | 위치 (순서) | alt 텍스트 | src |
|------|-----------|-----------|-----|
| 1 | 2번째 컴포넌트 | ... | ... |
| 2 | 6번째 컴포넌트 | ... | ... |
| ... | ... | ... | ... |

### 구조 통계
- 총 글자수 (공백 제외): X자
- H2 소제목 수: X개
- 이미지 수: X개
- 섹션 수: X개
```

---

## 에러 처리

### iframe 미발견 (구형 에디터 대응)

SE3의 `div.se-main-container`를 찾지 못할 경우, SE2의 `div#postViewArea`로 fallback한다. 두 셀렉터 모두 실패 시 에러를 반환한다.

### 비공개 글

로그인 필요 메시지를 감지한다:

```bash
playwright-cli run-code "async page => {
  const mainFrame = page.locator('iframe#mainFrame').contentFrame();
  const loginMsg = await mainFrame.locator('.login_required, .post_private').count();
  if (loginMsg > 0) {
    return { error: 'PRIVATE_POST', message: '비공개 글입니다. 로그인이 필요합니다.' };
  }
  return { error: null };
}"
```

### 타임아웃

- `waitForSelector` 기본 타임아웃: 10초
- 실패 시 1회 재시도 (페이지 reload 후 재시도)
- 2회 연속 실패 시 에러 반환 및 사용자에게 URL 확인 요청

### 네트워크 오류

- 페이지 로드 실패 시 3초 대기 후 1회 재시도
- 재시도 실패 시 "네트워크 오류가 발생했습니다. URL을 확인하거나 잠시 후 다시 시도해 주세요."라고 안내

---

## 주의사항

1. **자사 블로그 전용**: 이 스크래핑은 자사 블로그(lawyer_yongjours) 업데이트 목적으로만 사용한다
2. **요청 간격**: 과도한 스크래핑을 자제한다 (건당 3초 이상 대기)
3. **캐싱 불필요**: 업데이트 작업은 1회성이므로 스크래핑 결과를 캐싱하지 않는다
4. **데이터 보존**: 스크래핑한 원문을 before 상태로 보존하여 QA 비교에 사용한다
