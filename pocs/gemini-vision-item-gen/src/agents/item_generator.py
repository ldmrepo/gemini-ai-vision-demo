"""문항 생성 에이전트"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.config import settings
from ..core.schemas import (
    ItemQuestion,
    ItemType,
    DifficultyLevel,
    Choice,
    EvidencePack,
    GenerationLog,
)
from ..utils.json_utils import extract_json_from_text
from .vision_client import GeminiVisionClient


class ItemGeneratorAgent:
    """이미지 기반 문항 생성 에이전트"""

    # 문항 유형별 프롬프트 템플릿
    PROMPTS = {
        ItemType.GRAPH: """이 이미지는 그래프입니다.

**분석 지시:**
1. 그래프의 유형(막대, 선, 원 등)을 파악하세요.
2. 필요하다면 특정 구간을 확대하여 수치를 정확히 확인하세요.
3. 축의 레이블, 범례, 데이터 포인트를 정확히 읽으세요.

**출력 요구사항:**
그래프에서 직접 확인 가능한 정보만을 사용하여 다음 형식으로 객관식 문항 1개를 생성하세요.

반드시 다음 JSON 형식으로만 응답하세요:
```json
{
    "stem": "문항 질문",
    "choices": [
        {"label": "A", "text": "선지1"},
        {"label": "B", "text": "선지2"},
        {"label": "C", "text": "선지3"},
        {"label": "D", "text": "선지4"}
    ],
    "correct_answer": "정답 레이블",
    "explanation": "해설 (시각 근거 포함)",
    "evidence_facts": ["근거1", "근거2"]
}
```

추론 불가능한 정보는 사용하지 마세요.""",

        ItemType.GEOMETRY: """이 이미지는 도형입니다.

**분석 지시:**
1. 도형의 종류와 특성을 파악하세요.
2. 길이, 각도, 위치 관계를 분석하세요.
3. 필요 시 특정 부분을 확대하여 판단하세요.

**출력 요구사항:**
시각적 근거가 명확한 조건만을 사용하여 다음 형식으로 객관식 문항 1개를 생성하세요.

반드시 다음 JSON 형식으로만 응답하세요:
```json
{
    "stem": "문항 질문",
    "choices": [
        {"label": "A", "text": "선지1"},
        {"label": "B", "text": "선지2"},
        {"label": "C", "text": "선지3"},
        {"label": "D", "text": "선지4"}
    ],
    "correct_answer": "정답 레이블",
    "explanation": "해설 (시각 근거 포함)",
    "evidence_facts": ["근거1", "근거2"]
}
```

이미지에서 확인할 수 없는 값은 추정하지 마세요.""",

        ItemType.MEASUREMENT: """이 이미지는 측정 기기 또는 측정값이 포함된 이미지입니다.

**분석 지시:**
1. 측정 기기의 종류를 파악하세요.
2. 눈금과 단위를 정확히 확인하세요.
3. 판독이 어려운 경우 해당 영역을 확대하세요.

**출력 요구사항:**
이미지로 검증 가능한 측정값만을 사용하여 다음 형식으로 객관식 문항 1개를 생성하세요.

반드시 다음 JSON 형식으로만 응답하세요:
```json
{
    "stem": "문항 질문",
    "choices": [
        {"label": "A", "text": "선지1"},
        {"label": "B", "text": "선지2"},
        {"label": "C", "text": "선지3"},
        {"label": "D", "text": "선지4"}
    ],
    "correct_answer": "정답 레이블",
    "explanation": "해설 (시각 근거 포함)",
    "evidence_facts": ["근거1", "근거2"]
}
```

측정값의 정확성이 핵심입니다.""",
    }

    def __init__(self, vision_client: Optional[GeminiVisionClient] = None):
        self.vision_client = vision_client or GeminiVisionClient()
        self.generation_logs: list[GenerationLog] = []

    def generate_item(
        self,
        image_path: str | Path,
        item_type: ItemType,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        custom_prompt: Optional[str] = None
    ) -> tuple[Optional[ItemQuestion], GenerationLog]:
        """
        이미지에서 문항 생성

        Args:
            image_path: 이미지 경로
            item_type: 문항 유형
            difficulty: 난이도
            custom_prompt: 커스텀 프롬프트 (선택)

        Returns:
            (생성된 문항, 생성 로그) 튜플
        """
        session_id = str(uuid.uuid4())[:8]
        image_path = Path(image_path)

        # 생성 로그 초기화
        gen_log = GenerationLog(
            session_id=session_id,
            source_image=str(image_path),
            item_type=item_type,
        )

        try:
            # 프롬프트 선택
            prompt = custom_prompt or self.PROMPTS.get(item_type, self.PROMPTS[ItemType.GRAPH])

            # 난이도 지시 추가
            difficulty_instruction = self._get_difficulty_instruction(difficulty)
            full_prompt = f"{prompt}\n\n{difficulty_instruction}"

            # Agentic Vision으로 이미지 분석 및 문항 생성
            result = self.vision_client.analyze_image_with_agentic_vision(
                image_path=image_path,
                prompt=full_prompt,
                enable_code_execution=True
            )

            # 단계 로그 추가
            gen_log.phases = self.vision_client.get_phase_logs()
            gen_log.total_duration_ms = result.get("total_duration_ms", 0)

            # 응답에서 문항 파싱
            item = self._parse_item_from_response(
                response_text=result.get("text", ""),
                item_type=item_type,
                difficulty=difficulty,
                image_path=str(image_path),
                evidence=self.vision_client.extract_evidence(result)
            )

            if item:
                gen_log.success = True
                gen_log.final_item_id = item.item_id
            else:
                gen_log.success = False

            self.generation_logs.append(gen_log)
            return item, gen_log

        except Exception as e:
            gen_log.success = False
            # 기존 로그가 있으면 사용, 없으면 빈 상태 유지
            phase_logs = self.vision_client.get_phase_logs()
            if phase_logs:
                gen_log.phases = phase_logs
            self.generation_logs.append(gen_log)
            raise RuntimeError(f"문항 생성 실패: {e}") from e

    def _get_difficulty_instruction(self, difficulty: DifficultyLevel) -> str:
        """난이도별 추가 지시문"""
        instructions = {
            DifficultyLevel.EASY: "**난이도: 쉬움** - 이미지에서 직접 읽을 수 있는 단순한 정보를 묻는 문항을 만드세요.",
            DifficultyLevel.MEDIUM: "**난이도: 보통** - 이미지 정보를 바탕으로 한 단계 추론이 필요한 문항을 만드세요.",
            DifficultyLevel.HARD: "**난이도: 어려움** - 이미지의 여러 정보를 종합하여 분석해야 하는 문항을 만드세요.",
        }
        return instructions.get(difficulty, instructions[DifficultyLevel.MEDIUM])

    def _parse_item_from_response(
        self,
        response_text: str,
        item_type: ItemType,
        difficulty: DifficultyLevel,
        image_path: str,
        evidence: EvidencePack
    ) -> Optional[ItemQuestion]:
        """응답 텍스트에서 문항 JSON 파싱"""
        try:
            # JSON 블록 추출
            json_str = self._extract_json_from_text(response_text)
            if not json_str:
                return None

            data = json.loads(json_str)

            # Choice 객체 생성
            choices = [
                Choice(label=c["label"], text=c["text"])
                for c in data.get("choices", [])
            ]

            if len(choices) < 2:
                return None

            # Evidence 업데이트
            evidence_facts = data.get("evidence_facts", [])
            evidence.extracted_facts.extend(evidence_facts)

            # 문항 생성
            item = ItemQuestion(
                item_id=f"ITEM-{uuid.uuid4().hex[:8].upper()}",
                item_type=item_type,
                difficulty=difficulty,
                stem=data.get("stem", ""),
                choices=choices,
                correct_answer=data.get("correct_answer", ""),
                explanation=data.get("explanation", ""),
                evidence=evidence,
                source_image=image_path,
                model_version=settings.gemini_model
            )

            return item

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"문항 파싱 오류: {e}")
            return None

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """텍스트에서 JSON 블록 추출"""
        return extract_json_from_text(text)

    def save_item(self, item: ItemQuestion, output_dir: Optional[Path] = None) -> Path:
        """문항을 JSON 파일로 저장"""
        output_dir = output_dir or settings.output_dir / "items"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{item.item_id}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(item.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)

        return filepath

    def save_log(self, log: GenerationLog, output_dir: Optional[Path] = None) -> Path:
        """생성 로그를 JSON 파일로 저장"""
        output_dir = output_dir or settings.output_dir / "logs"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"log-{log.session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)

        return filepath
