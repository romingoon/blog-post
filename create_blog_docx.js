const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
        VerticalAlign, LevelFormat } = require('docx');
const fs = require('fs');

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "맑은 고딕", size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 48, bold: true, color: "000000", font: "맑은 고딕" },
        paragraph: { spacing: { before: 0, after: 300 }, alignment: AlignmentType.LEFT } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: "2B579A", font: "맑은 고딕" },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: "2B579A", font: "맑은 고딕" },
        paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
      { id: "Normal", name: "Normal",
        run: { size: 22, font: "맑은 고딕" },
        paragraph: { spacing: { after: 160, line: 360 } } }
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children: [
      // 제목
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("2026 대입, 학교폭력 전면 반영! 학부모 필독")] }),

      // 서론
      new Paragraph({ children: [new TextRun("안녕하세요, 오늘도 여러분의 교육법 고민을 함께 나누는 염용주 변호사입니다.")] }),
      new Paragraph({ children: [new TextRun({ text: "\"우리 아이 생기부에 학폭 기록이 있는데, 대학 갈 수 있을까요?\"", italics: true })] }),
      new Paragraph({ children: [new TextRun("요즘 이런 질문을 정말 많이 받습니다. 걱정되고 불안한 마음, 충분히 이해합니다. 특히 2026학년도 대입부터는 학교폭력 조치사항이 "), new TextRun({ text: "모든 대학, 모든 전형에서 의무 반영", bold: true }), new TextRun("됩니다. 2025학년도에는 147개 대학이 자율적으로 반영했지만, 이제는 선택이 아닌 필수가 된 것입니다.")] }),
      new Paragraph({ children: [new TextRun("오늘은 2026학년도 대입에서 학교폭력이 어떻게 반영되는지, 조치별 생기부 기재 기간은 어떻게 되는지, 그리고 학부모님이 알아야 할 핵심 대응 전략까지 상세히 안내해 드리겠습니다.")] }),

      // 본론 1
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("학교폭력 조치, 대입에 어떻게 반영되나요?")] }),
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2026학년도부터 전면 의무화")] }),
      new Paragraph({ children: [new TextRun("2023년 교육부가 발표한 「학교폭력 근절 종합대책」에 따라, 2026학년도 대입부터 학교폭력 조치사항은 모든 대학에서 의무적으로 반영됩니다. 수시 학생부교과, 학생부종합, 논술전형은 물론 정시 수능위주전형까지 예외 없이 적용됩니다.")] }),
      new Paragraph({ children: [new TextRun("반영 방식은 크게 세 가지로 나뉩니다.")] }),

      // 표1: 반영 방식
      new Table({
        columnWidths: [2000, 3500, 3860],
        rows: [
          new TableRow({
            tableHeader: true,
            children: [
              new TableCell({ borders: cellBorders, width: { size: 2000, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "반영 방식", bold: true, color: "FFFFFF" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3500, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "내용", bold: true, color: "FFFFFF" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3860, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "적용 예시", bold: true, color: "FFFFFF" })] })] })
            ]
          }),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 2000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "정량평가", bold: true })] })] }),
            new TableCell({ borders: cellBorders, width: { size: 3500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("조치 단계에 따라 점수 감점")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 3860, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("고려대, 부산대, 동국대 등")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 2000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "정성평가", bold: true })] })] }),
            new TableCell({ borders: cellBorders, width: { size: 3500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("서류평가 시 종합적 판단")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 3860, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("고려대(학생부종합), 강원대 등")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 2000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "지원자격 제한", bold: true })] })] }),
            new TableCell({ borders: cellBorders, width: { size: 3500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("학폭 기록 시 지원 불가 또는 부적격")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 3860, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("연세대 추천형, 이화여대 고교추천, 전국 교대")] })] })
          ]})
        ]
      }),

      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("특히 "), new TextRun({ text: "전국 교대", bold: true }), new TextRun("는 2026학년도부터 학폭 이력의 경중과 관계없이 모든 전형에서 지원자격을 제한하거나 부적격 처리하는 '무관용 원칙'을 예고했습니다.")] }),

      // 본론 2
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("대학별 감점 기준, 얼마나 다를까요?")] }),
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("주요 대학 반영 기준 비교")] }),
      new Paragraph({ children: [new TextRun("대학마다 감점 폭과 적용 방식이 다르므로, 지원 전 반드시 확인해야 합니다.")] }),

      new Paragraph({ children: [new TextRun({ text: "Q. 고려대학교는 어떻게 반영하나요?", bold: true })] }),
      new Paragraph({ children: [new TextRun("학교추천, 학업우수, 계열적합 전형에서는 정성평가를, 논술과 정시에서는 정량평가를 적용합니다. 조치 단계에 따라 최고 20점에서 최저 1점까지 감점되며, 체육교육과 특기자전형은 부적격 처리됩니다.")] }),

      new Paragraph({ children: [new TextRun({ text: "Q. 부산대학교 감점 기준은요?", bold: true })] }),
      new Paragraph({ children: [new TextRun("수시와 정시 감점 폭이 다릅니다. 수시는 1~3호 조치에 30점, 4~5호에 60점, 6~9호에 80점 감점입니다. 정시는 감점 폭이 더 큽니다.")] }),

      new Paragraph({ children: [new TextRun({ text: "Q. 동국대학교는 어떤가요?", bold: true })] }),
      new Paragraph({ children: [new TextRun("수능전형 기준, 1~3호는 감점 없이 통과됩니다. 그러나 4~7호는 100~400점 감점이 적용되며, 8~9호는 불합격 처리됩니다. 다만 소명 기회가 주어지는 경우도 있습니다.")] }),

      new Paragraph({ children: [new TextRun({ text: "Q. 지원 자체가 안 되는 대학도 있나요?", bold: true })] }),
      new Paragraph({ children: [new TextRun("네, 있습니다. 경희대 지역균형, 숙명여대 지역균형, 연세대 추천형, 이화여대 고교추천, 한국외대 학교장추천 전형은 학폭 기록이 있으면 지원 자체가 제한됩니다.")] }),
      new Paragraph({ children: [new TextRun("2025학년도 경북대학교에서는 학폭 기록으로 22명이 불합격 처리되었고, 전체 학폭 이력 수험생 397명 중 298명(75%)이 탈락했습니다.")] }),

      // 본론 3
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("생기부 기록, 언제까지 남아있나요?")] }),
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("조치별 보존 기간 총정리")] }),
      new Paragraph({ children: [new TextRun("학교폭력 조치는 「학교폭력예방 및 대책에 관한 법률」에 따라 1호부터 9호까지 9단계로 구분됩니다. 조치 단계에 따라 생기부 기재 여부와 보존 기간이 달라집니다.")] }),

      // 표2: 조치별 보존 기간
      new Table({
        columnWidths: [900, 2200, 1500, 2200, 2560],
        rows: [
          new TableRow({
            tableHeader: true,
            children: [
              new TableCell({ borders: cellBorders, width: { size: 900, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "조치", bold: true, color: "FFFFFF", size: 20 })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 2200, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "내용", bold: true, color: "FFFFFF", size: 20 })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 1500, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "기재 여부", bold: true, color: "FFFFFF", size: 20 })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 2200, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "보존 기간", bold: true, color: "FFFFFF", size: 20 })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 2560, type: WidthType.DXA }, shading: { fill: "2B579A", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "조기 삭제 가능", bold: true, color: "FFFFFF", size: 20 })] })] })
            ]
          }),
          // 1호~9호 데이터 행
          ...[
            ["1호", "서면 사과", "행동특성", "졸업 시 자동 삭제", "-"],
            ["2호", "접촉·협박·보복행위 금지", "행동특성", "졸업 시 자동 삭제", "-"],
            ["3호", "학교 봉사", "행동특성", "졸업 시 자동 삭제", "-"],
            ["4호", "사회 봉사", "출결특기", "졸업 후 2년", "피해학생 동의 시"],
            ["5호", "특별교육·심리치료", "출결특기", "졸업 후 2년", "피해학생 동의 시"],
            ["6호", "출석 정지", "출결특기", "졸업 후 4년", "피해학생 동의 시"],
            ["7호", "학급 교체", "행동특성", "졸업 후 4년", "피해학생 동의 시"],
            ["8호", "전학", "행동특성", "졸업 후 4년", "불가"],
            ["9호", "퇴학", "행동특성", "영구 보존", "불가"]
          ].map(row => new TableRow({ children: row.map((cell, i) =>
            new TableCell({ borders: cellBorders, width: { size: [900, 2200, 1500, 2200, 2560][i], type: WidthType.DXA },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: cell, size: 20 })] })] })
          )}))
        ]
      }),

      new Paragraph({ spacing: { before: 200 }, children: [new TextRun("중요한 점은 4~7호 조치의 경우 졸업 직전 학교폭력 전담기구 심의를 거쳐 조기 삭제가 가능하지만, "), new TextRun({ text: "반드시 피해학생의 동의", bold: true }), new TextRun("가 필요하다는 것입니다. 피해학생 동의 없이는 삭제가 불가능합니다.")] }),

      // 본론 4
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("학부모가 꼭 알아야 할 대응 전략")] }),
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("조치 단계별 핵심 체크포인트")] }),

      new Paragraph({ children: [new TextRun({ text: "1단계: 조치 통보 전 - 초기 대응이 가장 중요합니다", bold: true })] }),
      new Paragraph({ children: [new TextRun("학폭 사안이 발생하면 학교폭력대책심의위원회(심의위) 개최 전 충분한 준비가 필요합니다. 사실관계 확인, 증거자료 수집, 진술서 작성 등 초기 대응에 따라 조치 결과가 크게 달라질 수 있습니다.")] }),

      new Paragraph({ children: [new TextRun({ text: "2단계: 조치 결정 후 - 불복 절차 검토", bold: true })] }),
      new Paragraph({ children: [new TextRun("조치 결정에 이의가 있다면 90일 이내에 행정심판을 청구할 수 있습니다. 행정심판 결과에도 불복할 경우 행정소송을 제기할 수 있으며, 이 경우 신속재판 의무 규정이 적용되어 1심은 90일 이내에 선고됩니다.")] }),

      new Paragraph({ children: [new TextRun({ text: "3단계: 기록 삭제 준비 - 졸업 전 심의 대비", bold: true })] }),
      new Paragraph({ children: [new TextRun("4~7호 조치를 받은 경우, 졸업 직전 삭제 심의를 준비해야 합니다. 필요 서류는 다음과 같습니다.")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("가해학생 선도 조치 이행 확인서")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("특별교육 및 심리치료 이수 확인서")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("가해학생 의견서")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "피해학생 동의 확인서 (필수)", bold: true })] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("행정심판·행정소송 진행상황")] }),

      new Paragraph({ children: [new TextRun({ text: "4단계: 대입 지원 전 - 대학별 기준 확인", bold: true })] }),
      new Paragraph({ children: [new TextRun("지원하려는 대학의 학폭 반영 방식을 반드시 확인하세요. 감점 방식인지, 지원자격 제한인지에 따라 전략이 완전히 달라집니다. 소명 기회가 주어지는 대학도 있으니 모집요강을 꼼꼼히 살펴보시기 바랍니다.")] }),

      // 결론
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("마치며")] }),
      new Paragraph({ children: [new TextRun("2026학년도 대입부터 학교폭력 조치사항이 모든 대학, 모든 전형에서 의무 반영됩니다. 조치 단계에 따라 감점, 정성평가 불이익, 심지어 지원자격 제한까지 받을 수 있습니다. 그러나 적절한 시기에 올바른 대응을 한다면 불이익을 최소화할 수 있습니다.")] }),
      new Paragraph({ children: [new TextRun("저는 서울시교육청 법무팀에서 5년간 근무하며 수많은 학교폭력 사안을 다루었고, 9년간 교육법 분야에서 학부모님들의 고민을 함께 해결해 왔습니다. 혼자서 막막하고 어려우시다면, 전문가의 조력을 구하시기 바랍니다. 함께 최선의 해결 방안을 찾아드리겠습니다.")] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("2026대입_학교폭력반영_블로그용.docx", buffer);
  console.log("문서 생성 완료: 2026대입_학교폭력반영_블로그용.docx");
});
