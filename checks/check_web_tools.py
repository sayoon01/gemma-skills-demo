"""웹 검색·페이지 읽기 도구가 동작하는지 확인한다."""

import json

from src.web_tools import WebTools


def main():
    tools = WebTools()

    print("===== SEARCH =====")

    result = tools.web_search(
        "physical AI robotics autonomous mobile manipulation",
        max_results=5,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    if not result["results"]:
        raise SystemExit("검색 결과 없음")

    url = result["results"][0]["url"]

    print("\n===== FETCH =====")
    print("URL:", url)

    try:
        page = tools.fetch_page(
            url,
            focus="physical AI robotics autonomous operation",
            max_chars=5000,
        )

        print(
            json.dumps(
                page,
                ensure_ascii=False,
                indent=2,
            )
        )

    except Exception as e:
        print(
            "FETCH ERROR:",
            type(e).__name__,
            str(e),
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
