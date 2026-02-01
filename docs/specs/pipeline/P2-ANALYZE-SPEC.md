# P2-ANALYZE 단계 명세

**문서 ID**: P2-ANALYZE-SPEC-001
**버전**: v1.0.0
**목적**: Vision 분석 단계 상세 명세

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **단계** | P2-ANALYZE |
| **에이전트** | AG-VIS (Vision Explorer) |
| **모델** | Gemini 3 Flash |
| **입력** | `InputPack` |
| **출력** | `EvidencePack` |
| **목표 시간** | 3~8초 |

---

## 2. AG-VIS 에이전트

### 2.1 역할

- 문항 이미지 시각적 분석
- 그래프, 도형, 표 등 시각 요소 추출
- 수식 및 텍스트 OCR
- 문항 구조 분석

### 2.2 분석 유형

| 유형 | 분석 대상 | 추출 데이터 |
|------|----------|------------|
| `graph` | 함수 그래프 | 함수식, 점근선, 교점 |
| `geometry` | 도형 | 꼭짓점, 변의 길이, 각도 |
| `diagram` | 다이어그램 | 관계, 흐름, 구조 |
| `table` | 표 | 행/열 데이터, 헤더 |
| `image` | 일반 이미지 | 설명, 레이블 |

---

## 3. 출력: EvidencePack

```python
@dataclass
class EvidencePack:
    source_item_id: str                    # 원본 문항 ID
    extracted_text: str                    # OCR 텍스트
    visual_elements: List[VisualElement]   # 시각 요소 목록
    data_values: Dict[str, Any]            # 추출된 데이터 값
    mathematical_expressions: List[str]    # 수식 목록
    key_concepts: List[str]                # 핵심 개념
    structure_analysis: StructureAnalysis  # 문항 구조 분석
    confidence: float                      # 분석 신뢰도
```

### 3.1 VisualElement

```python
@dataclass
class VisualElement:
    element_id: str
    element_type: str       # graph | geometry | diagram | table | image
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    extracted_data: dict    # 유형별 추출 데이터
    confidence: float
```

### 3.2 StructureAnalysis

```python
@dataclass
class StructureAnalysis:
    item_type: str          # 문항 유형
    stem_analysis: dict     # 발문 분석
    choice_analysis: dict   # 선택지 분석
    answer_derivation: str  # 정답 도출 근거
```

---

## 4. 분석기 컴포넌트

### 4.1 GraphAnalyzer

```python
class GraphAnalyzer:
    def analyze(self, image: Image) -> GraphData:
        """함수 그래프 분석"""
        # - 함수 유형 식별 (일차, 이차, 삼각, 지수, 로그)
        # - 주요 점 추출 (교점, 극값, 점근선)
        # - 함수식 추론
```

### 4.2 GeometryAnalyzer

```python
class GeometryAnalyzer:
    def analyze(self, image: Image) -> GeometryData:
        """도형 분석"""
        # - 도형 유형 식별
        # - 꼭짓점 좌표 추출
        # - 변의 길이, 각도 계산
```

### 4.3 TableAnalyzer

```python
class TableAnalyzer:
    def analyze(self, image: Image) -> TableData:
        """표 분석"""
        # - 행/열 구조 인식
        # - 셀 데이터 추출
        # - 헤더 식별
```

### 4.4 MathExpressionParser

```python
class MathExpressionParser:
    def parse(self, text: str) -> List[MathExpression]:
        """수식 파싱"""
        # - LaTeX 변환
        # - SymPy 표현식 생성
```

---

## 5. 프롬프트 템플릿

```
당신은 교육 평가 문항 분석 전문가입니다.

다음 문항과 이미지를 분석하고 JSON 형식으로 응답하세요:

[분석 항목]
1. 문항 유형 식별 (객관식/주관식, 그래프/도형/표 등)
2. 시각 요소 추출 (좌표, 수치, 레이블)
3. 수식 및 기호 추출 (LaTeX 형식)
4. 핵심 개념 및 성취기준 식별
5. 정답 도출 과정 분석

[문항 내용]
{item_content}

[이미지]
{attached_images}

[응답 형식]
{evidence_pack_schema}
```

---

## 6. 품질 기준

| 지표 | 목표값 |
|------|--------|
| 텍스트 추출 정확도 | > 95% |
| 수식 인식 정확도 | > 90% |
| 그래프 데이터 정확도 | > 85% |
| 도형 인식 정확도 | > 90% |

---

**문서 끝**
