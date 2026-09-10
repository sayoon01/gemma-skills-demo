"""Generic local-file / PDF tools for B2 runtime.

Research policy and domain logic do not belong here.

This module only provides scoped filesystem capabilities:

- list files inside an allowed input directory;
- search text inside text-based PDFs;
- read explicit PDF pages.

Access outside the configured input directory is rejected.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import fitz


ZERO_WIDTH_RE = re.compile(
    r"[\u200b\u200c\u200d\ufeff]"
)

SPACE_RE = re.compile(
    r"\s+"
)


def file_sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def normalize_search_text(
    value: str,
) -> str:
    value = ZERO_WIDTH_RE.sub(
        "",
        value or "",
    )

    value = SPACE_RE.sub(
        " ",
        value,
    )

    return value.strip()


class LocalFileTools:
    """Tools scoped to one explicitly allowed input directory."""

    def __init__(
        self,
        input_dir: Path,
    ) -> None:
        root = Path(
            input_dir
        ).expanduser().resolve()

        if not root.is_dir():
            raise ValueError(
                "input_dir가 존재하는 "
                f"디렉터리가 아닙니다: {root}"
            )

        self.input_dir = root

    def _resolve_file(
        self,
        path: str,
    ) -> Path:
        value = (
            path
            or ""
        ).strip()

        if not value:
            raise ValueError(
                "path가 비어 있습니다."
            )

        raw = Path(
            value
        ).expanduser()

        candidates = []

        if raw.is_absolute():
            candidates.append(
                raw
            )

        else:
            #
            # "robot.pdf" 형식
            #
            candidates.append(
                self.input_dir
                / raw
            )

            #
            # "inputs/robot.pdf" 형식도 허용.
            # 최종 scope 검사를 통과해야만 사용 가능.
            #
            candidates.append(
                Path.cwd()
                / raw
            )

        resolved = None

        for candidate in candidates:
            candidate = (
                candidate.resolve()
            )

            try:
                candidate.relative_to(
                    self.input_dir
                )

            except ValueError:
                continue

            if candidate.is_file():
                resolved = candidate
                break

        if resolved is None:
            raise FileNotFoundError(
                "허용된 input_dir 안에서 "
                f"파일을 찾지 못했습니다: {value}"
            )

        return resolved

    def _display_path(
        self,
        path: Path,
    ) -> str:
        try:
            return str(
                path.relative_to(
                    Path.cwd().resolve()
                )
            )

        except ValueError:
            return str(
                path.relative_to(
                    self.input_dir
                )
            )

    def _require_pdf(
        self,
        path: str,
    ) -> Path:
        resolved = (
            self._resolve_file(
                path
            )
        )

        if (
            resolved.suffix.lower()
            != ".pdf"
        ):
            raise ValueError(
                "현재 document reader는 "
                "PDF만 지원합니다: "
                f"{resolved.name}"
            )

        return resolved

    def list_local_files(
        self,
        pattern: str = "*",
        recursive: bool = True,
        max_results: int = 100,
    ) -> dict[str, Any]:
        if not 1 <= max_results <= 500:
            raise ValueError(
                "max_results는 1~500이어야 합니다."
            )

        if not pattern.strip():
            pattern = "*"

        iterator = (
            self.input_dir.rglob(
                pattern
            )
            if recursive
            else self.input_dir.glob(
                pattern
            )
        )

        paths = sorted(
            (
                path.resolve()
                for path in iterator
                if path.is_file()
            ),
            key=lambda item:
                str(item),
        )

        paths = paths[
            :max_results
        ]

        files = []

        for path in paths:
            files.append(
                {
                    "path":
                        self._display_path(
                            path
                        ),
                    "name":
                        path.name,
                    "suffix":
                        path.suffix.lower(),
                    "size_bytes":
                        path.stat().st_size,
                    "sha256":
                        file_sha256(
                            path
                        ),
                }
            )

        return {
            "input_dir":
                str(
                    self.input_dir
                ),
            "file_count":
                len(files),
            "files":
                files,
        }

    def search_pdf_text(
        self,
        path: str,
        query: str,
        max_results: int = 10,
        context_chars: int = 500,
    ) -> dict[str, Any]:
        pdf_path = (
            self._require_pdf(
                path
            )
        )

        query = (
            query
            or ""
        ).strip()

        if not query:
            raise ValueError(
                "query가 비어 있습니다."
            )

        if not 1 <= max_results <= 50:
            raise ValueError(
                "max_results는 1~50이어야 합니다."
            )

        if not 100 <= context_chars <= 3000:
            raise ValueError(
                "context_chars는 "
                "100~3000이어야 합니다."
            )

        normalized_query = (
            normalize_search_text(
                query
            ).casefold()
        )

        query_tokens = [
            token
            for token in (
                normalized_query.split()
            )
            if token
        ]

        results = []

        with fitz.open(
            pdf_path
        ) as document:
            for page_index in range(
                document.page_count
            ):
                raw_text = (
                    document.load_page(
                        page_index
                    ).get_text(
                        "text"
                    )
                    or ""
                )

                text = (
                    normalize_search_text(
                        raw_text
                    )
                )

                searchable = (
                    text.casefold()
                )

                full_match_count = (
                    searchable.count(
                        normalized_query
                    )
                )

                token_match_count = sum(
                    searchable.count(
                        token
                    )
                    for token
                    in query_tokens
                )

                score = (
                    full_match_count * 10
                    + token_match_count
                )

                if score <= 0:
                    continue

                position = (
                    searchable.find(
                        normalized_query
                    )
                )

                if position < 0:
                    positions = [
                        searchable.find(
                            token
                        )
                        for token
                        in query_tokens
                        if (
                            searchable.find(
                                token
                            )
                            >= 0
                        )
                    ]

                    position = (
                        min(
                            positions
                        )
                        if positions
                        else 0
                    )

                half = (
                    context_chars
                    // 2
                )

                start = max(
                    0,
                    position - half,
                )

                end = min(
                    len(text),
                    position + half,
                )

                results.append(
                    {
                        "page":
                            page_index + 1,
                        "score":
                            score,
                        "snippet":
                            text[
                                start:end
                            ],
                        "page_text_chars":
                            len(text),
                    }
                )

        results.sort(
            key=lambda item: (
                -item["score"],
                item["page"],
            )
        )

        results = results[
            :max_results
        ]

        return {
            "source_kind":
                "file",
            "path":
                self._display_path(
                    pdf_path
                ),
            "file_sha256":
                file_sha256(
                    pdf_path
                ),
            "query":
                query,
            "match_count":
                len(results),
            "results":
                results,
        }

    def read_pdf_pages(
        self,
        path: str,
        start_page: int,
        end_page: int | None = None,
        max_chars: int = 12000,
    ) -> dict[str, Any]:
        pdf_path = (
            self._require_pdf(
                path
            )
        )

        if end_page is None:
            end_page = start_page

        if (
            start_page < 1
            or end_page < start_page
        ):
            raise ValueError(
                "잘못된 page 범위입니다."
            )

        if not 1000 <= max_chars <= 50000:
            raise ValueError(
                "max_chars는 "
                "1000~50000이어야 합니다."
            )

        pages = []

        total_chars = 0

        with fitz.open(
            pdf_path
        ) as document:
            if end_page > document.page_count:
                raise ValueError(
                    "요청 page가 PDF 범위를 "
                    "초과합니다: "
                    f"{end_page} > "
                    f"{document.page_count}"
                )

            for page_number in range(
                start_page,
                end_page + 1,
            ):
                raw_text = (
                    document.load_page(
                        page_number - 1
                    ).get_text(
                        "text"
                    )
                    or ""
                )

                text = (
                    normalize_search_text(
                        raw_text
                    )
                )

                remaining = (
                    max_chars
                    - total_chars
                )

                if remaining <= 0:
                    break

                if len(text) > remaining:
                    text = text[
                        :remaining
                    ]

                pages.append(
                    {
                        "page":
                            page_number,
                        "text":
                            text,
                        "content_chars":
                            len(text),
                    }
                )

                total_chars += (
                    len(text)
                )

        return {
            "source_kind":
                "file",
            "path":
                self._display_path(
                    pdf_path
                ),
            "title":
                pdf_path.stem,
            "file_sha256":
                file_sha256(
                    pdf_path
                ),
            "page_count":
                len(pages),
            "start_page":
                start_page,
            "end_page":
                (
                    pages[-1]["page"]
                    if pages
                    else start_page
                ),
            "content_chars":
                total_chars,
            "pages":
                pages,
        }
