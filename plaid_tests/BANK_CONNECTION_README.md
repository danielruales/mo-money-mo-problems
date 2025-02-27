# Connecting to Your Bank Account with Plaid

This guide explains how to connect to your bank account and retrieve transaction data using the Plaid API.

## Prerequisites

- Plaid API credentials (Client ID and Secret)
- Python 3.6 or higher
- Required packages: `plaid-python`, `flask`, `python-dotenv`

## Setup

1. Install the required packages:
   ```bash
   pip install plaid-python flask python-dotenv
   ```

2. Create a `.env` file with your Plaid credentials:
   ```
   PLAID_CLIENT_ID=your_client_id_here
   PLAID_SANDBOX_API_KEY=your_sandbox_key_here
   PLAID_ENV=sandbox
   # Optional for OAuth
   PLAID_REDIRECT_URI=http://localhost:8000/oauth-callback
   ```

3. Get your Plaid credentials:
   - Sign up at [https://dashboard.plaid.com/signup](https://dashboard.plaid.com/signup)
   - Create a new project
   - Navigate to the "Keys" section to find your Client ID and Secret

## Running the Application

1. Start the Flask web server:
   ```bash
   python plaid_connect_account.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Click the "Connect Your Bank" button

4. Follow the Plaid Link flow:
   - Select your bank
   - Sign in with your bank credentials
   - Authorize access to your account data

5. After successful connection, you'll be redirected to a page showing your account information and transactions.

## How it Works

The application follows these steps:

1. **Create a Link Token**: This initializes the Plaid Link flow
2. **User Authentication**: You log in to your bank through Plaid's secure interface
3. **Exchange Public Token**: The app exchanges the temporary public token for a permanent access token
4. **Retrieve Data**: The app uses the access token to fetch your account and transaction data

## Sandbox Testing

In sandbox mode, you can use the following credentials for testing:
- Username: `user_good`
- Password: `pass_good`

## Using in Your Own Application

If you want to use this in your own code instead of the Flask app:

1. You still need to go through the Link flow to get an access token (requires a web interface)
2. Once you have an access token, you can use it in a script to fetch transactions:

```python
from plaid_test_complete import get_client
import datetime
from plaid.model.transactions_get_request import TransactionsGetRequest

# Initialize client
client = get_client()

# Use your stored access token
access_token = "your_access_token"  # Store this securely after obtaining it

# Define date range
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)

# Create request
request = TransactionsGetRequest(
    access_token=access_token,
    start_date=start_date,
    end_date=end_date
)

# Get transactions
response = client.transactions_get(request)
transactions = response['transactions']

# Process transactions
for transaction in transactions:
    print(f"{transaction.date}: {transaction.name} - ${transaction.amount}")
```

## Important Security Notes

- Never expose your Plaid secret in client-side code
- Store access tokens securely (e.g., in a database with encryption)
- Use HTTPS in production
- Consider implementing token refresh mechanisms for long-term access

## Troubleshooting Common Errors

### OAuth Redirect URI Error

If you see an error like:
```
Error creating link token: Status Code: 400 Reason: Bad Request
Error message: "OAuth redirect URI must be configured in the developer dashboard."
```

This means you're trying to use OAuth features without configuring the redirect URI. You have two options:

1. **Option 1: Remove the redirect URI** (Simplest solution)
   - Edit the `plaid_connect_account.py` file
   - Remove the `redirect_uri` parameter from the `LinkTokenCreateRequest`
   - This works for most banks in Sandbox mode

2. **Option 2: Configure the redirect URI** (Required for OAuth-based institutions)
   - Go to your [Plaid Dashboard](https://dashboard.plaid.com/)
   - Navigate to Team Settings > API
   - Add `http://localhost:5000/oauth-callback` under "Allowed redirect URIs"
   - This is required for institutions like Chase, Wells Fargo, etc.

### API Keys Error

If you're getting authentication errors, make sure your `.env` file contains valid Plaid API credentials:
- Check that you're using the right environment (sandbox, development, or production)
- Verify your Client ID and Secret are correct
- Ensure you're using the right API key for the environment you specified 

### PRODUCT_NOT_READY Error

If you see this error:
```
Error retrieving transactions: Status Code: 400 Reason: Bad Request
Error code: "PRODUCT_NOT_READY"
Error message: "the requested product is not yet ready..."
```

This means Plaid needs time to prepare your transaction data. This is normal, especially in the Sandbox environment:

1. **Solution 1: Wait and refresh** (Our app now handles this with a nice UI)
   - The transaction data isn't immediately available after linking an account
   - Wait a few moments and try refreshing the page

2. **Solution 2: Implement webhooks** (For production apps)
   - In a real application, you should implement webhooks
   - Plaid will call your webhook when the data is ready: [Plaid Webhooks Guide](https://plaid.com/docs/api/webhooks/)
   - Add a `webhook` parameter to your `LinkTokenCreateRequest` with your webhook URL

3. **Sandbox testing note:**
   - In Sandbox mode, transaction data is simulated
   - Sometimes it's available immediately, sometimes it takes time
   - If it doesn't appear after multiple attempts, try reconnecting the account 