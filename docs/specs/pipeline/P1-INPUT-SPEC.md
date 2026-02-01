# P1-INPUT 단계 명세

**문서 ID**: P1-INPUT-SPEC-001
**버전**: v1.0.0
**목적**: 입력 수집 및 전처리 단계 상세 명세

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **단계** | P1-INPUT |
| **역할** | QTI 파싱, 이미지 검증, 메타데이터 정규화 |
| **입력** | QTI XML, 첨부 이미지, 메타데이터 |
| **출력** | `InputPack` |
| **목표 시간** | < 1초 |

---

## 2. 입력 사양

### 2.1 QTI XML

```xml
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
                identifier="ITEM-001"
                title="이차함수 문항">
  <itemBody>
    <p>이차함수 f(x) = x² + 2x - 3의 최솟값을 구하시오.</p>
    <choiceInteraction responseIdentifier="RESPONSE" maxChoices="1">
      <simpleChoice identifier="A">-4</simpleChoice>
      <simpleChoice identifier="B">-3</simpleChoice>
      <simpleChoice identifier="C">-2</simpleChoice>
      <simpleChoice identifier="D">-1</simpleChoice>
      <simpleChoice identifier="E">0</simpleChoice>
    </choiceInteraction>
  </itemBody>
  <responseDeclaration identifier="RESPONSE" cardinality="single">
    <correctResponse>
      <value>A</value>
    </correctResponse>
  </responseDeclaration>
</assessmentItem>
```

**지원 버전**: QTI 2.1, QTI 3.0

### 2.2 이미지

| 항목 | 요구사항 |
|------|---------|
| 포맷 | PNG, JPEG, WebP |
| 최대 크기 | 10MB |
| 최대 해상도 | 4096 x 4096 |
| 컬러 모드 | RGB, Grayscale |

### 2.3 메타데이터

```json
{
  "subject": "math",
  "grade": "high-2",
  "difficulty": "medium",
  "curriculum_standards": ["[10수학01-05]"],
  "variation_type": "similar"
}
```

---

## 3. 출력: InputPack

```python
@dataclass
class InputPack:
    request_id: str              # 요청 고유 ID
    qti_item: QTIItem            # 파싱된 QTI 문항
    images: List[Image]          # 첨부 이미지 (0~N개)
    subject: str                 # 과목 코드
    grade: str                   # 학년
    difficulty: str              # 목표 난이도
    variation_type: str          # 변형 유형
    curriculum_meta: dict        # 교육과정 메타데이터
    created_at: datetime         # 생성 시간
```

---

## 4. 처리 컴포넌트

### 4.1 QTIParser

```python
class QTIParser:
    def parse(self, xml_string: str) -> QTIItem:
        """QTI XML을 파싱하여 구조화된 객체로 변환"""

    def validate_schema(self, xml_string: str) -> bool:
        """QTI 스키마 유효성 검증"""
```

### 4.2 ImageProcessor

```python
class ImageProcessor:
    def validate(self, image_data: bytes) -> ValidationResult:
        """이미지 포맷, 크기, 해상도 검증"""

    def normalize(self, image_data: bytes) -> bytes:
        """이미지 정규화 (크기 조정, 포맷 변환)"""
```

### 4.3 MetadataNormalizer

```python
class MetadataNormalizer:
    def normalize(self, metadata: dict) -> dict:
        """메타데이터 정규화 및 기본값 적용"""

    def validate_subject_code(self, subject: str) -> bool:
        """과목 코드 유효성 검증"""
```

---

## 5. 검증 체크리스트

| 코드 | 검증 항목 | 실패 시 처리 |
|------|----------|-------------|
| V001 | QTI 스키마 유효성 | 요청 반려 |
| V002 | 이미지 포맷 | 요청 반려 |
| V003 | 이미지 크기 | 요청 반려 |
| V004 | 필수 메타데이터 | 기본값 적용 |
| V005 | 과목 코드 | 요청 반려 |

---

## 6. 오류 코드

| 코드 | 의미 | HTTP 상태 |
|------|------|----------|
| E001-001 | QTI 파싱 실패 | 400 |
| E001-002 | 지원하지 않는 QTI 버전 | 400 |
| E001-003 | 이미지 포맷 오류 | 400 |
| E001-004 | 이미지 크기 초과 | 400 |
| E001-005 | 필수 필드 누락 | 400 |

---

**문서 끝**
