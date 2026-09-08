"""B2 Markdown Runtime Contract Loader."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CONTRACT_ROOT = (
    ROOT
    / "runtime"
    / "b2"
)


class ContractError(
    ValueError
):
    pass


def load_contract(
    name: str,
    *,
    root: Path | None = None,
) -> str:
    contract_root = (
        Path(root).resolve()
        if root is not None
        else DEFAULT_CONTRACT_ROOT
    )

    if not name:
        raise ContractError(
            "Contract 이름이 비어 있습니다."
        )

    if not name.endswith(".md"):
        name = f"{name}.md"

    path = (
        contract_root
        / name
    ).resolve()

    try:
        path.relative_to(
            contract_root.resolve()
        )
    except ValueError:
        raise ContractError(
            "Contract root 밖의 파일은 "
            "읽을 수 없습니다."
        )

    if not path.is_file():
        raise ContractError(
            f"Contract 파일이 없습니다: "
            f"{path}"
        )

    text = path.read_text(
        encoding="utf-8-sig"
    ).strip()

    if not text:
        raise ContractError(
            f"Contract가 비어 있습니다: "
            f"{path}"
        )

    return text


def load_b2_contracts(
    *,
    root: Path | None = None,
) -> dict[str, str]:
    names = [
        "controller",
        "worker",
        "evidence-policy",
        "verification",
        "replan",
        "convergence",
        "synthesis",
    ]

    return {
        name: load_contract(
            name,
            root=root,
        )
        for name in names
    }
