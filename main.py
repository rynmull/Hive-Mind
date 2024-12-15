import asyncio
import json
import websockets
import requests
import os
from flask import Flask, send_from_directory, jsonify, request
import threading
from datetime import datetime
from solana.transaction import Transaction, TransactionInstruction
from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.keypair import Keypair

# Initialize Flask app
app = Flask(__name__)

# Access environment variables
private_key = os.getenv("PRIVATE_KEY")
rpc_endpoint = os.getenv("RPC_ENDPOINT")

# Initialize Solana client
solana_client = Client(rpc_endpoint)

# Phantom wallet public key
wallet_public_key = PublicKey("1342etfFbEfBK12i6MuDYgVBhpacjLwNkoSaz9wPnC1W")

# Constants for WebSocket and API
PUMP_WS_URL = "wss://pumpportal.fun/api/data"

# Adaptive parameters
adaptive_parameters = {
    "trending_threshold": 5,
    "profit_take_percentage": 20,
    "loss_cut_percentage": 10
}

# Persistent state
state = {
    "parameters": adaptive_parameters,
    "profit": 0,
    "recent_trades": [],
    "current_token": None,
    "current_token_buys": 0,
    "buy_price": None,
    "wallet_balance": 0
}

# WebSocket handler
async def monitor_pump_fun():
    async with websockets.connect(PUMP_WS_URL) as websocket:
        # Subscribe to token trade events
        await websocket.send(json.dumps({"method": "subscribeTokenTrade"}))
        print("Subscribed to Pump.fun WebSocket.")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "method" in data and data["method"] == "tokenTrade":
                    process_token_trade(data["params"])
            except websockets.ConnectionClosed:
                print("WebSocket connection closed. Reconnecting...")
                await asyncio.sleep(5)
                await monitor_pump_fun()

# Process token trade messages
def process_token_trade(trade_data):
    token = trade_data.get("mint", None)
    buys = trade_data.get("buys", 0)
    price = float(trade_data.get("price", 0))

    if token:
        state["current_token"] = token
        state["current_token_buys"] = buys
        state["buy_price"] = price
        print(f"Current Token: {token}, Buys: {buys}, Price: {price}")

        # Trigger a trade if conditions are met
        if buys >= state["parameters"]["trending_threshold"] and not state["current_token"]:
            execute_trade("buy", token, price)

# Trade execution function
def execute_trade(action, token, price):
    try:
        # Extract the keypair from the private key
        private_key_bytes = bytes.fromhex(private_key)
        keypair = Keypair.from_secret_key(private_key_bytes)

        if action == "buy":
            # Create a dummy transaction for buying
            instruction = TransactionInstruction(
                keys=[],
                program_id=PublicKey(token),  # Replace with actual program ID for the token
                data=b"Buy"  # Program-specific data
            )
            txn = Transaction().add(instruction)

            # Sign and send the transaction
            txn_signature = solana_client.send_transaction(txn, keypair)
            print(f"Transaction signature: {txn_signature}")

            # Update state
            state["current_token"] = token
            state["buy_price"] = price
            state["recent_trades"].append({"action": "buy", "token": token, "price": price, "time": str(datetime.now())})
            print(f"Bought {token} at {price} SOL.")

        elif action == "sell":
            # Create a dummy transaction for selling
            instruction = TransactionInstruction(
                keys=[],
                program_id=PublicKey(token),  # Replace with actual program ID for the token
                data=b"Sell"  # Program-specific data
            )
            txn = Transaction().add(instruction)

            # Sign and send the transaction
            txn_signature = solana_client.send_transaction(txn, keypair)
            print(f"Transaction signature: {txn_signature}")

            # Update state
            profit = (price - state["buy_price"]) * 0.1  # Assuming 0.1 SOL quantity
            state["profit"] += profit
            state["recent_trades"].append({"action": "sell", "token": token, "price": price, "profit": profit, "time": str(datetime.now())})
            state["current_token"] = None
            state["buy_price"] = None
            print(f"Sold {token} at {price} SOL. Profit: {profit} SOL.")

    except Exception as e:
        print(f"Error executing trade: {e}")

# Fetch wallet balance from RPC endpoint
def fetch_wallet_balance():
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": ["1342etfFbEfBK12i6MuDYgVBhpacjLwNkoSaz9wPnC1W"]  # Replace with your wallet public key
        }
        response = requests.post(rpc_endpoint, headers=headers, json=payload)

        response_data = response.json()
        balance = response_data.get("result", {}).get("value", 0) / 10**9  # Convert lamports to SOL
        state["wallet_balance"] = balance
        print(f"Fetched wallet balance: {balance} SOL")
    except Exception as e:
        print(f"Error fetching wallet balance: {e}")
        state["wallet_balance"] = 0

@app.route("/api/get-slot", methods=["GET"])  # New route to fetch the current Solana slot
def get_slot():
    try:
        current_slot = solana_client.get_slot()
        print(f"Current Slot: {current_slot['result']}")
        return jsonify({"slot": current_slot["result"]})
    except Exception as e:
        print(f"Error fetching slot: {e}")
        return jsonify({"error": str(e)}), 500

# Flask routes
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

@app.route("/api/status", methods=["GET"])
def api_status():
    fetch_wallet_balance()  # Update wallet balance before returning status
    return jsonify({
        "current_token": state["current_token"],
        "wallet_balance": state["wallet_balance"],
        "current_token_buys": state["current_token_buys"],
        "buy_price": state["buy_price"],
        "profit": state["profit"],
        "recent_trades": state["recent_trades"]
    })

@app.route("/api/update-parameters", methods=["POST"])
def update_parameters():
    body = request.get_json()
    state["parameters"].update(body)
    return jsonify({"success": True, "parameters": state["parameters"]})

# Main execution
if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(monitor_pump_fun()), daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
