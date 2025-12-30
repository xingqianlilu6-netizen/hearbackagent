"""Minimal web UI for the hearback errors interview agent."""

from __future__ import annotations

import html
import io
from typing import Iterable
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults

from .interview import InterviewAgent, InterviewQuestion, InterviewResponse, default_questions


def render_form(questions: Iterable[InterviewQuestion]) -> str:
    rows = []
    for question in questions:
        hint = f"<div class='hint'>{html.escape(question.detail)}</div>" if question.detail else ""
        rows.append(
            """
            <div class="question">
              <label for="{key}">{prompt}</label>
              {hint}
              <textarea id="{key}" name="{key}" rows="2" placeholder="请输入答案"></textarea>
            </div>
            """.format(
                key=html.escape(question.key), prompt=html.escape(question.prompt), hint=hint
            )
        )
    return "\n".join(rows)


def render_result(summary: str, payload: dict[str, str]) -> str:
    return f"""
    <h2>访谈纪要</h2>
    <pre>{html.escape(summary)}</pre>
    <h3>结构化回答</h3>
    <pre>{html.escape(str(payload))}</pre>
    <a href="/">返回继续填写</a>
    """


class WebApp:
    def __init__(self, questions: Iterable[InterviewQuestion] | None = None):
        self.questions = list(questions) if questions is not None else default_questions()
        self.agent = InterviewAgent(self.questions)

    def __call__(self, environ, start_response):
        setup_testing_defaults(environ)
        method = environ.get("REQUEST_METHOD", "GET").upper()

        if method == "POST":
            try:
                length = int(environ.get("CONTENT_LENGTH") or 0)
            except ValueError:  # pragma: no cover - defensive
                length = 0
            body = environ["wsgi.input"].read(length).decode("utf-8")
            fields = parse_qs(body)
            responses: list[InterviewResponse] = []
            for question in self.questions:
                answer = fields.get(question.key, [""])[0]
                responses.append(
                    InterviewResponse(key=question.key, question=question, answer=answer.strip())
                )
            summary = self.agent.summarize(responses)
            payload = self.agent.to_dict(responses)
            content = render_result(summary, payload)
        else:
            content = """
            <h1>Hearback errors 访谈</h1>
            <p>填写以下问题，提交后会生成访谈纪要和结构化回答。</p>
            <form method="POST">
              {questions}
              <button type="submit">生成纪要</button>
            </form>
            """.format(questions=render_form(self.questions))

        page = f"""
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              body {{ font-family: sans-serif; max-width: 800px; margin: 40px auto; }}
              .question {{ margin-bottom: 16px; }}
              label {{ font-weight: 600; display: block; margin-bottom: 4px; }}
              .hint {{ color: #555; font-size: 0.9em; margin-bottom: 6px; }}
              textarea {{ width: 100%; padding: 8px; }}
              button {{ padding: 8px 12px; }}
              pre {{ background: #f6f8fa; padding: 12px; white-space: pre-wrap; }}
            </style>
          </head>
          <body>
            {content}
          </body>
        </html>
        """

        encoded = page.encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(encoded)))])
        return [encoded]


def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    with make_server(host, port, WebApp()) as httpd:
        print(f"Serving hearback web UI on http://{host}:{port}")
        httpd.serve_forever()


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin wrapper
    serve()


if __name__ == "__main__":  # pragma: no cover
    main()
