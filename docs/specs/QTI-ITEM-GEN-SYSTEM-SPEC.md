# QTI 문항 생성 시스템 명세

**문서 ID**: QTI-ITEM-GEN-SYSTEM-SPEC-001
**버전**: v1.1.0
**작성일**: 2026-02-01
**목적**: AI 기반 QTI 문항 생성 시스템 전체 명세

---

## 1. 시스템 개요

### 1.1 목적

기존 QTI 문항을 분석하여 유사/변형 문항을 자동으로 생성하는 AI 시스템

### 1.2 핵심 기능

- **Vision 분석**: 문항 이미지에서 그래프, 도형, 수식 추출
- **문항 생성**: 분석 결과 기반 유사/변형 문항 생성
- **이미지 생성**: Nano Banana Pro를 활용한 문항 이미지 생성
- **품질 검증**: 정답 유일성, 계산 검증, 사실 검증

### 1.3 지원 과목

| 과목군 | 과목 | 특수 검증 |
|--------|------|----------|
| 수학 | 수학, 수학 I/II, 미적분, 확률과 통계, 기하 | AG-CALC |
| 과학 | 물리, 화학, 생명과학, 지구과학 | AG-CALC |
| 사회 | 한국사, 세계사, 사회문화, 경제 | AG-FACT, AG-SAFE |
| 언어 | 국어, 영어 | AG-SAFE |

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ITEM GENERATION SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐                                                        │
│  │   API GW    │◄──── REST API / GraphQL                               │
│  └──────┬──────┘                                                        │
│         │                                                               │
│  ┌──────▼──────────────────────────────────────────────────────────┐   │
│  │                      PIPELINE ORCHESTRATOR                       │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │   │
│  │  │   P1   │─▶│   P2   │─▶│   P3   │─▶│   P4   │─▶│   P5   │   │   │
│  │  │ INPUT  │  │ANALYZE │  │GENERATE│  │VALIDATE│  │ OUTPUT │   │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                        │              │              │              │   │
│                  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│                  │ Gemini 3  │ │ Gemini 3  │ │  Code     │ │   Nano    │
│                  │   Flash   │ │   Flash   │ │ Execution │ │  Banana   │
│                  │  (AG-VIS) │ │  (AG-GEN) │ │ (AG-CALC) │ │  (AG-IMG) │
│                  └───────────┘ └───────────┘ └───────────┘ └───────────┘
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      EXTERNAL SERVICES                           │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │   │
│  │  │  GPT-4o   │  │  Claude   │  │ 국사편찬  │  │  통계청   │    │   │
│  │  │ (검증용) │  │  (검증용) │  │ 위원회API │  │  KOSIS    │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. AI 모델

### 3.1 Primary Models

| 모델 | Model ID | 용도 | 특징 |
|------|----------|------|------|
| Gemini 3 Flash | `gemini-3-flash` | Vision 분석, 문항 생성 | 빠른 응답, 멀티모달 |
| Nano Banana Pro | `gemini-3-pro-image-preview` | 이미지 생성 | 4K 해상도, 텍스트 렌더링 |

### 3.2 Validation Models (Cross-Validation)

| 모델 | 용도 | 적용 레벨 |
|------|------|----------|
| GPT-4o | 교차 검증 | Level 2+ |
| Claude Sonnet | 교차 검증 | Level 3+ |
| Qwen 2.5 | 교차 검증 | Level 3+ |
| DeepSeek | 교차 검증 | Level 3+ |

### 3.3 On-Premise Options

| 모델 | 용도 | 비고 |
|------|------|------|
| Llama 3.1 70B | 교차 검증 | 자체 서버 운영 |
| EXAONE 3.5 | 한국어 특화 검증 | LG AI Research |

---

## 4. 에이전트 구성

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

## 5. 데이터 흐름

```
InputPack → EvidencePack → DraftItem → ValidationReport → FinalItem
```

| 데이터 | 설명 | 생성 단계 |
|--------|------|----------|
| InputPack | QTI 원본 + 이미지 + 메타데이터 | P1 |
| EvidencePack | 시각 분석 결과 + 추출 데이터 | P2 |
| DraftItem | 생성된 문항 초안 | P3 |
| ValidationReport | 검증 결과 | P4 |
| FinalItem | 최종 승인 문항 | P5 |

---

## 6. QTI 지원

### 6.1 지원 버전

- QTI 2.1 (IMS Global)
- QTI 3.0 (1EdTech)

### 6.2 지원 문항 유형

| 유형 | QTI Interaction | 지원 |
|------|-----------------|------|
| 객관식 (5지선다) | choiceInteraction | ✅ |
| 서술형 | extendedTextInteraction | ⚠️ 제한적 |
| 단답형 | textEntryInteraction | ⚠️ 제한적 |

---

## 7. API 인터페이스

### 7.1 문항 생성

```
POST /api/v1/items/generate
POST /api/v1/items/generate/batch
```

### 7.2 검증

```
POST /api/v1/items/validate
GET /api/v1/items/{item_id}/validation
```

### 7.3 조회

```
GET /api/v1/items/{item_id}
GET /api/v1/items?subject=math&grade=high-2
```

---

## 8. 성능 요구사항

| 지표 | 목표값 |
|------|--------|
| 단일 문항 생성 | < 30초 |
| 배치 처리량 | 100문항/시간 |
| API 응답 시간 | < 100ms (조회) |
| 검증 통과율 | > 75% |
| 시스템 가용성 | > 99.5% |

---

## 9. 보안

### 9.1 데이터 보안

- API Key 암호화 저장
- 전송 구간 TLS 1.3
- 문항 데이터 암호화

### 9.2 접근 제어

- API Key 기반 인증
- Rate Limiting
- IP Whitelist (옵션)

---

## 10. 참조 문서

| 문서 | 설명 |
|------|------|
| [파이프라인 명세](pipeline/README.md) | P1-P5 파이프라인 상세 |
| [Nano Banana Pro 연구](../research/NANO-BANANA-PRO-RESEARCH.md) | 이미지 생성 모델 분석 |

---

## 개정 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0.0 | 2026-02-01 | 초기 작성 |
| v1.1.0 | 2026-02-01 | Multi-Model Validation Strategy 추가 |

---

**문서 끝**
