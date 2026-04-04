"""Tests for the /api/chat and /api/summary AI endpoints."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_summary_success():
    """Test successful summary generation with mocked Anthropic."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="This is a summary. With exact numbers.")]
    
    with patch("backend.routes.ai.client.messages.create", return_value=mock_msg) as mock_create:
        resp = client.post(
            "/api/summary",
            params={"query": "test", "chart_type": "timeseries"},
            json=[{"date": "2022-02-24", "count": 10}]
        )
        assert resp.status_code == 200
        assert resp.json()["summary"] == "This is a summary. With exact numbers."
        assert resp.json().get("error") is None
        
        # Verify call params
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        system_p = kwargs["system"]
        assert "mention exact numbers" in system_p
        
        user_p = kwargs["messages"][0]["content"]
        assert "timeseries data for the query 'test'" in user_p
        assert "2022-02-24" in user_p


def test_summary_api_error():
    """Test that summary handles API errors without crashing."""
    with patch("backend.routes.ai.client.messages.create", side_effect=Exception("API Down")):
        resp = client.post(
            "/api/summary",
            params={"query": "test", "chart_type": "network"},
            json={"nodes": [], "edges": []}
        )
        assert resp.status_code == 200
        assert resp.json()["error"] == "AI service unavailable"


def test_chat_success():
    """Test successful chat generation and SUGGESTIONS parsing."""
    mock_text = "Here is the analysis based on data.\nSUGGESTIONS: [how did reddit react?] | [what about twitter?] | [key authors]"
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=mock_text)]
    
    with patch("backend.routes.ai.client.messages.create", return_value=mock_msg) as mock_create:
        resp = client.post(
            "/api/chat",
            json={
                "message": "analyze this",
                "context": "r/Anarchism",
                "history": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi"}
                ]
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "Here is the analysis based on data."
        assert len(data["suggestions"]) == 3
        assert "what about twitter?" in data["suggestions"]
        assert data.get("error") is None
        
        # Verify system prompt config
        kwargs = mock_create.call_args.kwargs
        assert "r/Anarchism" in kwargs["system"]
        
        # Verify history got mapped correctly
        msgs = kwargs["messages"]
        assert len(msgs) == 3
        assert msgs[0]["content"] == "hello"
        assert msgs[-1]["content"] == "analyze this"


def test_chat_api_error():
    """Test that chat gracefully handles API errors."""
    with patch("backend.routes.ai.client.messages.create", side_effect=Exception("Timeout")):
        resp = client.post(
            "/api/chat",
            json={"message": "hello"}
        )
        assert resp.status_code == 200
        assert resp.json()["error"] == "AI service unavailable"
