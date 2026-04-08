"""Tests for Google Chat webhook handling."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_added_to_dm():
    event = {
        "type": "ADDED_TO_SPACE",
        "space": {"type": "DM"},
    }
    response = client.post("/chat/webhook", json=event)
    assert response.status_code == 200
    assert "personal" in response.json()["text"].lower()


def test_added_to_space():
    event = {
        "type": "ADDED_TO_SPACE",
        "space": {"type": "ROOM"},
    }
    response = client.post("/chat/webhook", json=event)
    assert response.status_code == 200


def test_removed_from_space():
    event = {"type": "REMOVED_FROM_SPACE"}
    response = client.post("/chat/webhook", json=event)
    assert response.status_code == 200


def test_empty_message():
    event = {
        "type": "MESSAGE",
        "message": {"text": ""},
        "user": {"name": "users/123", "displayName": "Test User"},
        "space": {"name": "spaces/abc"},
    }
    response = client.post("/chat/webhook", json=event)
    assert response.status_code == 200
    assert "didn't catch" in response.json()["text"].lower()
