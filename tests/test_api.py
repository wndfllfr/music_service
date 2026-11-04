
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200


def test_info(client):
    response = client.get("/info")
    assert response.status_code == 200


def test_get_music(client):
    response = client.get("/api/music")
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_music_by_id(client):
    response = client.get("/api/music/1")
    assert response.status_code == 200
    assert response.json["title"] == "Night Drive"


def test_music_not_found(client):
    response = client.get("/api/music/999")
    assert response.status_code == 404


def test_sort_music(client):
    response = client.get("/api/music/sort?field=duration&order=asc")
    assert response.status_code == 200

    durations = [music["duration"] for music in response.json]
    assert durations == sorted(durations)


def test_statistics(client):
    response = client.get("/api/music/statistics")
    assert response.status_code == 200

    assert "duration" in response.json
    assert "average" in response.json["duration"]
    assert "min" in response.json["duration"]
    assert "max" in response.json["duration"]


def test_add_music(client):
    new_music = {
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "Pop",
        "duration": 200,
        "release_year": 2024,
        "bpm": 120,
        "rating": 9.0,
        "plays_count": 1000
    }

    response = client.post("/api/music", json=new_music)

    assert response.status_code == 201
    assert response.json["title"] == "Test Song"
    assert "id" in response.json


def test_update_music(client):
    updated_data = {
        "title": "Updated Song",
        "rating": 9.8
    }

    response = client.put("/api/music/1", json=updated_data)

    assert response.status_code == 200
    assert response.json["title"] == "Updated Song"
    assert response.json["rating"] == 9.8


def test_delete_music(client):
    response = client.delete("/api/music/4")

    assert response.status_code == 200
    assert response.json["id"] == 4

    check_response = client.get("/api/music/4")
    assert check_response.status_code == 404


def test_add_music_without_fields(client):
    response = client.post("/api/music", json={
        "title": "Incomplete Song"
    })

    assert response.status_code == 400


def test_sort_invalid_field(client):
    response = client.get(
        "/api/music/sort?field=unknown&order=asc"
    )

    assert response.status_code == 400


def test_update_missing_music(client):
    response = client.put(
        "/api/music/999",
        json={"title": "Unknown Song"}
    )

    assert response.status_code == 404
