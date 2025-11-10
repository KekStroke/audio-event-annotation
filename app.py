"""
Audio Event Annotation Tool - главный файл Flask приложения.

Минимальное Flask приложение для запуска сервера.
"""

from flask import Flask, render_template_string

# Инициализация Flask приложения
app = Flask(__name__)

# Конфигурация
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 * 1024  # 16GB max file size


# Временный HTML шаблон для главной страницы
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Event Annotation Tool</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .status {
            color: #28a745;
            font-weight: bold;
        }
        .info {
            margin-top: 20px;
            padding: 15px;
            background-color: #e9ecef;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Audio Event Annotation Tool</h1>
        <p class="status">✓ Приложение успешно запущено!</p>
        <div class="info">
            <h3>Информация:</h3>
            <ul>
                <li>Версия: MVP (Минимально Жизнеспособный Продукт)</li>
                <li>Статус: Инициализация проекта завершена</li>
                <li>Доступно: Базовая структура и настройка окружения</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    """
    Главная страница приложения.

    Returns:
        str: HTML страница с приветствием
    """
    return render_template_string(HOME_TEMPLATE)


@app.route("/health")
def health():
    """
    Health check endpoint для проверки работоспособности приложения.

    Returns:
        dict: JSON ответ со статусом
    """
    return {"status": "ok", "message": "Audio Event Annotation Tool is running"}


if __name__ == "__main__":
    # Запуск приложения в режиме разработки
    app.run(host="127.0.0.1", port=5000, debug=True)
