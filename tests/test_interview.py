import unittest

from hearback_agent.interview import (
    InterviewAgent,
    InterviewQuestion,
    InterviewResponse,
    default_questions,
)


class TestInterviewAgent(unittest.TestCase):
    def test_default_questions_have_expected_keys(self):
        keys = [q.key for q in default_questions()]
        self.assertEqual(
            keys,
            [
                "error_message",
                "expected",
                "steps",
                "frequency",
                "environment",
                "impact",
                "workarounds",
                "artifacts",
            ],
        )

    def test_agent_collects_and_summarizes(self):
        questions = default_questions()
        agent = InterviewAgent(questions)

        def responder(question: InterviewQuestion) -> str:
            return {
                "error_message": "报错 500",
                "expected": "接口返回 200",
                "steps": "打开页面 -> 点击保存",
                "frequency": "必现",
                "environment": "macOS + Chrome",
                "impact": "阻塞测试",
                "workarounds": "暂无",
                "artifacts": "请求ID=abc-123",
            }[question.key]

        responses = agent.conduct(responder)
        summary = agent.summarize(responses)

        self.assertIsInstance(summary, str)
        self.assertIn("报错 500", summary)
        self.assertIn("请求ID", summary)

    def test_recommendations_surface_missing_items(self):
        questions = default_questions()[:3]  # limit scope to ensure missing coverage
        agent = InterviewAgent(questions)
        responses = agent.conduct(lambda q: "" if q.key == "steps" else "some")
        summary = agent.summarize(responses)
        self.assertIn("最小可复现步骤", summary)


if __name__ == "__main__":
    unittest.main()
