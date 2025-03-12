#!/usr/bin/env python3
"""
Transaction Enrichment Script

This script enhances the consolidated transaction data by adding sub-categories
and additional analysis fields to provide more detailed financial insights.
"""

import os
import pandas as pd
import re
from datetime import datetime
import enum
import numpy as np

class EnrichedCategory(enum.Enum):
    ACCOMODATION = 'Accomodation'
    SHOPPING = 'Shopping'
    FOOD = 'Food'
    TRANSPORTATION = 'Transportation'
    DEBT = 'Debt'
    UTILITIES = 'Utilities'
    ENTERTAINMENT = 'Entertainment'
    HEALTH = 'Health'
    INVESTMENT = 'Investment'
    PETS = 'Pets'
    EDUCATION = 'Education'
    TRAVEL = 'Travel'
    INCOME = 'Income'
    PAYMENT = 'Payment'
    TRANSFER = 'Transfer'
    UNDEFINED = 'Undefined'

def load_transactions(file_path='data/my_consolidated_transactions.csv'):
    """
    Load the consolidated transactions dataset.
    
    Args:
        file_path (str): Path to consolidated transactions CSV
        
    Returns:
        pd.DataFrame: DataFrame containing transaction data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Transaction file not found: {file_path}")
    
    return pd.read_csv(file_path, parse_dates=['transaction_date', 'post_date'])

def enrich_amount(row):
    """
    Enrich the amount of the transaction.
    """
    
    if row['source'] == 'Amex':
        return row['amount'] * -1
    else:
        return row['amount']

def is_transfer(row):
    """
    Determine if the transaction is a transfer.
    """
    if row['source'] == 'SoFi':
        if row['description'].lower().startswith('wells fargo bank'): # Transfers from SoFi to Wells Fargo
            return True
        elif row['description'].lower().startswith('to') and row['description'].lower().endswith('vault'): # Transfers from SoFi to SoFi Vault
            return True
        else:
            return False
    elif row['source'] == 'WellsFargo':
        if row['description'].lower().startswith('sofi bank transfer'): # Transfers from SoFi to Wells Fargo
            return True
        elif row['description'].lower().startswith('online transfer to'): # Internal transfers from Wells Fargo to Wells Fargo
            return True
        else:
            return False
    else:
        return False

def enrich_transaction_type(row, amount_enriched):
    """
    Enrich the transaction data with the transaction type.
    """
    if row['account_type'] == 'Credit Card':
        if amount_enriched < 0:
            return 'Charge' # Charge was made to the credit card
        elif amount_enriched > 0:
            if 'payment' in row['description'].lower():
                return 'Payment'
            else:
                return 'Refund'
        else:
            return 'Undefined'
    elif row['account_type'] == 'Checkings':
        if is_transfer(row):
            return 'Transfer'
        else:
            if amount_enriched < 0:
                if 'payment' in row['description'].lower() or 'payment' in row['category'].lower():
                    return 'Payment'
                else:
                    return 'Charge'
            elif amount_enriched > 0:
                return 'Income'
            else:
                return 'Undefined'
    else:
        return 'Undefined'

def enrich_category(row, transaction_type):
    """
    Enrich the category of the transaction.
    """
    print('--------------------------------')
    category_source = row.get('category', 'undefined')
    # Coalesce the category source with 'Undefined' if it is None
    if category_source is None or pd.isna(category_source):
        category_source = 'undefined'
    category_source = category_source.lower()

    description_source = row.get('description', 'undefined')
    # Coalesce the category source with 'Undefined' if it is None
    if description_source is None or pd.isna(description_source):
        description_source = 'undefined'
    description_source = description_source.lower()
    print(description_source)
    if transaction_type == 'Income':
        return EnrichedCategory.INCOME.value
    elif transaction_type == 'Transfer':
        return EnrichedCategory.TRANSFER.value
    elif transaction_type == 'Payment':
        return EnrichedCategory.PAYMENT.value
    elif 'restaurant' in category_source:
        return EnrichedCategory.FOOD.value
    elif 'groceries' == category_source:
        return EnrichedCategory.FOOD.value
    elif 'food' in category_source:
        return EnrichedCategory.FOOD.value
    elif 'health' in category_source:
        return EnrichedCategory.HEALTH.value
    elif 'utilities' in category_source:
        return EnrichedCategory.UTILITIES.value
    elif 'transportation' == category_source:
        return EnrichedCategory.TRANSPORTATION.value
    elif 'entertainment' == category_source:
        return EnrichedCategory.ENTERTAINMENT.value
    elif 'entertainment' in category_source:
        return EnrichedCategory.ENTERTAINMENT.value
    elif 'rent pmt' in description_source:
        return EnrichedCategory.ACCOMODATION.value
    elif 'amazon' in description_source:
        return EnrichedCategory.SHOPPING.value
    elif 'target' in description_source:
        return EnrichedCategory.FOOD.value
    elif 'costco' in description_source:
        return EnrichedCategory.FOOD.value
    elif 'apple.com/bill' in description_source:
        return EnrichedCategory.UTILITIES.value
    elif 'openai' in description_source:
        return EnrichedCategory.UTILITIES.value
    elif 'cursor' in description_source:
        return EnrichedCategory.UTILITIES.value
    elif 'uber eats' in description_source:
        return EnrichedCategory.FOOD.value
    elif description_source.startswith('lyft'):
        return EnrichedCategory.TRANSPORTATION.value
    elif description_source.startswith('uber'):
        return EnrichedCategory.TRANSPORTATION.value
    elif 'shopping' in category_source:
        return EnrichedCategory.SHOPPING.value
    elif 'education' in category_source:
        return EnrichedCategory.EDUCATION.value
    elif 'communications' in category_source:
        return EnrichedCategory.UTILITIES.value
    elif 'travel' == category_source:
        return EnrichedCategory.TRAVEL.value
    else:
        return EnrichedCategory.UNDEFINED.value
        
def enrich_subcategory(row):
    """
    Enrich the subcategory of the transaction.
    """
    return 'Undefined'

def enrich_merchant(row):
    """
    Enrich the merchant of the transaction.
    """
    return 'Undefined'

def process_transaction(row):
    """
    Process the transaction data.
    """
    amount_enriched = enrich_amount(row)
    transaction_type = enrich_transaction_type(row, amount_enriched)
    category_enriched = enrich_category(row, transaction_type) # Process with LLM in downstream process
    subcategory_enriched = enrich_subcategory(row) # Process with LLM in downstream process
    merchant = enrich_merchant(row) # Process with LLM in downstream process
    return pd.Series([amount_enriched, transaction_type, category_enriched, subcategory_enriched, merchant])

def enrich_transactions(df):
    """
    Enrich the transaction data with sub-categories and additional analysis fields.
    This function generates offline enrichment of the transaction data.
    Another process will be used for online enrichment of the transaction data to correct offline enrichment and provide new insights.
    This would include user-generated descriptions, city, country, consumed_start_date, consumed_end_date, etc.

    Args:
        df (pd.DataFrame): DataFrame containing transaction data

    Returns:
        pd.DataFrame: DataFrame containing enriched transaction data
        Schema:
            - transaction_date: datetime
                The source date of the transaction
            - post_date: datetime
                The source date the transaction was posted to the account
            - description: str
                The source description of the transaction as it appears in the transaction feed
            - amount: float
                The source amount of the transaction
            - category_source: str
                The source category of the transaction as it appears in the transaction feed
            - source: str
                The source of the transaction, such as "Chase" or "Amex"
            - account_id: str
                The account ID of the transaction, such as "Chase_1234" or "Amex_1234"
            - additional_details: str
                Additional source details about the transaction as it appears in the transaction feed
            - account_type: str
                The type of account the transaction was made from, such as "Checking" or "Credit Card"
            - amount_enriched: float
                The enriched amount of the transaction.
                Chase, SoFi, and Wells Fargo transactions are already in the correct format, negative for charges and positive for income.
                Amex transactions are converted to the correct format.
            - transaction_type: str
                The type of transaction, such as "Debit" or "Credit"
            - category_enriched: str
                The enriched category of the transaction
            - subcategory_enriched: str
                The enriched subcategory of the transaction
            - merchant: str
                The enriched merchant of the transaction
    """
    
    # Extract existing fields
    enriched_df = df.copy()
    
    # Enrich fields
    enriched_df[['amount_enriched', 'transaction_type', 'category_enriched', 'subcategory_enriched', 'merchant']] = enriched_df.apply(process_transaction, axis=1)

    return enriched_df


def main():
    """
    Main function to run the transaction enrichment process.
    """
    print("Loading transactions...")
    transactions_df = load_transactions(file_path='data/consolidated_transactions.csv')
    
    print(f"Enriching {len(transactions_df)} transactions...")
    enriched_df = enrich_transactions(transactions_df)
    
    # Save enriched transactions to a new file
    enriched_df.to_csv('data/my_consolidated_transactions_enriched.csv', index=False)
    print("Saved enriched transactions to data/my_consolidated_transactions_enriched.csv")

if __name__ == "__main__":
    main() 