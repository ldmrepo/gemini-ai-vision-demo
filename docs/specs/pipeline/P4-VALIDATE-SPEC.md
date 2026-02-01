# P4-VALIDATE 단계 명세

**문서 ID**: P4-VALIDATE-SPEC-001
**버전**: v1.0.0
**목적**: 문항 검증 단계 상세 명세

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **단계** | P4-VALIDATE |
| **에이전트** | AG-VAL, AG-CALC, AG-FACT, AG-SAFE |
| **입력** | `DraftItem` + `EvidencePack` |
| **출력** | `ValidationReport` |
| **목표 시간** | 5~20초 (과목별 상이) |

---

## 2. 검증 에이전트

### 2.1 AG-VAL (Core Validator)

- 기본 검증 수행
- 정답 유일성, 선택지 구분성
- 난이도/교육과정 부합성

### 2.2 AG-CALC (Calculation Verifier)

- 수학/과학 계산 검증
- **Code Execution** 활용
- Python + SymPy 기반

### 2.3 AG-FACT (Fact Checker)

- 역사/사회 사실 검증
- 외부 API 연동
  - 국사편찬위원회 API
  - 통계청 KOSIS API
  - Wikipedia API

### 2.4 AG-SAFE (Safety Checker)

- 편향 검사 (성별, 인종, 지역 등)
- 유해 콘텐츠 탐지
- 민감 주제 검토

---

## 3. 출력: ValidationReport

```python
@dataclass
class ValidationReport:
    item_id: str
    overall_status: str        # PASS | FAIL | HOLD
    checks: List[CheckResult]  # 개별 검증 결과
    score: float               # 0.0 ~ 1.0
    issues: List[Issue]        # 발견된 이슈
    recommendations: List[str] # 개선 권고
    cross_validation: dict     # 교차 검증 결과
```

### 3.1 CheckResult

```python
@dataclass
class CheckResult:
    check_code: str      # 검증 코드
    status: str          # PASS | FAIL | WARN
    message: str         # 결과 메시지
    evidence: str        # 검증 근거
    weight: float        # 가중치
```

---

## 4. 검증 체크리스트

| 코드 | 검증 항목 | 가중치 | 적용 과목 |
|------|----------|--------|----------|
| `ANS_UNIQUE` | 정답 유일성 | 1.0 | 전체 |
| `ANS_CORRECT` | 정답 정확성 | 1.0 | 전체 |
| `CALC_VERIFY` | 계산 검증 | 1.0 | 수학, 물리, 화학 |
| `FACT_VERIFY` | 사실 검증 | 1.0 | 역사, 사회 |
| `OPT_DISTINCT` | 선택지 구분성 | 0.8 | 전체 |
| `OPT_PLAUSIBLE` | 오답 타당성 | 0.7 | 전체 |
| `DIFF_MATCH` | 난이도 부합 | 0.6 | 전체 |
| `CURR_ALIGN` | 교육과정 부합 | 0.8 | 전체 |
| `BIAS_FREE` | 편향 없음 | 1.0 | 전체 |
| `SAFE_CONTENT` | 안전한 콘텐츠 | 1.0 | 전체 |

---

## 5. 과목별 검증 파이프라인

### 5.1 수학/물리/화학

```
DraftItem ──▶ AG-VAL ──▶ AG-CALC ──▶ ValidationReport
                              │
                              ▼
                    [Code Execution]
                    Python + SymPy
```

### 5.2 국어/영어

```
DraftItem ──▶ AG-VAL ──▶ AG-SAFE ──▶ ValidationReport
```

### 5.3 역사/사회

```
DraftItem ──▶ AG-VAL ──▶ AG-FACT ──▶ AG-SAFE ──▶ ValidationReport
                              │
                              ▼
                    [외부 API 조회]
```

---

## 6. AG-CALC: Code Execution

### 6.1 샌드박스 환경

```python
class SandboxExecutor:
    def execute(self, code: str, timeout: int = 10) -> ExecutionResult:
        """격리된 환경에서 Python 코드 실행"""

    ALLOWED_IMPORTS = [
        "sympy", "numpy", "math", "fractions", "decimal"
    ]
```

### 6.2 검증 예시

```python
def verify_math_answer(draft_item: DraftItem) -> CheckResult:
    code = f"""
import sympy as sp
x = sp.Symbol('x')
f = {parsed_expression}
result = sp.solve(f, x)
print(result)
"""
    result = sandbox.execute(code)
    return compare_with_answer(result, draft_item.correct_answer)
```

---

## 7. 교차 검증 엔진

### 7.1 검증 레벨

| 레벨 | 모델 수 | 사용 모델 | 합의 기준 |
|------|--------|----------|----------|
| Level 1 | 1 | Gemini Flash | 단일 검증 |
| Level 2 | 2 | + GPT-4o | 2/2 합의 |
| Level 3 | 3 | + Claude Sonnet | 2/3 합의 |
| Level 4 | 3+ | + 전문가 | 전문가 최종 결정 |

### 7.2 불일치 처리

```
모델 A: PASS
모델 B: FAIL
모델 C: PASS
→ 2/3 합의 → PASS (단, 이슈 기록)
```

---

## 8. 실패 처리

| 검증 실패 | 처리 방법 |
|----------|----------|
| ANS_UNIQUE | P3 재생성 (최대 3회) |
| ANS_CORRECT | P3 재생성 (최대 3회) |
| CALC_VERIFY | P3 재생성 (최대 3회) |
| FACT_VERIFY | **즉시 폐기** |
| BIAS_FREE | 전문가 검토 대기 (HOLD) |
| SAFE_CONTENT | **즉시 폐기** |

---

**문서 끝**
