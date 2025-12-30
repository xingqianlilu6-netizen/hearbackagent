"""Command-line interface for the hearback errors interview agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .interview import InterviewAgent, InterviewQuestion, InterviewResponse, default_questions


def load_answers(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):  # pragma: no cover - defensive guard
        raise ValueError("Answers file must contain a JSON object mapping keys to answers")
    return {str(key): str(value) for key, value in data.items()}


def prompt_user(question: InterviewQuestion) -> str:
    lines = [question.prompt]
    if question.detail:
        lines.append(f"提示: {question.detail}")
    return input("\n".join(lines) + "\n> ")


def collect_responses(answers: dict[str, str]) -> list[InterviewResponse]:
    agent = InterviewAgent(default_questions())

    def responder(question: InterviewQuestion) -> str:
        if question.key in answers:
            return answers[question.key]
        return prompt_user(question)

    return agent.conduct(responder)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Hearback errors 访谈 agent，收集报错细节并输出摘要。"
    )
    parser.add_argument(
        "--answers",
        help="JSON 文件路径，键为问题 key，值为回答。提供后可非交互生成摘要。",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="输出格式：text 为可读纪要，json 为结构化回答与纪要。",
    )

    args = parser.parse_args(argv)
    answers = load_answers(args.answers)
    responses = collect_responses(answers)

    agent = InterviewAgent(default_questions())
    summary_text = agent.summarize(responses)

    if args.format == "json":
        payload: dict[str, Any] = {
            "responses": agent.to_dict(responses),
            "summary": summary_text,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(summary_text)


if __name__ == "__main__":
    main()
