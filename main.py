import hashlib
import re

from flask import Flask, jsonify, request
from flasgger import Swagger
from models import music_data, disease_data

app = Flask(__name__)

VERIFY_TOKEN = 'TUSUR-VASILEVA-20261110-5D238A8A'

app = Flask(__name__)

# Настройки Swagger
app.config["SWAGGER"] = {
    "title": "Music Service API",
    "uiversion": 3
}

swagger = Swagger(app)


@app.route("/", methods=["GET"])
def index():
    """
    Главная страница API
    ---
    tags:
      - Информация
    responses:
      200:
        description: API работает
        schema:
          type: object
          properties:
            message:
              type: string
            status:
              type: string
    """
    return jsonify({
        "message": "Music Service API",
        "status": "working"
    })


@app.route("/api/music", methods=["GET"])
def get_music():
    """
    Получение списка музыкальных произведений
    ---
    tags:
      - Музыкальные произведения
    responses:
      200:
        description: Список музыкальных произведений
        schema:
          type: array
          items:
            type: object
    """
    return jsonify(music_data)


@app.route("/api/music/<int:music_id>", methods=["GET"])
def get_music_by_id(music_id):
    """
    Получение музыкального произведения по ID
    ---
    tags:
      - Музыкальные произведения
    parameters:
      - name: music_id
        in: path
        type: integer
        required: true
        description: Идентификатор произведения
    responses:
      200:
        description: Найденное музыкальное произведение
      404:
        description: Произведение не найдено
    """
    for music in music_data:
        if music["id"] == music_id:
            return jsonify(music), 200

    return jsonify({"error": "Музыкальное произведение не найдено"}), 404


@app.route("/api/music", methods=["POST"])
def add_music():
    """
    Добавление музыкального произведения
    ---
    tags:
      - Музыкальные произведения
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            artist:
              type: string
            genre:
              type: string
            duration:
              type: number
            release_year:
              type: integer
            bpm:
              type: integer
            rating:
              type: number
            plays_count:
              type: integer
    responses:
      201:
        description: Произведение добавлено
      400:
        description: Некорректные данные
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Не переданы данные"}), 400

    required_fields = [
        "title", "artist", "genre", "duration",
        "release_year", "bpm", "rating", "plays_count"
    ]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Не все поля заполнены"}), 400

    new_music = {
        "id": max((music["id"] for music in music_data), default=0) + 1,
        **{field: data[field] for field in required_fields},
        "is_deleted": False
    }

    music_data.append(new_music)

    return jsonify(new_music), 201


@app.route("/api/music/<int:music_id>", methods=["PUT"])
def update_music(music_id):
    """
    Обновление музыкального произведения
    ---
    tags:
      - Музыкальные произведения
    parameters:
      - name: music_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: Произведение обновлено
      404:
        description: Произведение не найдено
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Не переданы данные"}), 400

    for music in music_data:
        if music["id"] == music_id:
            for field in music:
                if field != "id" and field in data:
                    music[field] = data[field]

            return jsonify(music), 200

    return jsonify({"error": "Музыкальное произведение не найдено"}), 404


@app.route("/api/music/<int:music_id>", methods=["DELETE"])
def delete_music(music_id):
    """Мягкое удаление музыкального произведения.
    ---
    tags:
      - Музыкальные произведения
    parameters:
      - name: music_id
        in: path
        type: integer
        required: true
      - name: confirm
        in: query
        type: boolean
        required: true
        description: Подтверждение удаления
    responses:
      200:
        description: Произведение перемещено в удалённые
      400:
        description: Необходимо подтвердить удаление
      404:
        description: Произведение не найдено
    """

    music = next(
        (
            item for item in music_data
            if item["id"] == music_id
            and not item.get("is_deleted", False)
        ),
        None
    )

    if music is None:
        return jsonify({"error": "Произведение не найдено"}), 404

    if request.args.get("confirm", "").lower() != "true":
        return jsonify({
            "message": "Подтвердите удаление, добавив параметр confirm=true",
            "id": music_id
        }), 400

    music["is_deleted"] = True

    return jsonify({
        "message": "Произведение успешно перемещено в удалённые",
        "id": music_id,
        "is_deleted": True
    }), 200


@app.route("/api/music/sort", methods=["GET"])
def sort_music():
    """
    Сортировка музыкальных произведений
    ---
    tags:
      - Музыкальные произведения
    parameters:
      - name: field
        in: query
        type: string
        required: true
        description: Поле для сортировки
        enum:
          - id
          - title
          - artist
          - genre
          - duration
          - release_year
          - bpm
          - rating
          - plays_count
      - name: order
        in: query
        type: string
        enum:
          - asc
          - desc
        default: asc
    responses:
      200:
        description: Отсортированный список произведений
      400:
        description: Некорректное поле сортировки
    """
    field = request.args.get("field")
    order = request.args.get("order", "asc")

    allowed_fields = [
        "id", "title", "artist", "genre",
        "duration", "release_year", "bpm",
        "rating", "plays_count"
    ]

    if field not in allowed_fields:
        return jsonify({"error": "Недопустимое поле сортировки"}), 400

    if order not in ["asc", "desc"]:
        return jsonify({"error": "Порядок сортировки должен быть asc или desc"}), 400

    sorted_music = sorted(
        music_data,
        key=lambda music: music[field],
        reverse=(order == "desc")
    )

    return jsonify(sorted_music), 200


@app.route("/api/music/statistics", methods=["GET"])
def music_statistics():
    """
    Статистика музыкальных произведений
    ---
    tags:
      - Музыкальные произведения
    responses:
      200:
        description: Статистика по числовым полям
    """
    numeric_fields = [
        "id",
        "duration",
        "release_year",
        "bpm",
        "rating",
        "plays_count"
    ]

    statistics = {}

    for field in numeric_fields:
        values = [music[field] for music in music_data]

        if values:
            statistics[field] = {
                "average": round(sum(values) / len(values), 2),
                "min": min(values),
                "max": max(values)
            }

    return jsonify(statistics), 200

@app.route("/info", methods=["GET"])
def info():
    """
    Информация о сервисе
    ---
    tags:
      - Информация
    responses:
      200:
        description: Информация о музыкальном сервисе
        schema:
          type: object
          properties:
            name:
              type: string
            version:
              type: string
            description:
              type: string
    """
    return jsonify({
        "name": "Music Service",
        "version": "1.0",
        "description": "API для работы с музыкальными произведениями"
    })

def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]
    lines = [re.sub(r'\s+', ' ', line) for line in lines]
    return '\n'.join(lines)


@app.route("/api/disease/", methods=["POST"])
def add_disease():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Не переданы данные"}), 400

    required_fields = [
        "country", "disease", "date",
        "sick", "recovered", "deaths"
    ]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Не все поля заполнены"}), 400

    new_disease = {
        "id": len(disease_data) + 1,
        **{field: data[field] for field in required_fields}
    }

    disease_data.append(new_disease)

    return jsonify(new_disease), 201


@app.route("/api/disease/", methods=["GET"])
def get_diseases():
    return jsonify(disease_data), 200


@app.route("/api/disease/<int:disease_id>", methods=["GET"])
def get_disease_by_id(disease_id):
    disease = next(
        (item for item in disease_data if item["id"] == disease_id),
        None
    )

    if disease is None:
        return jsonify({"error": "Запись не найдена"}), 404

    return jsonify(disease), 200


@app.after_request
def add_verify_hash(response):
    if (
        request.method == "GET"
        and re.match(r"^/api/disease/(?:\d+)?/?$", request.path)
        and response.status_code == 200
    ):
        body = response.get_data(as_text=True)
        normalized = normalize_text(body)

        body_hash = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        response.headers["X-Verify-Hash"] = body_hash

    return response

if __name__ == "__main__":
    app.run(debug=True)


