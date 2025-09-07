from flask import Flask, request, jsonify

app = Flask(__name__)

accounts = {}
next_id = 1        

@app.route("/create_account", methods=["POST"])
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

if __name__ == "__main__":
    app.run(debug=True)