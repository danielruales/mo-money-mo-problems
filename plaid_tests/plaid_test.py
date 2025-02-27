#!/usr/bin/env python3
"""
Plaid API Test Script

This script demonstrates how to use the Plaid API to fetch a list of financial institutions.
"""

# Import necessary Plaid libraries
import plaid
from plaid.api import plaid_api
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from dotenv import load_dotenv
import os
import ssl  # Add this import
load_dotenv()

# Add this line to disable SSL verification (only for development)
ssl._create_default_https_context = ssl._create_unverified_context

def get_client():
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox,  # or plaid.Environment.Production for live environment
        api_key={
            'clientId': os.getenv('PLAID_CLIENT_ID'),
            'secret': os.getenv('PLAID_SANDBOX_API_KEY'),
            'plaidVersion': '2020-09-14'
        }
    )
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    return client

def main(client):
    # Define pagination parameters
    count = 10  # Number of institutions to retrieve
    offset = 0  # Starting point for pagination

    # Create the request
    request = InstitutionsGetRequest(
        country_codes=[CountryCode('US')],
        count=count,
        offset=offset
    )
    
    try:
        # Make the API call
        response = client.institutions_get(request)
        institutions = response['institutions']
        
        # Display the results
        print(f"Retrieved {len(institutions)} institutions")
        for i, institution in enumerate(institutions):
            print(f"{i+1}. {institution.name} (ID: {institution.institution_id})")
        return institutions
    
    except plaid.ApiException as e:
        error_response = plaid.ApiException(e).body
        print(f"Error: {error_response}")
        return None

def get_chase_bank_details(client):
    """
    Retrieves detailed information about Chase Bank from Plaid API.
    
    Args:
        client: An initialized Plaid API client
        
    Returns:
        dict: Complete response data for Chase Bank or None if not found
    """
    from plaid.model.institutions_search_request import InstitutionsSearchRequest
    from plaid.model.country_code import CountryCode
    from plaid.model.products import Products
    
    try:
        # Search for Chase Bank
        search_request = InstitutionsSearchRequest(
            query="Chase",
            country_codes=[CountryCode('US')],
            # Include all available products to get complete information
            products=[
                Products('transactions'),
                Products('auth'),
                Products('identity'),
                Products('investments'),
                Products('liabilities')
            ]
        )
        
        search_response = client.institutions_search(search_request)
        institutions = search_response['institutions']
        
        # Find Chase among the results (it might not be the first result)
        chase_bank = None
        for institution in institutions:
            # Chase Bank's official name in Plaid is "Chase"
            if institution.name == "Chase":
                chase_bank = institution
                break
        
        if not chase_bank:
            print("Chase Bank not found in search results")
            return None
            
        # Get more detailed information using the institution_id
        from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
        
        detail_request = InstitutionsGetByIdRequest(
            institution_id=chase_bank.institution_id,
            country_codes=[CountryCode('US')],
            options={
                "include_optional_metadata": True,
                "include_status": True,
                "include_auth_metadata": True,
                "include_payment_initiation_metadata": True
            }
        )
        
        detail_response = client.institutions_get_by_id(detail_request)
        
        # Print some basic information
        institution = detail_response['institution']
        print(f"Name: {institution.name}")
        print(f"Institution ID: {institution.institution_id}")
        print(f"Products supported: {institution.products}")
        print(f"URL: {institution.url}")
        print(f"Primary color: {institution.primary_color}")
        print(f"Logo: {institution.logo}")
        
        # Return the full response for further processing
        return detail_response
        
    except Exception as e:
        print(f"Error retrieving Chase Bank details: {str(e)}")
        return None

if __name__ == "__main__":
    client = get_client()
    institutions = main(client) 
    chase_details = get_chase_bank_details(client)