import json
import time
import requests
import secrets  # Cryptographically strong random numbers
from web3 import Web3

# --- CONFIGURATION ---
# Connect to Avalanche Fuji Testnet
avalanche_url = "https://api.avax-test.network/ext/bc/C/rpc"
web3 = Web3(Web3.HTTPProvider(avalanche_url))

# --- DYNAMIC CHECKSUM CONVERSION ---
# We use lowercase here, and let the library fix the capitalization automatically.
# This prevents the "Invalid EIP-55 checksum" error.
contract_address = Web3.to_checksum_address("YOURCONTRACTADDRESS")
my_address = Web3.to_checksum_address("YOURWALLETADDRESS")

# YOUR WALLET PRIVATE KEY
private_key = "YOURKEYHERE"

# The ABI
contract_abi = [
    {"inputs": [{"internalType": "uint256","name": "_number","type": "uint256"}],"name": "fulfillRoll","outputs": [],"stateMutability": "nonpayable","type": "function"},
    {"inputs": [],"name": "requestRoll","outputs": [],"stateMutability": "nonpayable","type": "function"},
    {"inputs": [],"stateMutability": "nonpayable","type": "constructor"},
    {"anonymous": False,"inputs": [{"indexed": False,"internalType": "uint256","name": "result","type": "uint256"}],"name": "RollFulfilled","type": "event"},
    {"anonymous": False,"inputs": [{"indexed": False,"internalType": "address","name": "requester","type": "address"}],"name": "RollRequested","type": "event"},
    {"inputs": [],"name": "isRolling","outputs": [{"internalType": "bool","name": "","type": "bool"}],"stateMutability": "view","type": "function"},
    {"inputs": [],"name": "lastResult","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"},
    {"inputs": [],"name": "oracle","outputs": [{"internalType": "address","name": "","type": "address"}],"stateMutability": "view","type": "function"}
]

# Initialize Contract
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

def get_true_random_number():
    """Tries Quantum API first, falls back to Local Hardware Entropy"""
    
    # 1. Try the Australian National University Quantum Lab
    try:
        response = requests.get('https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint8', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                raw_num = data['data'][0]
                dice_roll = (raw_num % 6) + 1
                print(f"⚛️  Quantum Vacuum Data: {raw_num} -> Dice: {dice_roll}")
                return dice_roll
    except Exception as e:
        # Just logging the failure so you know it happened
        print(f"⚠️  Quantum API unreachable ({e}).")

    # 2. Fallback: Local Hardware Entropy (Cryptographically Secure)
    # This uses your OS's entropy pool (interrupts, thermal noise, etc.)
    print("💻 Switching to Local Hardware Entropy...")
    dice_roll = secrets.randbelow(6) + 1
    print(f"🔒 Secure Local Randomness -> Dice: {dice_roll}")
    return dice_roll

def fulfill_request(random_number):
    """Sends the number to the smart contract"""
    try:
        # Get fresh nonce (transaction count)
        nonce = web3.eth.get_transaction_count(my_address)
        
        # Build the transaction
        txn = contract.functions.fulfillRoll(random_number).build_transaction({
            'chainId': 43113, 
            'gas': 80000,
            'gasPrice': web3.to_wei('30', 'gwei'),
            'nonce': nonce,
        })
        
        # Sign the transaction
        signed_txn = web3.eth.account.sign_transaction(txn, private_key=private_key)
        
        # --- UNIVERSAL ADAPTER (Fixes the Attribute Error) ---
        # We try to get the raw bytes in every possible format to satisfy your specific library version.
        try:
            raw_tx_bytes = signed_txn.rawTransaction
        except AttributeError:
            try:
                raw_tx_bytes = signed_txn.raw_transaction
            except AttributeError:
                # If both fail, it's likely a tuple/list, so we grab the first element
                raw_tx_bytes = signed_txn[0]
        # -----------------------------------------------------

        # Send it!
        tx_hash = web3.eth.send_raw_transaction(raw_tx_bytes)
        
        print(f"🚀 Data sent to Blockchain! Hash: {web3.to_hex(tx_hash)}")
        
        # Wait for receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ Transaction Confirmed on Avalanche.")
        else:
            print("❌ Transaction Failed on Blockchain.")

    except Exception as e:
        print(f"❌ Blockchain Error: {e}")
        # Debugging helper
        if 'signed_txn' in locals():
            print(f"DEBUG: Object type: {type(signed_txn)}")
            print(f"DEBUG: Object attributes: {dir(signed_txn)}")

def main_loop():
    print(f"Listening to contract: {contract_address}...")
    print(f"Oracle Wallet: {my_address}")
    
    while True:
        try:
            is_rolling = contract.functions.isRolling().call()
            
            if is_rolling:
                print("\n🎲 Roll Requested! Processing...")
                q_num = get_true_random_number()
                fulfill_request(q_num)
                print("Waiting for next request...")
            else:
                pass
            
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n🛑 Oracle stopped by user.")
            break
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main_loop()
