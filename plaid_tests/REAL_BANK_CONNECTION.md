# Connecting to Real Bank Accounts with Plaid

This guide explains how to move from the Plaid Sandbox environment to Development or Production to connect to your real bank accounts.

## 1. Understanding Plaid Environments

Plaid offers three environments:

1. **Sandbox** 
   - For testing with fake data
   - Simulated bank responses
   - No connection to real financial institutions
   - Free to use

2. **Development**
   - Connect to real financial institutions
   - Access to real account data
   - Limited to 100 live items (connections)
   - Good for building and testing your app

3. **Production**
   - Full access to all Plaid products and features
   - Unlimited connections
   - Requires approval from Plaid
   - Requires a paid plan

## 2. Getting Development/Production Access

To move from Sandbox to Development or Production:

1. Log in to your [Plaid Dashboard](https://dashboard.plaid.com/)
2. For Development: This should be available immediately 
3. For Production:
   - Complete the application form in the dashboard
   - Provide details about your application and use case
   - Pass Plaid's security review
   - Sign contracts for pricing

## 3. Setting Up Your Environment

### Create or Update Your `.env` File

```
# Plaid API credentials
PLAID_CLIENT_ID=your_client_id_here

# Choose the appropriate API key
PLAID_DEVELOPMENT_API_KEY=your_development_key_here  # For connecting to real banks in test mode

# Set the environment to development
PLAID_ENV=development

# Enable OAuth (required for many real banks)
ENABLE_OAUTH=true

# Configure the redirect URI
PLAID_REDIRECT_URI=http://localhost:5000/oauth-callback
```

### Configure Redirect URIs

For real banks that use OAuth (like Chase, Wells Fargo, etc.):

1. In your Plaid Dashboard, go to **Team Settings** > **API**
2. Add `http://localhost:5000/oauth-callback` under "Allowed redirect URIs"
3. For production, you'll need to use a real domain with HTTPS

## 4. Running the Application

The core process is the same as in sandbox:

1. Run the Flask app:
   ```bash
   python plaid_connect_account.py
   ```

2. Open `http://localhost:5000` in your browser
3. Click "Connect Your Bank"
4. Select your actual bank
5. Log in with your real bank credentials
6. Complete any multi-factor authentication (MFA) if required

## 5. Important Considerations for Real Banks

### Security

When connecting to real bank accounts:

1. **Never store bank credentials** - Plaid handles this securely
2. **Store access tokens securely** - Encrypt sensitive data
3. **Use HTTPS in production** - Never use plain HTTP
4. **Implement proper error handling** - Banks may be temporarily unavailable

### User Experience

1. **Multi-factor Authentication (MFA)** - Many banks require additional verification
2. **OAuth Flows** - Some banks will redirect users to their own website
3. **Longer Processing Times** - Real banks may take longer to provide data

### Data Refresh

Transaction data needs to be refreshed periodically:

1. **Implement webhooks** - Get notified when new transactions are available
2. **Schedule regular updates** - Refresh data daily or weekly
3. **Handle stale connections** - Re-authenticate when connections expire

## 6. Code Changes

The existing code in `plaid_connect_account.py` and `plaid_test_complete.py` already supports switching environments. The main changes needed are:

1. Update your `.env` file with Development/Production credentials
2. Set `PLAID_ENV=development` (or `production`)
3. Set `ENABLE_OAUTH=true`
4. Configure webhook handling for production use

## 7. Webhooks for Production Use

For a production application, implement webhooks to receive notifications:

1. Add a webhook URL to your `.env` file:
   ```
   PLAID_WEBHOOK_URL=https://your-domain.com/webhook
   ```

2. Add the webhook URL to your link token configuration:
   ```python
   # In the create_link_token function:
   webhook = os.getenv("PLAID_WEBHOOK_URL")
   if webhook:
       config["webhook"] = webhook
   ```

3. Create a route to handle webhook notifications:
   ```python
   @app.route('/webhook', methods=['POST'])
   def webhook():
       # Verify webhook is from Plaid
       # Parse the webhook data
       # Update your database
       return '', 200
   ```

## 8. Production Best Practices

1. **Store access tokens in a database** - Not in session cookies
2. **Implement proper error handling** - Banking data can be unavailable
3. **Add rate limiting** - To avoid hitting Plaid API limits
4. **Implement logging** - Track API calls and errors
5. **Monitor your usage** - Watch for unexpected API calls 