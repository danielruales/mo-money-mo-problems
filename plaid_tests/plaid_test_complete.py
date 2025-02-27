import os
import plaid
from plaid import plaid_api

def get_client():
    """
    Returns a configured Plaid API client based on the environment settings in .env file.
    """
    # Get the environment setting
    plaid_env = os.getenv('PLAID_ENV', 'sandbox').lower()
    
    # Set the appropriate host based on environment
    if plaid_env == 'production':
        host = plaid.Environment.Production
        api_key = os.getenv('PLAID_PRODUCTION_API_KEY')
    elif plaid_env == 'development':
        host = plaid.Environment.Development
        api_key = os.getenv('PLAID_DEVELOPMENT_API_KEY')
    else:  # Default to sandbox
        host = plaid.Environment.Sandbox
        api_key = os.getenv('PLAID_SANDBOX_API_KEY')
    
    # Check if API key exists
    if not api_key:
        raise ValueError(f"No API key found for {plaid_env} environment. Check your .env file.")
    
    # Configure the client
    configuration = plaid.Configuration(
        host=host,
        api_key={
            'clientId': os.getenv('PLAID_CLIENT_ID'),
            'secret': api_key,
            'plaidVersion': '2020-09-14'
        }
    )
    
    # Log which environment we're using
    print(f"Initializing Plaid client in {plaid_env.upper()} environment")
    
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    return client 