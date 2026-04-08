import pytest
import os
import json
from unittest.mock import patch, MagicMock

# Set environment variables BEFORE importing app to bypass fail-fast check
os.environ['TELEGRAM_SECRET'] = 'tele_secret'
os.environ['TELEGRAM_CHAT_ID'] = '123456'
os.environ['TELEGRAM_BOT_TOKEN'] = 'bot_token'
os.environ['TARGET_WALLET'] = 'WALLET_ADDR'
os.environ['SECRET_TOKEN'] = 'helius_secret'
os.environ['ALARM_INTERVAL'] = '2'
os.environ['MAX_ALARM_DURATION'] = '1200'

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_telegram_unauthorized_token(client):
    rv = client.post('/telegram/wrong_token', json={})
    assert rv.status_code == 404

def test_telegram_ignore_wrong_chat(client):
    with patch('services.telegram_service.send_message') as mock_send:
        payload = {
            "message": {
                "chat": {"id": 999999}, # Wrong Chat ID
                "text": "/stop"
            }
        }
        rv = client.post('/telegram/tele_secret', json=payload)
        assert rv.status_code == 200
        mock_send.assert_not_called()

@patch('services.telegram_service.set_alarm_state')
@patch('services.telegram_service.send_message')
def test_telegram_stop_command(mock_send, mock_set_state, client):
    payload = {
        "message": {
            "chat": {"id": 123456}, # Correct Chat ID
            "text": "/stop"
        }
    }
    rv = client.post('/telegram/tele_secret', json=payload)
    assert rv.status_code == 200
    mock_set_state.assert_called_with(False)
    mock_send.assert_called()
    assert "dừng báo động" in mock_send.call_args[0][0].lower()

@patch('services.telegram_service.get_alarm_state')
@patch('services.telegram_service.send_message')
def test_telegram_status_command(mock_send, mock_get_state, client):
    mock_get_state.return_value = True
    payload = {
        "message": {
            "chat": {"id": 123456},
            "text": "/status"
        }
    }
    rv = client.post('/telegram/tele_secret', json=payload)
    assert rv.status_code == 200
    mock_send.assert_called()
    assert "ĐANG BÁO ĐỘNG" in mock_send.call_args[0][0]

@patch('services.telegram_service.set_alarm_state')
@patch('requests.post')
@patch('services.telegram_service.send_message')
def test_telegram_callback_stop(mock_send, mock_post, mock_set_state, client):
    payload = {
        "callback_query": {
            "id": "cb_123",
            "from": {"id": 123456},
            "data": "stop_alarm"
        }
    }
    rv = client.post('/telegram/tele_secret', json=payload)
    assert rv.status_code == 200
    mock_set_state.assert_called_with(False)
    # Verify callback was answered
    mock_post.assert_called()
    assert "answerCallbackQuery" in mock_post.call_args[0][0]
    mock_send.assert_called_with("🛑 Đã dừng báo động từ nút bấm.")
