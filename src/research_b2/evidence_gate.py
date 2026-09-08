"""B2 Worker 결과의 deterministic Evidence Gate.

이 모듈은 연구 내용을 판단하지 않는다.

기계적으로 확인 가능한 사실만 검사한다.

- Worker가 인용한 URL을 실제 fetch했는가?
- fetch가 성공했는가?
- 실제 읽은 URL과 citation URL이 일치하는가?

Claim의 의미적 지지 여부는 이후 Semantic Verification 단계에서 처리한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


def canonical_url(
    url: str,
) -> str:
    value = (
        url
        or ""
    ).strip()

    if not value:
        return ""

    parts = urlsplit(
        value
    )

    query = []

    for key, item in parse_qsl(
        parts.query,
        keep_blank_values=True,
    ):
        if key.lower().startswith(
            "utm_"
        ):
            continue

        query.append(
            (key, item)
        )

    path = parts.path

    if path != "/":
        path = path.rstrip("/")

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(query),
            "",
        )
    )


def build_fetch_index(
    tool_logs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """성공한 fetch_page 결과를 canonical URL 기준으로 색인한다."""

    index: dict[
        str,
        dict[str, Any],
    ] = {}

    for log in tool_logs:
        if (
            log.get("name")
            != "fetch_page"
        ):
            continue

        if log.get("ok") is not True:
            continue

        result = (
            log.get("result")
            or {}
        )

        if result.get("ok") is not True:
            continue

        data = (
            result.get("data")
            or {}
        )

        requested_url = (
            (log.get("arguments") or {})
            .get("url")
            or ""
        )

        final_url = (
            data.get("url")
            or ""
        )

        record = {
            "requested_url":
                requested_url,
            "final_url":
                final_url,
            "title":
                data.get("title")
                or "",
            "domain":
                data.get("domain")
                or "",
            "content":
                data.get("content")
                or "",
            "content_chars":
                data.get(
                    "content_chars"
                )
                or 0,
            "turn":
                log.get("turn"),
        }

        if requested_url:
            index[
                canonical_url(
                    requested_url
                )
            ] = record

        if final_url:
            index[
                canonical_url(
                    final_url
                )
            ] = record

    return index


def validate_worker_result(
    worker_result: dict[str, Any],
    tool_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    fetch_index = (
        build_fetch_index(
            tool_logs
        )
    )

    accepted_claims = []
    unsupported_claims = []

    rejected_sources = []

    claims = (
        worker_result.get("claims")
        or []
    )

    for claim_index, claim in enumerate(
        claims,
        1,
    ):
        if not isinstance(
            claim,
            dict,
        ):
            continue

        validated_sources = []

        sources = (
            claim.get("sources")
            or []
        )

        for source_index, source in enumerate(
            sources,
            1,
        ):
            if not isinstance(
                source,
                dict,
            ):
                continue

            source_kind = (
                source.get(
                    "source_kind"
                )
                or ""
            )

            if source_kind != "web":
                rejected_sources.append(
                    {
                        "claim_index":
                            claim_index,
                        "source_index":
                            source_index,
                        "state":
                            "UNSUPPORTED_KIND",
                        "source":
                            source,
                    }
                )

                continue

            url = (
                source.get("url")
                or ""
            ).strip()

            canonical = (
                canonical_url(
                    url
                )
            )

            fetch = (
                fetch_index.get(
                    canonical
                )
            )

            if fetch is None:
                rejected_sources.append(
                    {
                        "claim_index":
                            claim_index,
                        "source_index":
                            source_index,
                        "state":
                            "UNREAD",
                        "source":
                            source,
                    }
                )

                continue

            validated_source = (
                dict(source)
            )

            validated_source[
                "verification_state"
            ] = "FETCHED"

            validated_source[
                "retrieved_title"
            ] = fetch[
                "title"
            ]

            validated_source[
                "retrieved_url"
            ] = fetch[
                "final_url"
            ]

            validated_source[
                "retrieved_content_chars"
            ] = fetch[
                "content_chars"
            ]

            validated_sources.append(
                validated_source
            )

        validated_claim = (
            dict(claim)
        )

        validated_claim[
            "sources"
        ] = validated_sources

        verified_count = len(
            validated_sources
        )

        validated_claim[
            "verified_source_count"
        ] = verified_count

        if verified_count == 0:
            validated_claim[
                "validation_status"
            ] = "UNSUPPORTED"

            unsupported_claims.append(
                validated_claim
            )

        elif verified_count == 1:
            validated_claim[
                "validation_status"
            ] = "SINGLE_SOURCE"

            accepted_claims.append(
                validated_claim
            )

        else:
            # 이 단계에서는 publisher 독립성 및
            # 의미적 support를 아직 판정하지 않는다.
            validated_claim[
                "validation_status"
            ] = (
                "MULTI_SOURCE_PENDING_AUDIT"
            )

            accepted_claims.append(
                validated_claim
            )

    return {
        "accepted_claims":
            accepted_claims,
        "unsupported_claims":
            unsupported_claims,
        "rejected_sources":
            rejected_sources,
        "summary": {
            "raw_claim_count":
                len(claims),
            "accepted_claim_count":
                len(
                    accepted_claims
                ),
            "unsupported_claim_count":
                len(
                    unsupported_claims
                ),
            "rejected_source_count":
                len(
                    rejected_sources
                ),
            "successful_fetch_source_count":
                len(
                    {
                        record[
                            "final_url"
                        ]
                        for record
                        in fetch_index.values()
                        if record[
                            "final_url"
                        ]
                    }
                ),
        },
    }


def load_json(
    path: Path,
) -> Any:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--worker-result",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--tool-calls",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    worker_result = load_json(
        args.worker_result
    )

    tool_logs = load_json(
        args.tool_calls
    )

    result = validate_worker_result(
        worker_result,
        tool_logs,
    )

    args.output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            result["summary"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        "saved:",
        args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
