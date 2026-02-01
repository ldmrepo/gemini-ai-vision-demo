"""데이터 스키마 정의"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """문항 유형"""
    STANDALONE = "standalone"      # 단독 문항
    PASSAGE_GROUP = "passage_group"  # 지문 공유 문항


class BoundingBox(BaseModel):
    """바운딩 박스 좌표"""
    x1: float = Field(..., description="좌측 상단 X")
    y1: float = Field(..., description="좌측 상단 Y")
    x2: float = Field(..., description="우측 하단 X")
    y2: float = Field(..., description="우측 하단 Y")

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def to_tuple(self) -> tuple:
        return (self.x1, self.y1, self.x2, self.y2)


class ExtractedItem(BaseModel):
    """추출된 문항 정보"""
    item_number: str = Field(..., description="문항 번호")
    page_number: int = Field(..., description="페이지 번호")
    bbox: BoundingBox = Field(..., description="바운딩 박스")
    item_type: ItemType = Field(default=ItemType.STANDALONE, description="문항 유형")
    passage_ref: Optional[str] = Field(None, description="공유 지문 참조 (예: p1)")
    confidence: float = Field(default=1.0, description="추출 신뢰도")
    image_path: Optional[str] = Field(None, description="추출된 이미지 경로")


class PageLayout(BaseModel):
    """페이지 레이아웃 정보"""
    page_number: int = Field(..., description="페이지 번호")
    columns: int = Field(default=2, description="단 수")
    width: float = Field(..., description="페이지 너비 (픽셀)")
    height: float = Field(..., description="페이지 높이 (픽셀)")
    item_number_pattern: str = Field(default="", description="문항 번호 패턴")


class PassageInfo(BaseModel):
    """공유 지문 정보

    지문이 단(column)을 넘어가는 경우 bbox_list에 여러 bbox 저장
    """
    passage_id: str = Field(..., description="지문 ID (예: 37-38)")
    page_number: int = Field(..., description="페이지 번호")
    bbox: BoundingBox = Field(..., description="메인 바운딩 박스")
    bbox_list: list[BoundingBox] = Field(default_factory=list, description="다중 bbox (단 넘김 시)")
    item_range: str = Field(..., description="문항 범위 (예: 37~38)")
    image_path: Optional[str] = Field(None, description="추출된 이미지 경로")


class ExtractionResult(BaseModel):
    """추출 결과"""
    source_pdf: str = Field(..., description="원본 PDF 경로")
    total_pages: int = Field(..., description="총 페이지 수")
    processed_pages: int = Field(..., description="처리된 페이지 수")
    items: list[ExtractedItem] = Field(default_factory=list, description="추출된 문항 목록")
    passages: list[PassageInfo] = Field(default_factory=list, description="공유 지문 목록")
    layouts: list[PageLayout] = Field(default_factory=list, description="페이지 레이아웃")
    extracted_at: datetime = Field(default_factory=datetime.now, description="추출 시각")
    model_version: str = Field(default="", description="사용된 모델")


class AgenticStep(BaseModel):
    """Agentic Vision 단계 기록"""
    step_type: str = Field(..., description="단계 유형 (think/act/observe)")
    content: str = Field(..., description="단계 내용")
    timestamp: datetime = Field(default_factory=datetime.now)


class AgenticLog(BaseModel):
    """Agentic Vision 실행 로그"""
    page_number: int = Field(..., description="페이지 번호")
    steps: list[AgenticStep] = Field(default_factory=list, description="실행 단계")
    total_iterations: int = Field(default=0, description="총 반복 횟수")
    success: bool = Field(default=False, description="성공 여부")
