#!/usr/bin/env python3
"""
Plaid Bank Account Connection Script

This script demonstrates how to:
1. Create a link token for authentication
2. Exchange the public token for an access token
3. Retrieve account information
4. Fetch transaction data

Note: This script includes a simple Flask web server to handle the OAuth flow
"""

import os
import json
import datetime
import plaid
from plaid.api import plaid_api
from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

# Import the client creation function from your existing code
from plaid_test_complete import get_client

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random secret key for session

# Initialize Plaid client
client = get_client()

# Configuration for OAuth (can be enabled or disabled)
ENABLE_OAUTH = os.getenv('ENABLE_OAUTH', 'false').lower() == 'true'
print(f"OAuth support is {'enabled' if ENABLE_OAUTH else 'disabled'}")

@app.route('/') 

@app.route('/create_link_token')
def create_link_token():
    """
    Create a link token and redirect to the link page
    """
    try:
        # Create link token configuration
        config = {
            "user": LinkTokenCreateRequestUser(
                client_user_id=f"user-id-{str(datetime.datetime.now().timestamp())[0:10]}"
            ),
            "client_name": "My App",
            "products": [Products("transactions")],
            "country_codes": [CountryCode("US")],
            "language": "en"
        }
        
        # Add redirect_uri if OAuth is enabled
        if ENABLE_OAUTH:
            redirect_uri = os.getenv("PLAID_REDIRECT_URI") or "http://localhost:5000/oauth-callback"
            config["redirect_uri"] = redirect_uri
            print(f"OAuth is enabled. Using redirect URI: {redirect_uri}")
        
        # Add webhook URL if provided (important for production use)
        webhook_url = os.getenv("PLAID_WEBHOOK_URL")
        if webhook_url:
            config["webhook"] = webhook_url
            print(f"Using webhook URL: {webhook_url}")
        
        # Create the request with appropriate configuration
        request = LinkTokenCreateRequest(**config)
        
        response = client.link_token_create(request)
        link_token = response['link_token']
        
        # Store the link token in the session
        session['link_token'] = link_token
        
        # Redirect to the link page
        return redirect(url_for('link_page'))
    
    except Exception as e:
        return f"Error creating link token: {str(e)}"

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Handle webhooks from Plaid
    
    In a production application, this would:
    1. Verify the webhook is from Plaid
    2. Process different webhook types (transactions updates, etc.)
    3. Update your database with new data
    
    Webhook documentation: https://plaid.com/docs/api/webhooks/
    """
    try:
        # Get the webhook data as JSON
        webhook_data = request.get_json()
        
        if not webhook_data:
            return "No webhook data received", 400
            
        # Log the webhook
        webhook_type = webhook_data.get('webhook_type', 'UNKNOWN')
        webhook_code = webhook_data.get('webhook_code', 'UNKNOWN')
        item_id = webhook_data.get('item_id', 'UNKNOWN')
        
        print(f"Received webhook: Type={webhook_type}, Code={webhook_code}, Item ID={item_id}")
        
        # Handle different webhook types
        if webhook_type == 'TRANSACTIONS':
            if webhook_code == 'INITIAL_UPDATE':
                print("Initial transactions are ready")
                # In a real app, you would pull and store the transactions
                
            elif webhook_code == 'HISTORICAL_UPDATE':
                print("Historical transactions are ready")
                # In a real app, you would pull and store the transactions
                
            elif webhook_code == 'DEFAULT_UPDATE':
                print("New transactions are available")
                # In a real app, you would pull and store the new transactions
                
        # For a production application, handle all webhook types you care about
        # See https://plaid.com/docs/api/webhooks/ for details
        
        # Return 200 OK to acknowledge receipt
        return "", 200
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return f"Error: {str(e)}", 500 