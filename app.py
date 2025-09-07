from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_basicauth import BasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime
from dotenv import load_dotenv
import os
import logging

load_dotenv()

app = Flask(__name__)
basic_auth = BasicAuth(app)

def get_jwt_user():
    try:
        return get_jwt_identity()  
    except Exception as e:
        return get_remote_address()

limiter = Limiter(key_func = get_jwt_user, app=app, default_limits = ["60 per minute","2 per second"])

app.config['BASIC_AUTH_USERNAME'] = os.environ.get("BASIC_AUTH_USERNAME","XXX")
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get("BASIC_AUTH_PASSWORD","XXX")


app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY","XXX")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours= int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS",1)))
jwt = JWTManager(app)

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

transactions_log = []

def log_transaction(tx_type, account_id=None, amount=None, currency=None, 
                    from_id=None, to_id=None, status="success", error=None):
    record = {
        "type": tx_type,
        "account_id": account_id,
        "from_id": from_id,
        "to_id": to_id,
        "amount": amount,
        "currency": currency,
        "status": status,
        "error": error,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    transactions_log.append(record)
    logging.info(str(record))

@app.route("/login", methods=["POST"])
@basic_auth.required
@limiter.limit("5 per minute")
def login():
    access_token = create_access_token(identity="admin")
    return jsonify(access_token=access_token), 200

@app.route("/create_account", methods=["POST"])
@jwt_required() 
def create_account():
    global next_id

    data = request.get_json()
    name = data.get("name")
    balances = data.get("balances", {"USD": 0,"EUR":0,"UAH":0})

    if not name:
        log_transaction("create_account", status="failed", error="Name is required")
        return jsonify({"error": "Name is required"}), 400
    if not isinstance(balances, dict) or not balances:
        log_transaction("create_account", status="failed", error="Balances must be a dict")
        return jsonify({"error": "Balances must be a dict"}), 400
    
    for cur, amount in balances.items():
        if cur not in CURRENCY_RATES:
            log_transaction("create_account", status="failed", error=f"Unsupported currency {cur}")
            return jsonify({"error":f"Unsupported currency {cur}"}), 400
        if not isinstance(amount, (int,float)) or amount<0:
            log_transaction("create_account", status="failed", error=f"Invalid balance for {cur}")
            return jsonify({"error": f"Invalid balance for {cur}"}), 400

    account_id = next_id
    accounts[account_id] = {
        "id": account_id,
        "name": name,
        "balances": {cur: float(amount) for cur, amount in balances.items()}
    }
    next_id += 1

    log_transaction("create_account", account_id=account_id, status="success")
    return jsonify(accounts[account_id]), 201

@app.route("/deposit", methods=["POST"])
@jwt_required() 
def deposit():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")
    currency = data.get("currency")

    if account_id not in accounts:
        log_transaction("deposit", account_id, amount, currency, status="failed", error="Account not found")
        return jsonify({"error": "Account not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        log_transaction("deposit", account_id, amount, currency, status="failed", error="Invalid amount")
        return jsonify({"error": "Deposit amount must be positive"}), 400
    if currency not in CURRENCY_RATES:
        log_transaction("deposit", account_id, amount, currency, status="failed", error="Unsupported currency")
        return jsonify({"error": f"Unsupported currency {currency}"}), 400

    account = accounts[account_id]
    account["balances"][currency] = account["balances"].get(currency, 0) + float(amount)
    log_transaction("deposit", account_id, amount, currency, status="success")
    return jsonify(account), 200

@app.route("/withdraw", methods=["POST"])
@jwt_required() 
def withdraw():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")
    currency = data.get("currency")

    if account_id not in accounts:
        log_transaction("withdraw", account_id, amount, currency, status="failed", error="Account not found")
        return jsonify({"error": "Account not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        log_transaction("withdraw", account_id, amount, currency, status="failed", error="Invalid amount")
        return jsonify({"error": "Withdraw amount must be positive"}), 400
    if currency not in CURRENCY_RATES:
        log_transaction("withdraw", account_id, amount, currency, status="failed", error="Unsupported currency")
        return jsonify({"error": f"Unsupported currency {currency}"}), 400

    account = accounts[account_id]
    if account["balances"].get(currency, 0)<amount:
        log_transaction("withdraw", account_id, amount, currency, status="failed", error="Insufficient funds")
        return jsonify({"error": "Insufficient funds"}), 400

    account["balances"][currency] = account["balances"].get(currency, 0) - float(amount)
    log_transaction("withdraw", account_id, amount, currency, status="success")
    return jsonify(account), 200

@app.route("/transfer", methods=["POST"])
@jwt_required() 
def transfer():
    data = request.get_json()
    from_id = data.get("from_account_id")
    to_id = data.get("to_account_id")
    amount = data.get("amount")
    currency = data.get("currency")

    if from_id not in accounts or to_id not in accounts:
        log_transaction("transfer", from_id, amount, currency, to_id=to_id, status="failed", error="Account not found")
        return jsonify({"error": "One or both accounts not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        log_transaction("transfer", from_id, amount, currency, to_id=to_id, status="failed", error="Invalid amount")
        return jsonify({"error": "Transfer amount must be positive"}), 400
    if currency not in CURRENCY_RATES:
        log_transaction("transfer", from_id, amount, currency, to_id=to_id, status="failed", error="Unsupported currency")
        return jsonify({"error": f"Unsupported currency {currency}"}), 400
    
    from_account = accounts[from_id]
    to_account = accounts[to_id]

    if from_account["balances"].get(currency, 0)<amount:
        log_transaction("transfer", from_id, amount, currency, to_id=to_id, status="failed", error="Insufficient funds")
        return jsonify({"error": "Insufficient funds"}), 400
    
    from_account["balances"][currency] -= float(amount)
    to_account["balances"][currency] += float(amount)

    log_transaction("transfer", from_id, amount, currency, to_id=to_id, status="success")
    return jsonify({
        "from_account": from_account,
        "to_account": to_account
    }), 200

@app.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    return jsonify(transactions_log), 200

@app.route("/accounts", methods=["GET"])
@app.route("/accounts/<int:account_id>", methods=["GET"])
@jwt_required()
def get_accounts(account_id=None):
    if account_id is None:
        log_transaction("get_accounts", status="success")
        return jsonify(list(accounts.values())), 200
    else:
        if account_id not in accounts:
            log_transaction("get_accounts", account_id=account_id,
                            status="failed", error="Account not found")
            return jsonify({"error": "Account not found"}), 404
        log_transaction("get_accounts", account_id=account_id, status="success")
        return jsonify(accounts[account_id]), 200

if __name__ == "__main__":
    app.run(debug=True)