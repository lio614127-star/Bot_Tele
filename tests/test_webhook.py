import pytest
import os
import json

# Set environment variables BEFORE importing app to bypass fail-fast check
os.environ['TELEGRAM_BOT_TOKEN'] = 'bot_token'
os.environ['TELEGRAM_CHAT_ID'] = '123456'
os.environ['SECRET_TOKEN'] = 'helius_secret'
os.environ['TARGET_WALLET'] = 'TARGET_WALLET_ADDR'
os.environ['MIN_SOL'] = '1.0'
os.environ['MAX_SOL'] = '100.0'
os.environ['ALARM_INTERVAL'] = '2'
os.environ['MAX_ALARM_DURATION'] = '1200'
os.environ['TELEGRAM_SECRET'] = 'tele_secret'

from app import app
from unittest.mock import patch

# Mock environment variables for testing (already set above)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'healthy' in rv.data

def test_webhook_unauthorized(client):
    # Wrong token
    rv = client.post('/webhook/wrong_token', json={})
    assert rv.status_code == 404

def test_webhook_no_payload(client):
    rv = client.post('/webhook/helius_secret', content_type='application/json')
    assert rv.status_code in [400, 415]

@patch('services.webhook_service.load_signatures')
@patch('services.webhook_service.save_signatures')
@patch('services.webhook_service.set_alarm_state')
def test_webhook_match(mock_set_alarm, mock_save, mock_load, client):
    mock_load.return_value = set()
    
    # Mock Helius payload: Outgoing transfer of 1.0 SOL from target wallet
    payload = [{
        "signature": "sig_123",
        "nativeTransfers": [
            {
                "fromUser": "TARGET_WALLET_ADDR",
                "toUser": "SOME_OTHER_ADDR",
                "amount": 1_000_000_000 # 1.0 SOL
            }
        ]
    }]
    
    rv = client.post('/webhook/helius_secret', json=payload)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'match_found'
    assert data['signature'] == 'sig_123'
    
    # Verify alarm was activated
    mock_set_alarm.assert_called_with(True)
    # Verify signature was saved
    mock_save.assert_called()

@patch('services.webhook_service.load_signatures')
def test_webhook_no_match_amount(mock_load, client):
    mock_load.return_value = set()
    
    # Amount too low (0.1 SOL, target is 0.5-1.5)
    payload = [{
        "signature": "sig_456",
        "nativeTransfers": [
            {
                "fromUser": "TARGET_WALLET_ADDR",
                "toUser": "SOME_OTHER_ADDR",
                "amount": 100_000_000 # 0.1 SOL
            }
        ]
    }]
    
    rv = client.post('/webhook/helius_secret', json=payload)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'processed'
    assert 'No matching' in data['message']

@patch('services.webhook_service.load_signatures')
def test_webhook_deduplication(mock_load, client):
    # Signature already exists
    mock_load.return_value = {'sig_already_done'}
    
    payload = [{
        "signature": "sig_already_done",
        "nativeTransfers": [
            {
                "fromUser": "TARGET_WALLET_ADDR",
                "toUser": "SOME_OTHER_ADDR",
                "amount": 1_000_000_000
            }
        ]
    }]
    
    rv = client.post('/webhook/helius_secret', json=payload)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'processed' # Not a match because it's a duplicate
