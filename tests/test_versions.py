"""Проверка зафиксированных версий инструментов (AGENTS.md, п. 6а)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS_FILE = ROOT / "docs" / "sprint" / "VERSIONS.md"


def _versions() -> dict[str, str]:
    """Читает блок ```versions из VERSIONS.md."""
    values: dict[str, str] = {}
    in_block = False
    for line in VERSIONS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip() == "```versions":
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if in_block and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _docker_arg(name: str) -> str:
    prefix = f"ARG {name}="
    for line in (ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise AssertionError(f"В Dockerfile нет {prefix}")


def test_pandoc_cli_is_3_9() -> None:
    """Сервер обязан использовать Pandoc 3.9 (как pandoc-wasm 1.0.1)."""
    pandoc = shutil.which("pandoc")
    assert pandoc is not None, "pandoc не установлен"
    result = subprocess.run([pandoc, "--version"], capture_output=True, text=True, check=True)
    assert result.stdout.splitlines()[0] == "pandoc 3.9"


def test_dockerfile_matches_versions_md() -> None:
    versions = _versions()
    assert _docker_arg("PANDOC_VERSION") == versions["pandoc_server"]
    assert _docker_arg("TYPST_VERSION") == versions["typst_server"]


def test_pandoc_wasm_matches_server() -> None:
    versions = _versions()
    version_file = ROOT / "frontend" / "node_modules" / "pandoc-wasm" / "pandoc-version.txt"
    if version_file.exists():
        assert version_file.read_text(encoding="utf-8").strip() == versions["pandoc_wasm"]
    assert versions["pandoc_wasm"] == versions["pandoc_server"]


def test_typst_cli_matches_versions_md() -> None:
    typst = shutil.which("typst")
    if typst is None:
        return
    result = subprocess.run([typst, "--version"], capture_output=True, text=True, check=True)
    version = result.stdout.split()[1]
    assert version == _versions()["typst_local"]


def test_typst_server_matches_typst_ts() -> None:
    versions = _versions()
    assert versions["typst_server"] == versions["typst_ts"]

    script = ROOT / "frontend" / "scripts" / "typst-ts-version.mjs"
    wasm = (
        ROOT
        / "frontend"
        / "node_modules"
        / "@myriaddreamin"
        / "typst-ts-web-compiler"
        / "pkg"
        / "typst_ts_web_compiler_bg.wasm"
    )
    if shutil.which("node") is None or not wasm.exists():
        return
    result = subprocess.run(
        ["node", str(script)],
        cwd=ROOT / "frontend",
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip().splitlines()[-1] == versions["typst_ts"]
