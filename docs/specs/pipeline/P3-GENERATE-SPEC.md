# P3-GENERATE 단계 명세

**문서 ID**: P3-GENERATE-SPEC-001
**버전**: v1.0.0
**목적**: 문항 생성 단계 상세 명세

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **단계** | P3-GENERATE |
| **에이전트** | AG-GEN (Item Generator) |
| **모델** | Gemini 3 Flash |
| **입력** | `EvidencePack` + 생성 설정 |
| **출력** | `DraftItem` |
| **목표 시간** | 5~15초 |

---

## 2. 생성 전략

### 2.1 변형 유형

| 유형 | 전략 | 예시 |
|------|------|------|
| `SIMILAR` | 구조 유지, 수치/조건 변경 | f(x)=x²+2x → f(x)=x²-3x |
| `NUMERICAL` | 수치만 변경 | 15cm → 20cm |
| `STRUCTURAL` | 문항 구조 변형 | 최댓값 → 최솟값 |
| `DIFFICULTY_UP` | 난이도 상향 | 조건 추가, 복합 계산 |
| `DIFFICULTY_DOWN` | 난이도 하향 | 조건 단순화 |
| `CONCEPT_TRANSFER` | 개념 이전 | 같은 개념, 다른 상황 |
| `INVERSE` | 역문항 생성 | 조건↔결론 교환 |

---

## 3. 출력: DraftItem

```python
@dataclass
class DraftItem:
    item_id: str                        # 생성된 문항 ID
    stem: str                           # 발문
    choices: List[Choice]               # 선택지 (5개)
    correct_answer: str                 # 정답 (①~⑤)
    explanation: str                    # 해설
    solution_steps: List[str]           # 풀이 단계 (수학/과학)
    visual_specification: VisualSpec    # 이미지 생성 사양
    difficulty_estimate: str            # 예상 난이도
    curriculum_alignment: List[str]     # 성취기준
    generation_config: dict             # 생성에 사용된 설정
```

### 3.1 Choice

```python
@dataclass
class Choice:
    label: str           # ①, ②, ③, ④, ⑤
    text: str            # 선택지 내용
    is_correct: bool     # 정답 여부
    distractor_type: str # 오답 유형 (정답이 아닌 경우)
```

### 3.2 오답 유형 (DistractorType)

| 유형 | 설명 | 예시 |
|------|------|------|
| `SIGN_ERROR` | 부호 오류 | +4 대신 -4 |
| `CALCULATION_ERROR` | 계산 실수 | 3×4=11 |
| `CONCEPT_CONFUSION` | 개념 혼동 | 평균↔중앙값 |
| `PARTIAL_SOLUTION` | 부분 풀이 | 중간 단계 값 |
| `SIMILAR_VALUE` | 유사 수치 | 15 대신 14 또는 16 |
| `UNIT_ERROR` | 단위 오류 | m 대신 cm |

### 3.3 VisualSpec

```python
@dataclass
class VisualSpec:
    required: bool          # 이미지 필요 여부
    visual_type: str        # graph | geometry | diagram | none
    description: str        # 시각 요소 설명
    data: dict              # 렌더링 데이터
    rendering_instructions: str  # 렌더링 지침
```

---

## 4. 생성기 컴포넌트

### 4.1 StemGenerator

```python
class StemGenerator:
    def generate(self, evidence: EvidencePack, config: dict) -> str:
        """발문 생성"""
```

### 4.2 ChoiceGenerator

```python
class ChoiceGenerator:
    def generate(self, stem: str, answer: str, count: int = 5) -> List[Choice]:
        """선택지 생성 (정답 + 오답 4개)"""
```

### 4.3 ExplanationGenerator

```python
class ExplanationGenerator:
    def generate(self, item: DraftItem) -> str:
        """해설 생성"""
```

### 4.4 VisualSpecGenerator

```python
class VisualSpecGenerator:
    def generate(self, evidence: EvidencePack, stem: str) -> VisualSpec:
        """시각 사양 생성"""
```

---

## 5. 생성 규칙

### 5.1 수학 문항

- 정답이 유일하게 결정되어야 함
- 계산 결과가 깔끔한 정수 또는 분수여야 함
- 선택지 간 명확한 구분
- 풀이 단계 포함

### 5.2 역사/사회 문항

- **사실 검증 필수** (AG-FACT 연동)
- 연도, 인물, 사건 정확성
- 편향 없는 서술

### 5.3 과학 문항

- 과학적 사실 기반
- 단위 정확성
- 실험/관찰 결과 일관성

---

## 6. 품질 기준

| 지표 | 목표값 |
|------|--------|
| 정답 유일성 | 100% |
| 선택지 구분성 | > 90% |
| 난이도 적합성 | > 80% |
| 교육과정 부합 | > 95% |

---

**문서 끝**
