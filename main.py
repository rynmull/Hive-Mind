
import asyncio
import json
import websockets
import requests
import os
from flask import Flask, send_from_directory, jsonify, request
import threading
from datetime import datetime, timedelta

# Access environment variables
private_key = os.getenv("PRIVATE_KEY")
rpc_endpoint = os.getenv("RPC_ENDPOINT")

# Constants for WebSocket and API
PUMP_WS_URL = "wss://pumpportal.fun/api/data"
TRADE_API_URL = "https://pumpportal.fun/api/trade-local"

# Adaptive parameters (initial values)
adaptive_parameters = {
    "trending_threshold": 5,  # Buys in 30 seconds
    "profit_take_percentage": 20,
    "loss_cut_percentage": 10,
    "time_window": 30  # Seconds
}

# Persistent state
state = {
    "parameters": adaptive_parameters,
    "profit": 0,
    "recent_trades": [],
    "current_token": None,
    "buy_price": None
}

# File for saving state
STATE_FILE = "trading_state.json"

# Load state from file if it exists
def load_state():
    try:
        with open(STATE_FILE, "r") as file:
            global state
            state.update(json.load(file))
    except FileNotFoundError:
        pass

# Save state to file
def save_state():
    with open(STATE_FILE, "w") as file:
        json.dump(state, file)

# WebSocket handler
async def monitor_trending_tokens():
    async with websockets.connect(PUMP_WS_URL) as websocket:
        # Subscribe to updates
        await websocket.send(json.dumps({"action": "subscribeNewToken"}))
        await websocket.send(json.dumps({"action": "subscribeTokenTrade"}))

        print("Subscribed to PumpPortal WebSocket.")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                process_message(data)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed. Reconnecting...")
                await asyncio.sleep(5)
                await monitor_trending_tokens()

# Process incoming WebSocket messages
def process_message(data):
    if "newToken" in data:
        print("New Token Detected:", data["newToken"])
    elif "tokenTrade" in data:
        analyze_trade(data["tokenTrade"])

# Analyze trades to detect trends
def analyze_trade(trade):
    token = trade["mint"]
    buys = trade["buys"]
    price = float(trade["price"])

    if buys >= state["parameters"]["trending_threshold"]:
        print(f"Trending token detected: {token} with {buys} buys.")
        if not state["current_token"]:
            execute_trade("buy", token, price)

# Execute trade actions
def execute_trade(action, token, price):
    if action == "buy":
        state["current_token"] = token
        state["buy_price"] = price
        state["recent_trades"].append({"action": "buy", "token": token, "price": price, "time": str(datetime.now())})
        print(f"Bought {token} at {price} SOL.")
    elif action == "sell":
        profit = (price - state["buy_price"]) * 0.1  # Assuming 0.1 SOL quantity
        state["profit"] += profit
        state["recent_trades"].append({"action": "sell", "token": token, "price": price, "profit": profit, "time": str(datetime.now())})
        state["current_token"] = None
        state["buy_price"] = None
        print(f"Sold {token} at {price} SOL. Profit: {profit} SOL.")

    save_state()

# Check trading conditions and execute sell if conditions met
def check_trading_conditions():
    if state["current_token"] and state["buy_price"]:
        current_price = get_current_price(state["current_token"])

        if current_price >= state["buy_price"] * (1 + state["parameters"]["profit_take_percentage"] / 100):
            execute_trade("sell", state["current_token"], current_price)
        elif current_price <= state["buy_price"] * (1 - state["parameters"]["loss_cut_percentage"] / 100):
            execute_trade("sell", state["current_token"], current_price)

# Fetch current price of a token
def get_current_price(token):
    # Placeholder for API call or WebSocket message processing
    return state["buy_price"] * 1.2  # Mock price movement

# Flask Web Server
app = Flask(__name__)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

@app.route("/api/start-trading", methods=["POST"])
def start_trading():
    body = request.get_json()
    trade_amount = body.get("amount", 0.1)  # Default to 0.1 SOL

    print(f"Start trading request received. Trade amount: {trade_amount}")  # Debug log

    return jsonify({
        "success": True,
        "token": state.get("current_token", "None"),
        "profit": float(state.get("profit", 0)),
        "totalProfit": float(state.get("profit", 0)),
        "recentTrades": state["recent_trades"]
    })


@app.route("/api/stop-trading", methods=["POST"])
def stop_trading():
    return jsonify({
        "success": True,
        "message": "Trading stopped successfully",
        "recentTrades": state["recent_trades"]
    })

@app.route("/api/update-parameters", methods=["POST"])
def update_parameters():
    body = request.get_json()
    state["parameters"]["trending_threshold"] = body.get("trending_threshold", state["parameters"]["trending_threshold"])
    state["parameters"]["profit_take_percentage"] = body.get("profit_take_percentage", state["parameters"]["profit_take_percentage"])
    state["parameters"]["loss_cut_percentage"] = body.get("loss_cut_percentage", state["parameters"]["loss_cut_percentage"])
    save_state()
    return jsonify({"success": True, "parameters": state["parameters"]})

@app.route("/api/get-balance", methods=["GET"])
def get_balance():
    # Replace with actual RPC call
    balance = 10  # Mocked balance
    return jsonify({"balance": balance})

# Start the trading bot in a separate thread
def start_trading_bot():
    asyncio.run(main())

if __name__ == "__main__":
    # Start the bot in a new thread
    bot_thread = threading.Thread(target=start_trading_bot, daemon=True)
    bot_thread.start()

    # Run the Flask web server
    app.run(host="0.0.0.0", port=8080)
