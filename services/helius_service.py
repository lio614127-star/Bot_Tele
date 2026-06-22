import os
import requests
from utils.logger import setup_logger
from utils.persistence import load_wallets

logger = setup_logger()

def sync_wallets_to_helius():
    """
    Syncs the current local wallets list to the Helius webhook configuration.
    """
    api_key = os.getenv("HELIUS_API_KEY")
    webhook_id = os.getenv("HELIUS_WEBHOOK_ID")
    
    if not api_key or not webhook_id:
        logger.warning("Missing HELIUS_API_KEY or HELIUS_WEBHOOK_ID. Skipping sync.")
        return False, "Thiếu cấu hình API Key hoặc Webhook ID của Helius trong .env."
        
    url = f"https://api.helius.xyz/v0/webhooks/{webhook_id}?api-key={api_key}"
    
    # Get current wallets
    wallets = load_wallets()
    addresses = [w['address'] for w in wallets]
    
    try:
        # 1. GET current webhook config so we don't overwrite other settings like URL
        get_response = requests.get(url, timeout=10)
        get_response.raise_for_status()
        current_config = get_response.json()
        
        # 2. Extract only valid fields for PUT request
        payload = {
            "webhookURL": current_config.get("webhookURL"),
            "transactionTypes": current_config.get("transactionTypes", ["TRANSFER"]),
            "accountAddresses": addresses,
            "webhookType": current_config.get("webhookType", "enhanced")
        }
        
        # 3. PUT the updated config
        put_response = requests.put(url, json=payload, timeout=10)
        put_response.raise_for_status()
        
        logger.info(f"Successfully synced {len(addresses)} wallets to Helius.")
        return True, f"Đã đồng bộ thành công {len(addresses)} ví lên Helius!"
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to sync with Helius API: {e}")
        return False, f"Lỗi khi đồng bộ lên Helius: {e}"
