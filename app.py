
import os
import hmac
import re
import sqlite3

from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, Response

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "applications.db"

app = Flask(__name__, static_folder=None)

# Пароль задаётся в настройках Render
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


# Создание базы данных
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = [
            row[1] for row in conn.execute(
                "PRAGMA table_info(applications)"
            )
        ]

        if "status" not in columns:
            conn.execute("""
                ALTER TABLE applications
                ADD COLUMN status TEXT NOT NULL DEFAULT 'new'
            """)


# Проверка пароля администратора
def admin_required():
    if not ADMIN_PASSWORD:
        return jsonify({
            "success": False,
            "message": "Пароль администратора не настроен"
        }), 503

    auth = request.authorization

    if (
        not auth
        or auth.username != "admin"
        or not auth.password
        or not hmac.compare_digest(auth.password, ADMIN_PASSWORD)
    ):
        response = Response(
            "Требуется авторизация",
            401,
            {"WWW-Authenticate": 'Basic realm="INK HOUSE Admin"'}
        )
        return response

    return None


# Защита админки и операций с заявками
@app.before_request
def protect_admin():
    protected = (
        request.path == "/admin"
        or (
            request.path.startswith("/api/applications")
            and request.method in ("GET", "PATCH", "DELETE")
        )
    )

    if protected:
        return admin_required()


# Главная страница
@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# Страница администратора
@app.route("/admin")
def admin():
    return send_from_directory(BASE_DIR, "admin.html")


# Разрешённые публичные файлы сайта
@app.route("/<path:filename>")
def static_files(filename):
    allowed_files = {
        "style.css",
        "admin.css",
        "script.js",
        "admin.js"
        "favicon.png"
    }

    allowed_image = re.fullmatch(
        r"(hero|tattoo[1-8])\.avif",
        filename
    )

    if filename not in allowed_files and not allowed_image:
        return "Файл не найден", 404

    return send_from_directory(BASE_DIR, filename)


# Приём заявок — публичный
@app.route("/api/applications", methods=["POST"])
def create_application():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Некорректные данные"
        }), 400

    name = data.get("name", "")
    phone = data.get("phone", "")
    email = data.get("email", "")
    message = data.get("message", "")

    if not all(isinstance(x, str) for x in (name, phone, email, message)):
        return jsonify({
            "success": False,
            "message": "Некорректные данные"
        }), 400

    name = name.strip()
    phone = phone.strip()
    email = email.strip()
    message = message.strip()

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "Заполните имя и телефон"
        }), 400

    if (
        len(name) > 100
        or len(phone) > 30
        or len(email) > 254
        or len(message) > 3000
    ):
        return jsonify({
            "success": False,
            "message": "Слишком длинные данные"
        }), 400

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO applications (name, phone, email, message)
            VALUES (?, ?, ?, ?)
        """, (name, phone, email, message))

    return jsonify({
        "success": True,
        "message": "Заявка успешно сохранена!"
    }), 201


# Просмотр заявок — только после авторизации
@app.route("/api/applications", methods=["GET"])
def get_applications():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT id, name, phone, email, message, created_at, status
            FROM applications
            ORDER BY id DESC
        """).fetchall()

    return jsonify([dict(row) for row in rows])


# Изменение статуса
@app.route("/api/applications/<int:application_id>", methods=["PATCH"])
def update_application(application_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ("new", "completed"):
        return jsonify({
            "success": False,
            "message": "Некорректный статус"
        }), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute("""
            UPDATE applications
            SET status = ?
            WHERE id = ?
        """, (status, application_id))

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Заявка не найдена"
            }), 404

    return jsonify({"success": True})


# Удаление заявки
@app.route("/api/applications/<int:application_id>", methods=["DELETE"])
def delete_application(application_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute("""
            DELETE FROM applications
            WHERE id = ?
        """, (application_id,))

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Заявка не найдена"
            }), 404

    return jsonify({"success": True})


# База создаётся и при запуске через Gunicorn
init_db()


if __name__ == "__main__":
    app.run(debug=False)
