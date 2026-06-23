import requests
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger()

def get_wallet_info(address):
    """
    Queries Solana mainnet-beta public RPC to get wallet information.
    Returns: balance (SOL), is_new (bool), oldest_tx_time (str)
    """
    url = 'https://api.mainnet-beta.solana.com'
    
    try:
        # 1. Get Balance
        res_bal = requests.post(url, json={
            'jsonrpc': '2.0', 'id': 1,
            'method': 'getBalance',
            'params': [address]
        }, timeout=5).json()
        balance = res_bal.get('result', {}).get('value', 0) / 1e9
        
        # 2. Get Recent Signatures to determine if new
        res_sigs = requests.post(url, json={
            'jsonrpc': '2.0', 'id': 2,
            'method': 'getSignaturesForAddress',
            'params': [address, {'limit': 10}]
        }, timeout=5).json()
        
        sigs = res_sigs.get('result', [])
        
        # Determine if it's a "New" wallet (less than or equal to 5 transactions)
        is_new = len(sigs) <= 5
        
        oldest_tx_time = 'N/A'
        if sigs:
            timestamp = sigs[-1].get('blockTime')
            if timestamp:
                oldest_tx_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
        return balance, is_new, oldest_tx_time
    except Exception as e:
        logger.error(f"Error querying RPC for {address}: {e}")
        return 0.0, False, 'N/A'
