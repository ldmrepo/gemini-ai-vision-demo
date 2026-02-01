"""통합 파이프라인 - 출제-검수 자동화

파이프라인 단계:
- P1-INPUT: 입력 검증
- P2-ANALYZE: 시각 분석 (Gemini 3 Flash)
- P3-GENERATE: 문항 생성 (Gemini 3 Flash)
- P4-VALIDATE: 검증
- P5-OUTPUT: 이미지 생성 (Nano Banana Pro) + 출력
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .core.config import settings
from .core.schemas import (
    ItemType,
    DifficultyLevel,
    ItemQuestion,
    ValidationReport,
    ValidationStatus,
    GenerationLog,
    VisualSpec,
    GeneratedImage,
)
from .agents.item_generator import ItemGeneratorAgent
from .agents.nano_banana_client import NanoBananaClient
from .validators.consistency_validator import ConsistencyValidator
from .validators.quality_checker import QualityChecker
from .utils.logger import AuditLogger
from .utils.image_utils import ImageProcessor


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    success: bool
    item: Optional[ItemQuestion]
    generation_log: Optional[GenerationLog]
    quality_report: Optional[ValidationReport]
    consistency_report: Optional[ValidationReport]
    final_status: str
    error_message: Optional[str] = None


class ItemGenerationPipeline:
    """
    출제-검수 통합 파이프라인

    단계:
    1. 입력 검증 - 이미지 유효성 확인
    2. 시각 분석 - Agentic Vision으로 이미지 탐색
    3. 문항 생성 - 질문/선지/정답/해설 생성
    4. 자동 검수 - 규칙 기반 + AI 기반 검증
    5. 품질 판정 - 통과/재생성/폐기 결정
    """

    def __init__(self, enable_image_generation: bool = True):
        """파이프라인 초기화

        Args:
            enable_image_generation: P5에서 Nano Banana Pro 이미지 생성 활성화
        """
        self.image_processor = ImageProcessor()
        self.item_generator = ItemGeneratorAgent()
        self.quality_checker = QualityChecker()
        self.consistency_validator = ConsistencyValidator()
        self.logger = AuditLogger()

        # P5-OUTPUT: Nano Banana Pro 이미지 생성
        self.enable_image_generation = enable_image_generation
        self.nano_banana_client = NanoBananaClient() if enable_image_generation else None

    def run(
        self,
        image_path: str | Path,
        item_type: ItemType,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        auto_retry: bool = True,
        max_retries: int = 3,
        save_results: bool = True,
        generate_new_image: bool = False
    ) -> PipelineResult:
        """
        파이프라인 실행

        Args:
            image_path: 입력 이미지 경로
            item_type: 문항 유형
            difficulty: 난이도
            auto_retry: 검수 실패 시 자동 재생성
            max_retries: 최대 재시도 횟수
            save_results: 결과 파일 저장 여부
            generate_new_image: P5에서 새 이미지 생성 여부

        Returns:
            PipelineResult
        """
        image_path = Path(image_path)

        # P1-INPUT: 입력 검증
        is_valid, issues = self.image_processor.validate_image(image_path)
        if not is_valid:
            return PipelineResult(
                success=False,
                item=None,
                generation_log=None,
                quality_report=None,
                consistency_report=None,
                final_status="INPUT_INVALID",
                error_message="; ".join(issues)
            )

        # 재시도 루프
        attempts = 0
        last_error = None

        while attempts < max_retries:
            attempts += 1
            self.logger.log_generation_start(
                session_id=f"attempt-{attempts}",
                image_path=str(image_path),
                item_type=item_type.value
            )

            try:
                # P2-ANALYZE & P3-GENERATE: 시각 분석 및 문항 생성 (Gemini 3 Flash)
                item, gen_log = self.item_generator.generate_item(
                    image_path=image_path,
                    item_type=item_type,
                    difficulty=difficulty
                )

                if not item:
                    last_error = "문항 파싱 실패"
                    if not auto_retry:
                        break
                    continue

                self.logger.log_generation_complete(gen_log)

                # P4-VALIDATE: 자동 검수
                quality_report = self.quality_checker.check(item)
                consistency_report = self.consistency_validator.validate(item)

                self.logger.log_validation(quality_report)
                self.logger.log_validation(consistency_report)

                # 품질 판정
                final_status = self._determine_final_status(quality_report, consistency_report)

                if final_status == "PASS":
                    # P5-OUTPUT: 이미지 생성 (Nano Banana Pro)
                    if generate_new_image and self.enable_image_generation:
                        item = self._generate_item_image(item, item_type)

                    # 결과 저장
                    if save_results:
                        self.item_generator.save_item(item)
                        self.item_generator.save_log(gen_log)

                    return PipelineResult(
                        success=True,
                        item=item,
                        generation_log=gen_log,
                        quality_report=quality_report,
                        consistency_report=consistency_report,
                        final_status=final_status
                    )

                elif final_status == "REJECT":
                    # 폐기
                    return PipelineResult(
                        success=False,
                        item=item,
                        generation_log=gen_log,
                        quality_report=quality_report,
                        consistency_report=consistency_report,
                        final_status=final_status,
                        error_message="검수 기준 미달"
                    )

                else:  # RETRY
                    last_error = "검수 미통과, 재생성 필요"
                    if not auto_retry:
                        # 재시도 비활성화 시 REVIEW로 반환
                        if save_results:
                            self.item_generator.save_item(item)
                            self.item_generator.save_log(gen_log)

                        return PipelineResult(
                            success=False,
                            item=item,
                            generation_log=gen_log,
                            quality_report=quality_report,
                            consistency_report=consistency_report,
                            final_status="REVIEW"
                        )

            except Exception as e:
                last_error = str(e)
                self.logger.log_error("pipeline", e)
                if not auto_retry:
                    break

        # 모든 재시도 실패
        return PipelineResult(
            success=False,
            item=None,
            generation_log=None,
            quality_report=None,
            consistency_report=None,
            final_status="MAX_RETRIES_EXCEEDED",
            error_message=last_error
        )


    def _generate_item_image(self, item: ItemQuestion, item_type: ItemType) -> ItemQuestion:
        """P5-OUTPUT: Nano Banana Pro로 이미지 생성

        Args:
            item: 문항 객체
            item_type: 문항 유형

        Returns:
            이미지가 추가된 문항 객체
        """
        if not self.nano_banana_client:
            return item

        try:
            # 시각 사양 생성
            visual_spec = self._create_visual_spec(item, item_type)
            item.visual_spec = visual_spec

            if not visual_spec.required:
                return item

            # 이미지 생성
            self.logger.log_info(f"[P5-OUTPUT] Nano Banana Pro 이미지 생성 시작: {item.item_id}")

            image_bytes = self.nano_banana_client.generate_from_specification(
                visual_spec=visual_spec.model_dump(),
                size="2K"
            )

            # 이미지 저장
            image_id = f"IMG-{uuid.uuid4().hex[:8].upper()}"
            output_path = settings.output_dir / "nano_banana" / f"{image_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            self.nano_banana_client.save_image(image_bytes, output_path)

            # GeneratedImage 객체 생성
            generated_image = GeneratedImage(
                image_id=image_id,
                path=str(output_path),
                format="PNG",
                resolution="2K",
                visual_spec=visual_spec,
                generation_model=settings.nano_banana_model,
            )
            item.generated_image = generated_image

            self.logger.log_info(f"[P5-OUTPUT] 이미지 생성 완료: {output_path}")

        except Exception as e:
            self.logger.log_error("P5-OUTPUT", e)
            # 이미지 생성 실패해도 문항은 유지

        return item

    def _create_visual_spec(self, item: ItemQuestion, item_type: ItemType) -> VisualSpec:
        """문항 유형에 맞는 시각 사양 생성"""
        visual_type_map = {
            ItemType.GRAPH: "bar_chart",
            ItemType.GEOMETRY: "geometry",
            ItemType.MEASUREMENT: "diagram",
        }

        # 기본 시각 사양
        visual_spec = VisualSpec(
            required=True,
            visual_type=visual_type_map.get(item_type, "diagram"),
            description=f"문항 '{item.stem[:50]}...'에 대한 시각 자료",
            data={
                "item_type": item_type.value,
                "stem": item.stem,
                "choices": [c.model_dump() for c in item.choices],
                "correct_answer": item.correct_answer,
            },
            rendering_instructions=f"""
- 교과서/시험지에 적합한 깔끔한 스타일
- 흰색 배경
- 모든 레이블과 텍스트 선명하게
- 한글 및 수학 기호 정확하게 렌더링
- 문항 유형: {item_type.value}
"""
        )

        return visual_spec

    def _determine_final_status(
        self,
        quality_report: ValidationReport,
        consistency_report: ValidationReport
    ) -> str:
        """
        최종 상태 결정

        Returns:
            "PASS" - 통과
            "RETRY" - 재생성 필요
            "REJECT" - 폐기
        """
        # 둘 다 통과
        if (quality_report.status == ValidationStatus.PASS and
            consistency_report.status == ValidationStatus.PASS):
            return "PASS"

        # 하나라도 실패
        if (quality_report.status == ValidationStatus.FAIL or
            consistency_report.status == ValidationStatus.FAIL):
            # 심각한 실패는 폐기
            critical_codes = {"NO_VISUAL_EVIDENCE", "OUT_OF_SCOPE"}
            all_codes = set(f.value for f in quality_report.failure_codes + consistency_report.failure_codes)

            if all_codes & critical_codes:
                return "REJECT"

            return "RETRY"

        # REVIEW 상태는 재시도
        return "RETRY"

    def run_batch(
        self,
        image_dir: str | Path,
        item_type: ItemType,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> list[PipelineResult]:
        """
        디렉토리 내 이미지 일괄 처리
        """
        image_dir = Path(image_dir)
        extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        images = [f for f in image_dir.iterdir() if f.suffix.lower() in extensions]

        results = []
        for image_path in images:
            result = self.run(
                image_path=image_path,
                item_type=item_type,
                difficulty=difficulty
            )
            results.append(result)

        return results

    def get_statistics(self, results: list[PipelineResult]) -> dict:
        """결과 통계"""
        total = len(results)
        success = sum(1 for r in results if r.success)
        fail = total - success

        status_counts = {}
        for r in results:
            status_counts[r.final_status] = status_counts.get(r.final_status, 0) + 1

        return {
            "total": total,
            "success": success,
            "fail": fail,
            "success_rate": success / total * 100 if total > 0 else 0,
            "status_distribution": status_counts
        }
