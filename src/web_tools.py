"""Deep Research용 범용 웹 검색/페이지 읽기 도구."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 "
    "(X11; Linux x86_64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


class WebTools:
    """Gemma agent에서 사용할 범용 웹 검색 및 읽기 도구."""

    def __init__(
        self,
        timeout: int = 20,
        max_search_results: int = 5,
        max_fetch_chars: int = 8000,
    ):
        self.timeout = timeout
        self.max_search_results = max_search_results
        self.max_fetch_chars = max_fetch_chars

    def web_search(
        self,
        query: str,
        max_results: int | None = None,
    ) -> dict[str, Any]:
        """웹 검색 결과를 compact JSON으로 반환한다."""

        query = query.strip()
        if not query:
            raise ValueError("검색어가 비어 있습니다.")

        limit = max_results or self.max_search_results

        if not 1 <= limit <= 10:
            raise ValueError("max_results는 1~10이어야 합니다.")

        ddgs = DDGS(timeout=self.timeout)

        raw_results = ddgs.text(
            query,
            max_results=limit,
        )

        results = []

        for item in raw_results:
            title = str(item.get("title") or "").strip()
            url = str(
                item.get("href")
                or item.get("url")
                or ""
            ).strip()
            snippet = str(
                item.get("body")
                or item.get("snippet")
                or ""
            ).strip()

            if not url:
                continue

            results.append({
                "title": title,
                "url": url,
                "snippet": snippet[:1000],
                "domain": urlparse(url).netloc,
            })

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    def fetch_page(
        self,
        url: str,
        focus: str | None = None,
        max_chars: int | None = None,
    ) -> dict[str, Any]:
        """URL을 읽고 정리한 텍스트 일부를 반환한다."""

        url = url.strip()

        if not url.startswith(("http://", "https://")):
            raise ValueError("http 또는 https URL만 지원합니다.")

        char_limit = max_chars or self.max_fetch_chars

        if not 1000 <= char_limit <= 20000:
            raise ValueError("max_chars는 1000~20000이어야 합니다.")

        response = requests.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
            },
            allow_redirects=True,
        )

        response.raise_for_status()

        content_type = (
            response.headers
            .get("content-type", "")
            .lower()
        )

        if "text/html" not in content_type:
            raise ValueError(
                f"현재 HTML 페이지만 지원합니다: {content_type}"
            )

        soup = BeautifulSoup(
            response.text,
            "lxml",
        )

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "form",
        ]):
            tag.decompose()

        raw_text = "\n".join(
            line.strip()
            for line in soup.get_text("\n").splitlines()
            if line.strip()
        )

        raw_text = re.sub(
            r"\n{3,}",
            "\n\n",
            raw_text,
        )

        content = self._select_relevant_text(
            raw_text,
            focus=focus,
            max_chars=char_limit,
        )

        return {
            "url": response.url,
            "title": title,
            "domain": urlparse(response.url).netloc,
            "focus": focus,
            "content": content,
            "content_chars": len(content),
            "truncated": len(content) < len(raw_text),
        }

    @staticmethod
    def _select_relevant_text(
        text: str,
        focus: str | None,
        max_chars: int,
    ) -> str:
        """간단한 키워드 기반 span filtering."""

        if not focus:
            return text[:max_chars]

        keywords = [
            word.lower()
            for word in re.findall(
                r"[A-Za-z0-9가-힣_-]{2,}",
                focus,
            )
        ]

        if not keywords:
            return text[:max_chars]

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n")
            if paragraph.strip()
        ]

        scored = []

        for index, paragraph in enumerate(paragraphs):
            lower = paragraph.lower()

            score = sum(
                1
                for keyword in keywords
                if keyword in lower
            )

            if score:
                scored.append((
                    score,
                    index,
                    paragraph,
                ))

        if not scored:
            return text[:max_chars]

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected_indexes = set()

        for _, index, _ in scored[:20]:
            for nearby in range(
                max(0, index - 1),
                min(len(paragraphs), index + 2),
            ):
                selected_indexes.add(nearby)

        selected = "\n".join(
            paragraphs[index]
            for index in sorted(selected_indexes)
        )

        return selected[:max_chars]
