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

@app.route("/create_account", methods=["POST"])
@jwt_required() 
def create_account():
    global next_id

    data = request.get_json()
    name = data.get("name")
    initial_balance = data.get("initial_balance", 0)

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not isinstance(initial_balance, (int, float)) or initial_balance < 0:
        return jsonify({"error": "Initial balance must be a non-negative number"}), 400

    account_id = next_id
    accounts[account_id] = {
        "id": account_id,
        "name": name,
        "balance": float(initial_balance)
    }
    next_id += 1

    return jsonify(accounts[account_id]), 201

@app.route("/deposit", methods=["POST"])
@jwt_required() 
def deposit():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")

    if account_id not in accounts:
        return jsonify({"error": "Account not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Deposit amount must be positive"}), 400

    accounts[account_id]["balance"] += float(amount)
    return jsonify(accounts[account_id]), 200

@app.route("/withdraw", methods=["POST"])
@jwt_required() 
def withdraw():
    data = request.get_json()
    account_id = data.get("account_id")
    amount = data.get("amount")

    if account_id not in accounts:
        return jsonify({"error": "Account not found"}), 404
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Withdraw amount must be positive"}), 400

    if accounts[account_id]["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    accounts[account_id]["balance"] -= float(amount)
    return jsonify(accounts[account_id]), 200

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