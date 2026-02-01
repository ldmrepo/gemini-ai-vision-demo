# P5-OUTPUT 단계 명세

**문서 ID**: P5-OUTPUT-SPEC-001
**버전**: v1.0.0
**목적**: 최종 출력 단계 상세 명세

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **단계** | P5-OUTPUT |
| **에이전트** | AG-IMG, AG-STD, AG-AUD |
| **입력** | 검증된 `DraftItem` |
| **출력** | `FinalItem` + 이미지 + 감사 로그 |
| **목표 시간** | 3~10초 |

---

## 2. 출력 에이전트

### 2.1 AG-IMG (Image Generator)

- **모델**: Nano Banana Pro (gemini-3-pro-image-preview)
- 문항 시각 자료 생성
- 그래프, 도형, 다이어그램

### 2.2 AG-STD (Standardizer)

- 용어 표준화
- 단위 표기 통일
- 기호 정규화

### 2.3 AG-AUD (Audit Logger)

- 전체 처리 과정 기록
- 추적 가능성 보장
- 감사 로그 생성

---

## 3. 출력: FinalItem

```python
@dataclass
class FinalItem:
    # 기본 정보
    item_id: str
    source_item_id: str
    version: int

    # 문항 내용
    subject: str
    grade: str
    difficulty: str
    stem: str
    choices: List[Choice]
    correct_answer: str
    explanation: str

    # 메타데이터
    curriculum_standards: List[str]
    keywords: List[str]

    # 첨부
    generated_image: Optional[GeneratedImage]

    # 품질
    validation_score: float
    validation_summary: dict
    human_reviewed: bool

    # 추적
    created_at: datetime
    audit_log_id: str
```

### 3.1 GeneratedImage

```python
@dataclass
class GeneratedImage:
    image_id: str
    path: str
    format: str             # PNG
    resolution: str         # 2K (2048x2048)
    visual_spec: VisualSpec # 생성 사양
    generation_model: str   # gemini-3-pro-image-preview
    generated_at: datetime
```

---

## 4. AG-IMG: Nano Banana Pro

### 4.1 이미지 생성

```python
def generate_item_image(visual_spec: VisualSpec) -> GeneratedImage:
    if not visual_spec.required:
        return None

    prompt = build_image_prompt(visual_spec)

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="2K"
            )
        )
    )

    return extract_and_save_image(response)
```

### 4.2 프롬프트 템플릿

```
교육용 {visual_type}을(를) 생성하세요.

[설명]
{description}

[데이터]
{data}

[요구사항]
- 교과서/시험지에 적합한 깔끔한 스타일
- 흰색 배경
- 모든 레이블과 텍스트 선명하게
- 한글 및 수학 기호 정확하게 렌더링
- 2K 해상도 (2048x2048)
```

### 4.3 지원 시각 유형

| 유형 | 설명 |
|------|------|
| `function_graph` | 함수 그래프 |
| `geometry` | 도형 (삼각형, 사각형, 원 등) |
| `coordinate` | 좌표평면 |
| `bar_chart` | 막대 그래프 |
| `line_chart` | 선 그래프 |
| `pie_chart` | 원 그래프 |
| `diagram` | 다이어그램 |

---

## 5. AG-STD: 표준화 규칙

### 5.1 용어 표준화

| 비표준 | 표준 |
|--------|------|
| 가로, 밑변 | 밑변 |
| 세로, 높이 | 높이 |
| 반지름, 반경 | 반지름 |

### 5.2 단위 표기

| 비표준 | 표준 |
|--------|------|
| cm², ㎠ | cm² |
| m/s, m/sec | m/s |
| kg, KG | kg |

### 5.3 수학 기호

| 비표준 | 표준 |
|--------|------|
| ×, x | × |
| ÷, / | ÷ |
| ≤, <= | ≤ |

---

## 6. AG-AUD: 감사 로그

### 6.1 로그 스키마

```python
@dataclass
class AuditLog:
    log_id: str
    item_id: str
    request_id: str

    # 타임라인
    started_at: datetime
    completed_at: datetime
    duration_ms: int

    # 단계별 기록
    stages: List[StageLog]

    # 결과
    final_status: str
    error_code: Optional[str]
```

### 6.2 StageLog

```python
@dataclass
class StageLog:
    stage: str            # P1, P2, P3, P4, P5
    started_at: datetime
    completed_at: datetime
    status: str           # SUCCESS | FAILED | SKIPPED
    input_hash: str       # 입력 데이터 해시
    output_hash: str      # 출력 데이터 해시
    model_used: str       # 사용된 모델
    token_usage: dict     # 토큰 사용량
```

---

## 7. QTI 변환

### 7.1 출력 형식

```xml
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
                identifier="{item_id}"
                title="{title}">
  <itemBody>
    <p>{stem}</p>
    <img src="{image_url}" alt="{image_alt}"/>
    <choiceInteraction responseIdentifier="RESPONSE" maxChoices="1">
      <simpleChoice identifier="A">{choice_1}</simpleChoice>
      <simpleChoice identifier="B">{choice_2}</simpleChoice>
      <simpleChoice identifier="C">{choice_3}</simpleChoice>
      <simpleChoice identifier="D">{choice_4}</simpleChoice>
      <simpleChoice identifier="E">{choice_5}</simpleChoice>
    </choiceInteraction>
  </itemBody>
  <responseDeclaration identifier="RESPONSE" cardinality="single">
    <correctResponse>
      <value>{correct_answer}</value>
    </correctResponse>
  </responseDeclaration>
</assessmentItem>
```

---

## 8. 저장 구조

```
output/
├── items/
│   └── {item_id}.json       # FinalItem JSON
├── images/
│   └── {image_id}.png       # 생성된 이미지
├── qti/
│   └── {item_id}.xml        # QTI XML
└── logs/
    └── {log_id}.json        # 감사 로그
```

---

**문서 끝**
