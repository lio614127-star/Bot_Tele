import pytest
import time
from unittest.mock import patch, MagicMock
from services.alarm_manager import alarm_worker_loop

@pytest.fixture
def mock_deps():
    with patch('services.alarm_manager.get_alarm_state') as mock_get, \
         patch('services.alarm_manager.set_alarm_state') as mock_set, \
         patch('services.alarm_manager.send_alarm_message') as mock_send_alarm, \
         patch('services.alarm_manager.send_message') as mock_send, \
         patch('time.sleep', return_value=None): # Speed up tests
        yield mock_get, mock_set, mock_send_alarm, mock_send

def test_alarm_worker_loop_stops_when_inactive(mock_deps):
    mock_get, mock_set, mock_send_alarm, mock_send = mock_deps
    
    # First call active, second call inactive
    mock_get.side_effect = [
        {"is_active": True, "start_time": time.time(), "current_tx": {"amount": 1, "wallet": "W1", "signature": "S1"}},
        {"is_active": False}
    ]
    
    alarm_worker_loop()
    
    # Should have sent alarm message once
    assert mock_send_alarm.call_count == 1
    mock_send_alarm.assert_called_with(amount=1, wallet="W1", signature="S1")

def test_alarm_worker_loop_auto_stops_after_duration(mock_deps):
    mock_get, mock_set, mock_send_alarm, mock_send = mock_deps
    
    # start_time is 2000 seconds ago (max is 1200)
    mock_get.return_value = {
        "is_active": True, 
        "start_time": time.time() - 2000, 
        "current_tx": {"amount": 1, "wallet": "W1", "signature": "S1"}
    }
    
    # We need to break the loop or it will go forever in mock
    # Let's make it exit after one check by making it inactive
    mock_set.side_effect = lambda x: None # Mock set_alarm_state(False)
    
    # To prevent infinite loop in test, we can use side_effect to change return value
    mock_get.side_effect = [
        {"is_active": True, "start_time": time.time() - 2000, "current_tx": {}},
        {"is_active": False}
    ]
    
    alarm_worker_loop()
    
    # Should have called set_alarm_state(False)
    mock_set.assert_called_with(False)
    # Should have sent auto-stop message
    assert any("Auto-stop activated" in call[0][0] for call in mock_send.call_args_list)

def test_alarm_worker_loop_updates_content(mock_deps):
    mock_get, mock_set, mock_send_alarm, mock_send = mock_deps
    
    # First call Tx1, second call Tx2, third call inactive
    mock_get.side_effect = [
        {"is_active": True, "start_time": time.time(), "current_tx": {"amount": 10, "signature": "SIG1"}},
        {"is_active": True, "start_time": time.time(), "current_tx": {"amount": 20, "signature": "SIG2"}},
        {"is_active": False}
    ]
    
    alarm_worker_loop()
    
    assert mock_send_alarm.call_count == 2
    mock_send_alarm.assert_any_call(amount=10, wallet="Unknown", signature="SIG1")
    mock_send_alarm.assert_any_call(amount=20, wallet="Unknown", signature="SIG2")
