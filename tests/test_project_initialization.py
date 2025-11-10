"""Step definitions для тестирования инициализации проекта."""

import os
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
import pytest

# Связываем сценарии из feature файла
scenarios("features/project_initialization.feature")


@pytest.fixture
def project_root():
    """Возвращает путь к корню проекта."""
    return Path(__file__).parent.parent


@given("я нахожусь в корне проекта")
def current_directory(project_root):
    """Устанавливаем контекст - корень проекта."""
    return project_root


@then(parsers.parse('должна существовать директория "{directory}"'))
def check_directory_exists(project_root, directory):
    """Проверяем существование директории."""
    dir_path = project_root / directory
    assert dir_path.exists(), f"Директория {directory} не существует"
    assert dir_path.is_dir(), f"{directory} не является директорией"


@then(parsers.parse('должен существовать файл "{filename}"'))
def check_file_exists(project_root, filename):
    """Проверяем существование файла."""
    file_path = project_root / filename
    assert file_path.exists(), f"Файл {filename} не существует"
    assert file_path.is_file(), f"{filename} не является файлом"


@given(parsers.parse('файл "{filename}" существует'))
def file_exists(project_root, filename):
    """Проверяем что файл существует перед его чтением."""
    file_path = project_root / filename
    assert file_path.exists(), f"Файл {filename} не существует"
    return file_path


@then(parsers.parse('файл "{filename}" должен содержать "{content}"'))
def check_file_contains(project_root, filename, content):
    """Проверяем что файл содержит указанную строку."""
    file_path = project_root / filename
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    assert (
        content.lower() in file_content.lower()
    ), f"Файл {filename} не содержит '{content}'"


@given('существует файл "app.py"')
def app_file_exists(project_root):
    """Проверяем существование app.py."""
    app_path = project_root / "app.py"
    assert app_path.exists(), "Файл app.py не существует"
    return app_path


@pytest.fixture
def flask_app_module(project_root):
    """Fixture для импорта Flask приложения."""
    import sys

    sys.path.insert(0, str(project_root))
    try:
        import app

        return app
    except ImportError as e:
        pytest.fail(f"Не удалось импортировать app: {e}")


@when("я импортирую Flask приложение")
def import_flask_app(flask_app_module):
    """Импортируем Flask приложение."""
    return flask_app_module


@then("приложение должно быть экземпляром Flask")
def check_flask_instance(flask_app_module):
    """Проверяем что app это экземпляр Flask."""
    from flask import Flask

    assert hasattr(flask_app_module, "app"), "Модуль app не содержит объект app"
    assert isinstance(flask_app_module.app, Flask), "app не является экземпляром Flask"


@then("приложение должно иметь корневой маршрут")
def check_root_route(flask_app_module):
    """Проверяем наличие корневого маршрута."""
    app = flask_app_module.app
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert "/" in rules, "Корневой маршрут '/' не найден"


@then("корневой маршрут должен возвращать статус 200")
def check_root_route_response(flask_app_module):
    """Проверяем что корневой маршрут возвращает 200."""
    app = flask_app_module.app
    with app.test_client() as client:
        response = client.get("/")
        assert (
            response.status_code == 200
        ), f"Корневой маршрут вернул статус {response.status_code} вместо 200"
