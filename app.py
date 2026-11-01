
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "applications.db"

app = Flask(__name__, static_folder=None)


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

        # Добавляем статус в существующую базу
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



# Главная страница
@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

# Админ страница
@app.route("/admin")
def admin():
    return send_from_directory(BASE_DIR, "admin.html")

# CSS, JavaScript и изображения
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


# Приём заявок
@app.route("/api/applications", methods=["POST"])
def create_application():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "message": "Некорректные данные"}), 400

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "Заполните имя и телефон"
        }), 400

    if len(name) > 100 or len(phone) > 30 or len(email) > 254 or len(message) > 3000:
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


# Просмотр заявок — только локально
@app.route("/api/applications", methods=["GET"])
def get_applications():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify({"success": False, "message": "Доступ запрещён"}), 403

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, name, phone, email, message, created_at, status
            FROM applications
            ORDER BY id DESC
        """).fetchall()

    return jsonify([dict(row) for row in rows])



# Изменение статуса заявки
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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
