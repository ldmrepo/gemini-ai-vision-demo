"""설정 관리 모듈"""

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # API 설정
    google_api_key: str = Field(default="", description="Google AI API Key")

    # 모델 설정 (스펙 기준)
    # - Gemini 3 Flash: gemini-3-flash-preview (Vision 분석, 문항 생성)
    # - Nano Banana Pro: gemini-3-pro-image-preview (이미지 생성)
    gemini_model: str = Field(default="gemini-3-flash-preview", description="Gemini 3 Flash - Vision 분석/문항 생성")
    nano_banana_model: str = Field(default="gemini-3-pro-image-preview", description="Nano Banana Pro - 이미지 생성")

    # 경로 설정
    output_dir: Path = Field(default=Path("./output"), description="출력 디렉토리")
    log_level: str = Field(default="INFO", description="로그 레벨")

    # 생성 설정
    max_vision_actions: int = Field(default=5, description="최대 Vision 탐색 횟수")
    max_regenerations: int = Field(default=3, description="최대 재생성 횟수")

    # 검수 설정
    min_confidence: float = Field(default=0.7, description="최소 신뢰도")

    # Data-Collect 통합 설정
    data_collect_path: str = Field(
        default="/Users/ldm/work/data-collect",
        description="Data-Collect 프로젝트 경로"
    )
    curriculum_version: str = Field(default="2022", description="교육과정 버전")
    exam_years: str = Field(
        default="2020,2021,2022,2023,2024,2025",
        description="수집 대상 시험 년도 (콤마 구분)"
    )

    @property
    def curriculum_dir(self) -> Path:
        """교육과정 PDF 디렉토리"""
        return Path(self.data_collect_path) / "data" / "raw" / "curriculum" / "ncic" / self.curriculum_version

    @property
    def exam_dir(self) -> Path:
        """시험지 PDF 디렉토리"""
        return Path(self.data_collect_path) / "data" / "raw" / "examinations"

    @property
    def textbook_csv(self) -> Path:
        """교과서 메타데이터 CSV"""
        return Path(self.data_collect_path) / "data" / "raw" / "textbook" / "data-2015-meta-textbook-all.csv"

    @property
    def exam_years_list(self) -> list[int]:
        """시험 년도 리스트"""
        return [int(y.strip()) for y in self.exam_years.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "items").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)


# 전역 설정 인스턴스
settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    """캐시된 설정 인스턴스 반환"""
    return Settings()
