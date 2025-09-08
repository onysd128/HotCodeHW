# HotCode HW

This project is a simple **banking API** built with Flask featuring:
- JWT authentication
- BasicAuth for login
- Rate limiting (Flask-Limiter)
- Multi-currency account balances
- Operations: account creation, deposit, withdrawal, transfer
- Transaction logging
- Endpoints for viewing transactions and accounts

I also added postman collection file to the repo (HotcodeHW.postman_collection.json), so you can import it into postman and test this api in more user-frindly way!

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/onysd128/HotCodeHW.git
cd HotCodeHW
```

### 2. Create virtual environment and install dependencies
```
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

### 3. Configure environment variables
Create a .env file in the project root:
```
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=admin
JWT_SECRET_KEY=my-secret-key
JWT_ACCESS_TOKEN_EXPIRES_HOURS=1
```

### 4. Run the server
```
python app.py
```

The API will start at http://127.0.0.1:5000.

## API Endpoints

### Login
```
POST /login
Auth: Basic (username & password from .env)
```

Response:
```
{ "access_token": "XXX" }
```

### Create Account
```
POST /create_account
Headers: Authorization: Bearer <token>
Body (JSON):
{
  "name": "Alice",
  "balances": { "USD": 100, "EUR": 50 }
}
```

Response:
```
{
    "balances": {
        "EUR": 50.0,
        "USD": 100.0
    },
    "id": 1,
    "name": "Alice"
}
```

### Deposit
```
POST /deposit
Headers: Authorization: Bearer <token>
Body:
{
  "account_id": 1,
  "amount": 100,
  "currency": "USD"
}
```

Response:
```
{
    "balances": {
        "EUR": 50.0,
        "USD": 200.0
    },
    "id": 1,
    "name": "Alice"
}
```

### Withdraw
```
POST /withdraw
Headers: Authorization: Bearer <token>
Body:
{
  "account_id": 1,
  "amount": 50,
  "currency": "USD"
}
```

Response:
```
{
    "balances": {
        "EUR": 50.0,
        "USD": 150.0
    },
    "id": 1,
    "name": "Alice"
}
```

### Transfer
```
POST /transfer
Headers: Authorization: Bearer <token>
Body:
{
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": 10,
  "currency": "EUR"
}
```

Response:
```
{
    "from_account": {
        "balances": {
            "EUR": 40.0,
            "USD": 150.0
        },
        "id": 1,
        "name": "Alice"
    },
    "to_account": {
        "balances": {
            "EUR": 60.0,
            "USD": 100.0
        },
        "id": 2,
        "name": "Brandon"
    }
}
```

### Transactions
```
GET /transactions
Headers: Authorization: Bearer <token>
```

Response:
```
[
    {
        "account_id": 1,
        "amount": null,
        "currency": null,
        "error": null,
        "from_id": null,
        "status": "success",
        "timestamp": "2025-09-08T10:07:31.581792",
        "to_id": null,
        "type": "create_account"
    },
    {
        "account_id": 1,
        "amount": 100,
        "currency": "USD",
        "error": null,
        "from_id": null,
        "status": "success",
        "timestamp": "2025-09-08T10:09:25.779552",
        "to_id": null,
        "type": "deposit"
    },
    {
        "account_id": 1,
        "amount": 50,
        "currency": "USD",
        "error": null,
        "from_id": null,
        "status": "success",
        "timestamp": "2025-09-08T10:10:31.603714",
        "to_id": null,
        "type": "withdraw"
    },
    {
        "account_id": 2,
        "amount": null,
        "currency": null,
        "error": null,
        "from_id": null,
        "status": "success",
        "timestamp": "2025-09-08T10:11:49.384010",
        "to_id": null,
        "type": "create_account"
    },
    {
        "account_id": 1,
        "amount": 10,
        "currency": "EUR",
        "error": null,
        "from_id": null,
        "status": "success",
        "timestamp": "2025-09-08T10:12:02.194163",
        "to_id": 2,
        "type": "transfer"
    }
]
```

### Accounts
Get all accounts:
```
GET /accounts
Headers: Authorization: Bearer <token>
```

Response:
```
[
    {
        "balances": {
            "EUR": 40.0,
            "USD": 150.0
        },
        "id": 1,
        "name": "Alice"
    },
    {
        "balances": {
            "EUR": 60.0,
            "USD": 100.0
        },
        "id": 2,
        "name": "Brandon"
    }
]
```

Get account by id
```
GET /accounts/1
Headers: Authorization: Bearer <token>
```

Response:
```
{
    "balances": {
        "EUR": 40.0,
        "USD": 150.0
    },
    "id": 1,
    "name": "Alice"
}
```