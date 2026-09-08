"""B2 Agent Runtime의 범용 Tool 연결 계층.

연구 정책이나 deep-research workflow는 이 파일에 두지 않는다.
이 파일은 모델이 호출할 수 있는 Tool schema와 실제 구현을 연결한다.
"""

from __future__ import annotations

from typing import Any

from src.web_tools import WebTools


WEB_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "공개 웹에서 관련 자료 후보를 검색합니다. "
                "제목, URL, snippet, domain을 반환합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색 질의",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": [
                    "query"
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": (
                "HTTP/HTTPS 웹페이지를 실제로 읽습니다. "
                "focus와 관련된 텍스트를 compact하게 반환합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                    },
                    "focus": {
                        "type": "string",
                        "description": (
                            "페이지에서 확인할 주장, "
                            "기술, 수치 또는 사실"
                        ),
                    },
                    "max_chars": {
                        "type": "integer",
                        "minimum": 1000,
                        "maximum": 12000,
                        "default": 6000,
                    },
                },
                "required": [
                    "url"
                ],
                "additionalProperties": False,
            },
        },
    },
]


class ToolRuntime:
    """Agent가 사용할 범용 Tool 실행기."""

    def __init__(
        self,
        web: WebTools | None = None,
    ):
        self.web = (
            web
            if web is not None
            else WebTools(
                max_search_results=5,
                max_fetch_chars=6000,
            )
        )

        self.handlers = {
            "web_search":
                self.web.web_search,
            "fetch_page":
                self.web.fetch_page,
        }

    @property
    def schemas(
        self,
    ) -> list[dict]:
        return WEB_TOOL_SCHEMAS

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        if name not in self.handlers:
            raise ValueError(
                f"등록되지 않은 Tool: {name}"
            )

        if not isinstance(
            arguments,
            dict,
        ):
            raise ValueError(
                "Tool arguments는 객체여야 합니다."
            )

        handler = self.handlers[name]

        return handler(
            **arguments
        )
