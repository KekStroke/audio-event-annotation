"""Step definitions for frontend global state validation."""
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then

scenarios("features/frontend_state.feature")


@pytest.fixture
def context():
    """Shared context for steps."""
    return {}


@given('директория фронтенда "static/js"')
def frontend_directory(context):
    """Store the frontend directory path in context."""
    scripts_dir = Path("static/js")
    assert scripts_dir.exists(), "Директория static/js не найдена"
    context["scripts_dir"] = scripts_dir


@then("JS файлы не должны содержать конфликтующие объявления глобальных переменных")
def no_conflicting_global_declarations(context):
    """Ensure conflicting global let declarations are absent."""
    scripts_dir: Path = context["scripts_dir"]
    forbidden_patterns = ("let currentAudioFileId", "let currentRegion")

    offenders = []
    for script_path in scripts_dir.rglob("*.js"):
        content = script_path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in content:
                offenders.append((script_path, pattern))

    assert not offenders, (
        "Обнаружены конфликтующие глобальные объявления: "
        + ", ".join(f"{path} содержит '{pattern}'" for path, pattern in offenders)
    )

