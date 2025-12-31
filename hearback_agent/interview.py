"""Interview agent for collecting detailed error feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


@dataclass(frozen=True)
class InterviewQuestion:
    key: str
    prompt: str
    detail: str | None = None


@dataclass
class InterviewResponse:
    key: str
    question: InterviewQuestion
    answer: str


DEFAULT_QUESTIONS: list[InterviewQuestion] = [
    InterviewQuestion(
        key="error_message",
        prompt="发生了什么错误？(What error did you see?)",
        detail="粘贴报错信息、截图或直观描述。",
    ),
    InterviewQuestion(
        key="expected",
        prompt="你本来期望发生什么？(What did you expect to happen?)",
        detail="描述理想结果或正确行为。",
    ),
    InterviewQuestion(
        key="steps",
        prompt="重现步骤是什么？(How can we reproduce it?)",
        detail="一步一步写出操作流程，包含输入、点击或命令。",
    ),
    InterviewQuestion(
        key="frequency",
        prompt="问题出现频率如何？(How often does it happen?)",
        detail="必现/偶现，最近一次出现时间。",
    ),
    InterviewQuestion(
        key="environment",
        prompt="运行环境是什么？(What environment are you using?)",
        detail="系统、浏览器或客户端版本、网络/权限限制。",
    ),
    InterviewQuestion(
        key="impact",
        prompt="影响有多大？(How is this impacting you?)",
        detail="阻塞程度、影响的用户或业务范围。",
    ),
    InterviewQuestion(
        key="workarounds",
        prompt="有没有临时解决方案？(Any workarounds tried?)",
        detail="暂时可用的替代方案或尝试过的操作。",
    ),
    InterviewQuestion(
        key="artifacts",
        prompt="有没有附件或日志？(Any logs or attachments?)",
        detail="日志片段、请求 ID、截图、视频等。",
    ),
]


def default_questions() -> list[InterviewQuestion]:
    return DEFAULT_QUESTIONS.copy()


class InterviewAgent:
    """Runs a structured interview for error/incident reports."""

    def __init__(self, questions: Sequence[InterviewQuestion] | None = None):
        self.questions = list(questions) if questions is not None else default_questions()

    def conduct(
        self,
        responder: Callable[[InterviewQuestion], str],
    ) -> list[InterviewResponse]:
        responses: list[InterviewResponse] = []
        for question in self.questions:
            answer = responder(question).strip()
            responses.append(
                InterviewResponse(key=question.key, question=question, answer=answer)
            )
        return responses

    def summarize(self, responses: Iterable[InterviewResponse]) -> str:
        lines: list[str] = ["Hearback errors 访谈纪要 (Interview Summary)", ""]
        for response in responses:
            detail = f"（{response.question.detail}）" if response.question.detail else ""
            prompt = f"- {response.question.prompt}{detail}".strip()
            answer = response.answer or "<未提供>"
            lines.append(f"{prompt}\n  回复: {answer}")
        recommendations = self._recommendations(responses)
        if recommendations:
            lines.append("")
            lines.append("后续建议 / Next steps:")
            lines.extend([f"- {item}" for item in recommendations])
        return "\n".join(lines)

    def to_dict(self, responses: Iterable[InterviewResponse]) -> dict[str, str]:
        return {response.key: response.answer for response in responses}

    def _recommendations(self, responses: Iterable[InterviewResponse]) -> list[str]:
        response_map = {response.key: response.answer.strip() for response in responses}
        suggestions: list[str] = []

        if not response_map.get("artifacts"):
            suggestions.append("附上日志、请求 ID 或截图，帮助快速定位。")
        if not response_map.get("steps"):
            suggestions.append("补充最小可复现步骤，便于工程师复现问题。")
        if not response_map.get("environment"):
            suggestions.append("说明操作系统、浏览器或客户端版本，避免环境差异。")
        if response_map.get("impact", "").lower() in {"", "low", "minor"}:
            suggestions.append("如果影响扩大，请更新优先级和受影响范围。")

        return suggestions
