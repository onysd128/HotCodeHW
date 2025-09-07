from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_basicauth import BasicAuth
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
basic_auth = BasicAuth(app)

app.config['BASIC_AUTH_USERNAME'] = os.environ.get("BASIC_AUTH_USERNAME","XXX")
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get("BASIC_AUTH_PASSWORD","XXX")


app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY","XXX")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours= int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS",1)))
jwt = JWTManager(app)

@app.route("/login", methods=["POST"])
@basic_auth.required
def login():
    access_token = create_access_token(identity="admin")
    return jsonify(access_token=access_token), 200

accounts = {}
next_id = 1

CURRENCY_RATES = {
    "USD": 1,
    "EUR": 0.85,
    "UAH": 41.24
}

def convert(amount, from_currency, to_currency):
    if from_currency not in CURRENCY_RATES or to_currency not in CURRENCY_RATES:
        raise ValueError("Unsupported currency")
    amount_in_usd = amount/CURRENCY_RATES[from_currency]
    return amount_in_usd * CURRENCY_RATES[to_currency]

@app.route("/create_account", methods=["POST"])
@jwt_required() 
def create_account():
    global next_id

    data = request.get_json()
    name = data.get("name")
    # initial_balance = data.get("initial_balance", 0)
    balances = data.get("balances", {"USD": 0,"EUR":0,"UAH":0})

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not isinstance(balances, dict) or not balances:
        return jsonify({"error": "Balances must be a dict"}), 400
    
    for cur, amount in balances.items():
        if cur not in CURRENCY_RATES:
            return jsonify({"error":f"Unsupported currency {cur}"}), 400
        if not isinstance(amount, (int,float)) or amount<0:
            return jsonify({"error": f"Invalid balance for {cur}"}), 400

    account_id = next_id
    accounts[account_id] = {
        "id": account_id,
        "name": name,
        "balances": {cur: float(amount) for cur, amount in balances.items()}
    }
    next_id += 1

    return jsonify(accounts[account_id]), 201

@app.route("/deposit", methods=["POST"])
@jwt_required() 
def deposit():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")
    currency = data.get("currency")

    if account_id not in accounts:
        return jsonify({"error": "Account not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Deposit amount must be positive"}), 400
    if currency not in CURRENCY_RATES:
        return jsonify({"error": f"Unsupported currency {currency}"}), 400

    account = accounts[account_id]
    account["balances"][currency] = account["balances"].get(currency, 0) + float(amount)
    return jsonify(account), 200

@app.route("/withdraw", methods=["POST"])
@jwt_required() 
def withdraw():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")
    currency = data.get("currency")

    if account_id not in accounts:
        return jsonify({"error": "Account not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Withdraw amount must be positive"}), 400
    if currency not in CURRENCY_RATES:
        return jsonify({"error": f"Unsupported currency {currency}"}), 400

    account = accounts[account_id]
    if account["balances"].get(currency, 0)<amount:
        return jsonify({"error": "Insufficient funds"}), 400

    account["balances"][currency] = account["balances"].get(currency, 0) - float(amount)
    return jsonify(account), 200

@app.route("/transfer", methods=["POST"])
@jwt_required() 
def transfer():
    data = request.get_json()
    from_id = data.get("from_account_id")
    to_id = data.get("to_account_id")
    amount = data.get("amount")

    if from_id not in accounts or to_id not in accounts:
        return jsonify({"error": "One or both accounts not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Transfer amount must be positive"}), 400
    if accounts[from_id]["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    accounts[from_id]["balance"] -= float(amount)
    accounts[to_id]["balance"] += float(amount)

    return jsonify({
        "from_account": accounts[from_id],
        "to_account": accounts[to_id]
    }), 200

if __name__ == "__main__":
    app.run(debug=True)