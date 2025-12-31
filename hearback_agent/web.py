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
        hint = (
            f"<div class='hint'>{html.escape(question.detail)}</div>"
            if question.detail
            else ""
        )
        rows.append(
            """
            <div class="question">
              <div class="question__header">
                <label for="{key}">{prompt}</label>
                <button type="button" class="mic-btn" data-target="{key}">🎤 语音输入</button>
              </div>
              {hint}
              <textarea id="{key}" name="{key}" rows="2" placeholder="请输入答案"></textarea>
            </div>
            """.format(
                key=html.escape(question.key),
                prompt=html.escape(question.prompt),
                hint=hint,
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
            <p class="lead">填写以下问题，提交后会生成访谈纪要和结构化回答。可选语音输入需要浏览器支持 Web Speech API（推荐 Chrome）。</p>
            <form method="POST">
              {questions}
              <div class="actions">
                <button type="submit">生成纪要</button>
              </div>
            </form>
            """.format(questions=render_form(self.questions))

        page_template = """
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              :root {{
                --bg: #0f172a;
                --panel: #111827;
                --muted: #94a3b8;
                --text: #e2e8f0;
                --accent: #38bdf8;
                --card: #1f2937;
              }}
              * {{ box-sizing: border-box; }}
              body {{
                font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
                background: radial-gradient(circle at 20% 20%, rgba(56,189,248,0.08), transparent 25%),
                            radial-gradient(circle at 80% 0%, rgba(94,234,212,0.08), transparent 20%),
                            var(--bg);
                color: var(--text);
                max-width: 960px;
                margin: 0 auto;
                padding: 32px 20px 48px;
              }}
              h1 {{ font-size: 28px; margin-bottom: 12px; letter-spacing: 0.4px; }}
              .lead {{ color: var(--muted); margin-bottom: 18px; }}
              form {{ background: var(--card); border: 1px solid #1f2937; border-radius: 14px; padding: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.35); }}
              .question {{ margin-bottom: 18px; }}
              .question__header {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
              label {{ font-weight: 700; display: block; margin-bottom: 4px; color: #f8fafc; }}
              .hint {{ color: var(--muted); font-size: 0.9em; margin-bottom: 6px; }}
              textarea {{
                width: 100%;
                padding: 10px 12px;
                border-radius: 10px;
                border: 1px solid #1f2937;
                background: #0b1220;
                color: var(--text);
                min-height: 68px;
                resize: vertical;
              }}
              textarea:focus {{ outline: 2px solid var(--accent); border-color: var(--accent); }}
              .actions {{ text-align: right; margin-top: 12px; }}
              button {{
                padding: 10px 16px;
                border: none;
                border-radius: 10px;
                background: linear-gradient(135deg, #38bdf8, #6366f1);
                color: white;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 10px 30px rgba(99,102,241,0.35);
              }}
              button:hover {{ filter: brightness(1.05); }}
              .mic-btn {{
                background: #1f2937;
                border: 1px solid #2f3b52;
                color: var(--text);
                padding: 6px 10px;
                border-radius: 8px;
                font-size: 13px;
                box-shadow: none;
              }}
              .mic-btn.recording {{ border-color: var(--accent); color: var(--accent); }}
              pre {{ background: #0b1220; padding: 12px; white-space: pre-wrap; border-radius: 12px; border: 1px solid #1f2937; }}
            </style>
            <script>
              document.addEventListener("DOMContentLoaded", () => {{
                const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!Recognition) {{
                  document.querySelectorAll(".mic-btn").forEach(btn => {{
                    btn.disabled = true;
                    btn.textContent = "🎤 语音输入不可用";
                    btn.title = "浏览器不支持 Web Speech API";
                  }});
                  return;
                }}
                let activeRecognition = null;
                document.body.addEventListener("click", (e) => {{
                  if (!e.target.matches(".mic-btn")) return;
                  const targetId = e.target.getAttribute("data-target");
                  const textarea = document.getElementById(targetId);
                  if (!textarea) return;

                  if (activeRecognition) {{
                    activeRecognition.stop();
                    activeRecognition = null;
                    document.querySelectorAll(".mic-btn.recording").forEach(btn => btn.classList.remove("recording"));
                    return;
                  }}

                  const recog = new Recognition();
                  recog.lang = "zh-CN";
                  recog.continuous = false;
                  recog.interimResults = false;
                  e.target.classList.add("recording");
                  recog.onresult = (event) => {{
                    const transcript = event.results[0][0].transcript;
                    const sep = textarea.value ? "\\n" : "";
                    textarea.value = textarea.value + sep + transcript;
                  }};
                  recog.onend = () => {{
                    e.target.classList.remove("recording");
                    activeRecognition = null;
                  }};
                  recog.onerror = () => {{
                    e.target.classList.remove("recording");
                    activeRecognition = null;
                  }};
                  activeRecognition = recog;
                  recog.start();
                }});
              });
            </script>
          </head>
          <body>
            {content}
          </body>
        </html>
        """

        page = page_template.replace("{content}", content)

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
