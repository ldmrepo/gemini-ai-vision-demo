"""데이터 스키마 정의"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """문항 유형"""
    GRAPH = "graph"           # 그래프 해석형
    GEOMETRY = "geometry"     # 도형/공간 인식형
    MEASUREMENT = "measurement"  # 측정값 판독형


class DifficultyLevel(str, Enum):
    """난이도"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PhaseType(str, Enum):
    """에이전트 실행 단계"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


class ValidationStatus(str, Enum):
    """검수 상태"""
    PASS = "pass"
    FAIL = "fail"
    REVIEW = "review"


class FailureCode(str, Enum):
    """실패 사유 코드"""
    AMBIGUOUS_READ = "AMBIGUOUS_READ"
    NO_VISUAL_EVIDENCE = "NO_VISUAL_EVIDENCE"
    MULTI_CORRECT = "MULTI_CORRECT"
    OPTION_OVERLAP = "OPTION_OVERLAP"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    INVALID_FORMAT = "INVALID_FORMAT"


class Choice(BaseModel):
    """선지"""
    label: str = Field(..., description="선지 레이블 (A, B, C, D)")
    text: str = Field(..., description="선지 내용")


class Region(BaseModel):
    """이미지 영역"""
    region_id: str = Field(..., description="영역 ID")
    x: int = Field(..., description="X 좌표")
    y: int = Field(..., description="Y 좌표")
    width: int = Field(..., description="너비")
    height: int = Field(..., description="높이")
    transform: Optional[str] = Field(None, description="적용된 변환 (zoom, rotate 등)")
    extracted_text: Optional[str] = Field(None, description="추출된 텍스트")
    extracted_value: Optional[str] = Field(None, description="추출된 수치")
    confidence: float = Field(default=1.0, description="신뢰도")
    purpose: str = Field(default="evidence", description="용도 (정답 근거/오답 근거)")


class EvidencePack(BaseModel):
    """시각 근거 패키지"""
    regions: list[Region] = Field(default_factory=list, description="분석된 영역들")
    extracted_facts: list[str] = Field(default_factory=list, description="추출된 사실들")
    analysis_summary: str = Field(default="", description="분석 요약")


class VisualSpec(BaseModel):
    """시각 자료 생성 사양 (P5-OUTPUT용)"""
    required: bool = Field(default=False, description="이미지 생성 필요 여부")
    visual_type: str = Field(default="", description="시각화 유형 (function_graph, geometry, bar_chart 등)")
    description: str = Field(default="", description="시각 자료 설명")
    data: dict = Field(default_factory=dict, description="시각화 데이터")
    rendering_instructions: str = Field(default="", description="렌더링 지침")


class GeneratedImage(BaseModel):
    """생성된 이미지 정보"""
    image_id: str = Field(..., description="이미지 ID")
    path: str = Field(..., description="저장 경로")
    format: str = Field(default="PNG", description="이미지 포맷")
    resolution: str = Field(default="2K", description="해상도")
    visual_spec: Optional[VisualSpec] = Field(None, description="생성 사양")
    generation_model: str = Field(default="", description="생성에 사용된 모델")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시각")


class ItemQuestion(BaseModel):
    """생성된 문항"""
    item_id: str = Field(..., description="문항 ID")
    item_type: ItemType = Field(..., description="문항 유형")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="난이도")
    stem: str = Field(..., description="문항 질문")
    choices: list[Choice] = Field(..., description="선지 목록")
    correct_answer: str = Field(..., description="정답")
    explanation: str = Field(..., description="해설")
    evidence: EvidencePack = Field(default_factory=EvidencePack, description="시각 근거")
    source_image: str = Field(..., description="원본 이미지 경로")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시각")
    model_version: str = Field(default="", description="사용된 모델 버전")

    # P5-OUTPUT 관련
    visual_spec: Optional[VisualSpec] = Field(default=None, description="시각 자료 생성 사양")
    generated_image: Optional[GeneratedImage] = Field(default=None, description="생성된 이미지")


class ValidationReport(BaseModel):
    """검수 보고서"""
    item_id: str = Field(..., description="문항 ID")
    status: ValidationStatus = Field(..., description="검수 상태")
    failure_codes: list[FailureCode] = Field(default_factory=list, description="실패 사유 코드")
    details: list[str] = Field(default_factory=list, description="상세 내용")
    recommendations: list[str] = Field(default_factory=list, description="개선 권고사항")
    validated_at: datetime = Field(default_factory=datetime.now, description="검수 시각")


class PhaseLog(BaseModel):
    """단계별 로그"""
    phase: PhaseType = Field(..., description="실행 단계")
    input_data: dict = Field(default_factory=dict, description="입력 데이터")
    output_data: dict = Field(default_factory=dict, description="출력 데이터")
    code_executed: Optional[str] = Field(None, description="실행된 코드")
    duration_ms: int = Field(default=0, description="소요 시간(ms)")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")


class GenerationLog(BaseModel):
    """생성 전체 로그"""
    session_id: str = Field(..., description="세션 ID")
    source_image: str = Field(..., description="원본 이미지")
    item_type: ItemType = Field(..., description="문항 유형")
    phases: list[PhaseLog] = Field(default_factory=list, description="단계별 로그")
    total_duration_ms: int = Field(default=0, description="총 소요 시간")
    success: bool = Field(default=False, description="성공 여부")
    final_item_id: Optional[str] = Field(None, description="최종 문항 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시각")
