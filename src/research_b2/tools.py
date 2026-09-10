"""B2 Agent Runtime의 범용 Tool 연결 계층.

연구 정책이나 deep-research workflow는 이 파일에 두지 않는다.

이 파일은 모델이 호출할 수 있는 범용 Tool schema와
실제 구현을 연결한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.web_tools import WebTools

from .local_files import LocalFileTools


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
                "additionalProperties":
                    False,
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
                "additionalProperties":
                    False,
            },
        },
    },
]


LOCAL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name":
                "list_local_files",
            "description": (
                "허용된 input 디렉터리 안의 "
                "로컬 파일을 조회합니다. "
                "파일 경로, 크기, 확장자, SHA-256을 반환합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type":
                            "string",
                        "description": (
                            "glob pattern. "
                            "예: *.pdf"
                        ),
                        "default":
                            "*",
                    },
                    "recursive": {
                        "type":
                            "boolean",
                        "default":
                            True,
                    },
                    "max_results": {
                        "type":
                            "integer",
                        "minimum":
                            1,
                        "maximum":
                            500,
                        "default":
                            100,
                    },
                },
                "additionalProperties":
                    False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name":
                "search_pdf_text",
            "description": (
                "허용된 input 디렉터리의 PDF에서 "
                "텍스트를 검색해 관련 page 후보와 "
                "주변 문맥을 반환합니다. "
                "검색 결과는 위치 탐색용이며, "
                "최종 근거로 사용하려면 "
                "read_pdf_pages로 실제 page를 읽어야 합니다."
            ),
            "parameters": {
                "type":
                    "object",
                "properties": {
                    "path": {
                        "type":
                            "string",
                        "description": (
                            "PDF 경로. "
                            "input_dir 기준 상대경로 또는 "
                            "inputs/example.pdf 형식"
                        ),
                    },
                    "query": {
                        "type":
                            "string",
                    },
                    "max_results": {
                        "type":
                            "integer",
                        "minimum":
                            1,
                        "maximum":
                            50,
                        "default":
                            10,
                    },
                    "context_chars": {
                        "type":
                            "integer",
                        "minimum":
                            100,
                        "maximum":
                            3000,
                        "default":
                            500,
                    },
                },
                "required": [
                    "path",
                    "query",
                ],
                "additionalProperties":
                    False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name":
                "read_pdf_pages",
            "description": (
                "허용된 input 디렉터리의 PDF에서 "
                "지정한 실제 page 범위의 텍스트를 읽습니다. "
                "file SHA-256, page 번호와 실제 추출 텍스트를 반환합니다."
            ),
            "parameters": {
                "type":
                    "object",
                "properties": {
                    "path": {
                        "type":
                            "string",
                    },
                    "start_page": {
                        "type":
                            "integer",
                        "minimum":
                            1,
                    },
                    "end_page": {
                        "type":
                            "integer",
                        "minimum":
                            1,
                    },
                    "max_chars": {
                        "type":
                            "integer",
                        "minimum":
                            1000,
                        "maximum":
                            50000,
                        "default":
                            12000,
                    },
                },
                "required": [
                    "path",
                    "start_page",
                ],
                "additionalProperties":
                    False,
            },
        },
    },
]


class ToolRuntime:
    """Agent가 사용할 범용 Tool 실행기."""

    def __init__(
        self,
        web: WebTools | None = None,
        input_dir: Path | None = None,
    ) -> None:
        self.web = (
            web
            if web is not None
            else WebTools(
                max_search_results=5,
                max_fetch_chars=6000,
            )
        )

        self.local = (
            LocalFileTools(
                Path(
                    input_dir
                )
            )
            if input_dir is not None
            else None
        )

        self.handlers = {
            "web_search":
                self.web.web_search,
            "fetch_page":
                self.web.fetch_page,
        }

        if self.local is not None:
            self.handlers.update(
                {
                    "list_local_files":
                        self.local.list_local_files,
                    "search_pdf_text":
                        self.local.search_pdf_text,
                    "read_pdf_pages":
                        self.local.read_pdf_pages,
                }
            )

    @property
    def schemas(
        self,
    ) -> list[dict]:
        schemas = list(
            WEB_TOOL_SCHEMAS
        )

        if self.local is not None:
            schemas.extend(
                LOCAL_TOOL_SCHEMAS
            )

        return schemas

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

        handler = self.handlers[
            name
        ]

        return handler(
            **arguments
        )
