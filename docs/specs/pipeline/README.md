# 문항 생성 파이프라인 문서 인덱스

AI 기반 문항 생성 시스템 파이프라인 명세 문서 모음

---

## 문서 구성

| 문서 | 설명 |
|------|------|
| [ITEM-GEN-PIPELINE-SPEC.md](ITEM-GEN-PIPELINE-SPEC.md) | 파이프라인 핵심 명세 (개요) |
| [P1-INPUT-SPEC.md](P1-INPUT-SPEC.md) | 입력 처리 단계 상세 |
| [P2-ANALYZE-SPEC.md](P2-ANALYZE-SPEC.md) | 분석 단계 상세 (AG-VIS) |
| [P3-GENERATE-SPEC.md](P3-GENERATE-SPEC.md) | 생성 단계 상세 (AG-GEN) |
| [P4-VALIDATE-SPEC.md](P4-VALIDATE-SPEC.md) | 검증 단계 상세 (AG-VAL, AG-CALC, AG-FACT, AG-SAFE) |
| [P5-OUTPUT-SPEC.md](P5-OUTPUT-SPEC.md) | 출력 단계 상세 (AG-IMG, AG-STD, AG-AUD) |

---

## 파이프라인 개요

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ P1-INPUT │───▶│P2-ANALYZE│───▶│P3-GENERATE│───▶│P4-VALIDATE│───▶│ P5-OUTPUT│
│          │    │          │    │          │    │          │    │          │
│ QTI 파싱 │    │ Vision   │    │ 문항     │    │ 정답     │    │ 이미지   │
│ 이미지   │    │ 분석     │    │ 생성     │    │ 검증     │    │ 생성     │
│ 검증     │    │ 수식추출 │    │ 오답설계 │    │ 계산검증 │    │ 표준화   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
 InputPack      EvidencePack     DraftItem    ValidationReport  FinalItem
```

---

## 에이전트 매트릭스

| 에이전트 | 역할 | 사용 모델 | 적용 단계 |
|---------|------|----------|----------|
| AG-VIS | Vision 분석 | Gemini 3 Flash | P2 |
| AG-GEN | 문항 생성 | Gemini 3 Flash | P3 |
| AG-VAL | 기본 검증 | Gemini 3 Flash | P4 |
| AG-CALC | 계산 검증 | Code Execution | P4 |
| AG-FACT | 사실 검증 | 외부 API | P4 |
| AG-SAFE | 안전 검증 | Gemini 3 Flash | P4 |
| AG-IMG | 이미지 생성 | Nano Banana Pro | P5 |
| AG-STD | 표준화 | 규칙 기반 | P5 |
| AG-AUD | 감사 로깅 | - | P5 |

---

## 과목별 파이프라인

### 수학/과학

```
P1 → P2(AG-VIS) → P3(AG-GEN) → P4(AG-VAL + AG-CALC) → P5
```

### 국어/영어

```
P1 → P2(AG-VIS) → P3(AG-GEN) → P4(AG-VAL + AG-SAFE) → P5
```

### 역사/사회

```
P1 → P2(AG-VIS) → P3(AG-GEN) → P4(AG-VAL + AG-FACT + AG-SAFE) → P5
```

---

## 검증 레벨

| 레벨 | 모델 수 | 사용 모델 | 적용 상황 |
|------|--------|----------|----------|
| Level 1 | 1 | Gemini Flash | 일반 문항 |
| Level 2 | 2 | + GPT-4o | 역사/사회 |
| Level 3 | 3 | + Claude Sonnet | 민감 주제 |
| Level 4 | 3+ | + 전문가 검토 | 공식 시험 |

---

## 오류 코드

| 코드 | 단계 | 의미 | 처리 |
|------|------|------|------|
| E001 | P1 | 입력 파싱 실패 | 요청 반려 |
| E002 | P2 | Vision 분석 실패 | 재시도 (3회) |
| E003 | P3 | 생성 실패 | 재시도 (3회) |
| E004 | P4 | 계산 검증 실패 | 재생성 |
| E005 | P4 | 사실 검증 실패 | 즉시 폐기 |
| E006 | P4 | 편향 감지 | 전문가 검토 |
| E007 | P5 | 이미지 생성 실패 | 텍스트 전용 출력 |
| E008 | ALL | 타임아웃 | 재시도 (3회) |

---

## 구현 로드맵

### Phase 1: Core (2주)
- [ ] P1 입력 파서
- [ ] P2 AG-VIS 구현
- [ ] P3 AG-GEN 구현
- [ ] 기본 출력 포맷터

### Phase 2: Validation (2주)
- [ ] P4 AG-VAL 구현
- [ ] AG-CALC (Code Execution)
- [ ] AG-FACT (외부 API 연동)
- [ ] 교차 검증 엔진

### Phase 3: Output (2주)
- [ ] P5 AG-IMG (Nano Banana Pro)
- [ ] AG-STD (표준화)
- [ ] AG-AUD (감사 로깅)

### Phase 4: Production (2주)
- [ ] API 엔드포인트
- [ ] 배치 처리
- [ ] 모니터링/대시보드

---

**마지막 업데이트**: 2026-02-01
