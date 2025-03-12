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

def load_transactions(file_path='data/consolidated_transactions.csv'):
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

def determine_subcategory(row):
    """
    Determine a subcategory based on transaction description and category.
    
    Args:
        row: DataFrame row containing transaction data
        
    Returns:
        str: Sub-category for the transaction
    """
    description = str(row['description']).lower()
    category = str(row['category']).lower()
    transaction_type = str(row['transaction_type'])
    
    # Sub-categories for Groceries
    if category == 'groceries':
        if any(store in description for store in ['safeway', 'andronicos']):
            return 'Supermarket'
        elif 'costco' in description:
            return 'Wholesale Club'
        elif any(store in description for store in ['gus', 'community market', 'lucas market', 'h mart']):
            return 'Specialty Grocery'
        elif 'walmart' in description:
            return 'Grocery Store'
        else:
            return 'General Grocery'
    
    # Sub-categories for Shopping
    elif category == 'shopping':
        if any(keyword in description for keyword in ['amazon', 'mktpl']):
            return 'Online Marketplace'
        elif any(keyword in description for keyword in ['nord', 'sephora']):
            return 'Department Store'
        elif 'apple' in description:
            return 'Electronics'
        elif any(keyword in description for keyword in ['vpn', 'chatgpt', 'openai', 'cursor']):
            return 'Software Subscription'
        elif 'nintendo' in description:
            return 'Gaming'
        elif 'tips' in description:
            return 'Service Tips'
        else:
            return 'General Shopping'
    
    # Sub-categories for Food & Drink
    elif category == 'food & drink':
        if any(keyword in description for keyword in ['doordash', 'uber eats', 'rappi']):
            return 'Food Delivery'
        elif any(keyword in description for keyword in ['pizza', 'taco']):
            return 'Fast Food'
        elif any(keyword in description for keyword in ['restaurant', 'grill', 'café', 'cafe', 'breakfast']):
            return 'Restaurant'
        elif any(keyword in description for keyword in ['el torito', 'the grill', 'rosamunde', 'angies']):
            return 'Sit-down Restaurant'
        else:
            return 'Dining'
    
    # Sub-categories for Bills & Utilities
    elif category == 'bills & utilities':
        if 'pg&e' in description:
            return 'Electricity/Gas'
        elif any(keyword in description for keyword in ['spotify', 'hulu', 'prime', 'video']):
            return 'Streaming Services'
        elif any(keyword in description for keyword in ['internet', 'cable']):
            return 'Internet/Cable'
        else:
            return 'General Utilities'
    
    # Sub-categories for Entertainment
    elif category == 'entertainment':
        if any(keyword in description for keyword in ['steam', 'game', 'nintendo']):
            return 'Video Games'
        elif any(keyword in description for keyword in ['youtube', 'spotify']):
            return 'Streaming'
        elif 'ticketmaster' in description:
            return 'Events/Concerts'
        else:
            return 'General Entertainment'
    
    # Sub-categories for Direct Payment
    elif category == 'direct payment':
        if 'robinhood' in description:
            return 'Investment Platform'
        elif 'education' in description:
            return 'Education Payment'
        elif 'venmo' in description:
            return 'P2P Payment'
        elif 'dept education' in description:
            return 'Student Loan'
        else:
            return 'Other Payment'
    
    # Sub-categories for Health & Wellness
    elif category == 'health & wellness':
        if 'classpass' in description:
            return 'Fitness Membership'
        else:
            return 'General Health'
    
    # Sub-categories for Travel
    elif category == 'travel':
        if 'lyft' in description:
            return 'Rideshare'
        elif 'uber' in description and 'eats' not in description:
            return 'Rideshare'
        else:
            return 'General Travel'
    
    # Sub-categories for Education
    elif category == 'education':
        if 'coursera' in description:
            return 'Online Course'
        else:
            return 'General Education'
            
    # Sub-categories for Transaction Types
    if transaction_type == 'Credit Payment Sent':
        if 'chase' in description:
            return 'Chase Credit Card Payment'
        elif 'amex' in description:
            return 'Amex Credit Card Payment'
        else:
            return 'Other Credit Card Payment'
            
    elif transaction_type == 'Credit Payment Received':
        if 'mobile' in description:
            return 'Mobile Payment Received'
        else:
            return 'Credit Card Payment Received'
            
    elif transaction_type == 'Income':
        if 'xpo cnw' in description:
            return 'Salary/Wages'
        elif 'interest' in description:
            return 'Interest Income'
        elif any(keyword in description for keyword in ['refund', 'tourist']):
            return 'Refund Income'
        elif any(keyword in description for keyword in ['transfer', 'to']):
            return 'Internal Transfer'
        else:
            return 'Other Income'
            
    elif transaction_type == 'Refund':
        if 'payment' in description:
            return 'Payment Refund'
        elif any(keyword in description for keyword in ['uber', 'paypal']):
            return 'Service Refund'
        else:
            return 'Purchase Refund'
            
    elif transaction_type in ['Transfer', 'Incoming Transfer', 'Outgoing Transfer']:
        # Common subcategories for all transfer types
        if 'vault' in description or 'to house' in description:
            return 'Savings Transfer'
        elif any(bank in description.lower() for bank in ['wells fargo', 'chase', 'bank of america', 'sofi bank']):
            return 'Bank Transfer'
        
        # Directional subcategories
        if transaction_type == 'Incoming Transfer':
            return 'Incoming Bank Transfer'
        elif transaction_type == 'Outgoing Transfer':
            return 'Outgoing Bank Transfer'
        else:
            return 'Account Transfer'
            
    elif transaction_type == 'Charge':
        if 'wells fargo' in description:
            return 'Bank Withdrawal'
        
    # Default sub-category
    return 'General'

def add_merchant_name(description):
    """
    Extract a simplified merchant name from the description.
    
    Args:
        description: Transaction description string
        
    Returns:
        str: Extracted merchant name
    """
    description = str(description)
    
    # Common patterns to clean up
    patterns = [
        # Remove common prefixes
        (r'^(SQ|TST|DD|PP|PAYPAL|MOBILE|AMEX)\s*\*\s*', ''),
        # Remove transaction identifiers
        (r'\b[A-Z0-9]{6,}\b', ''),
        # Remove dates and numbers at the end
        (r'\s+\d{1,2}[-/]\d{1,2}(\s|$)', ' '),
        # Remove common suffixes
        (r'\s+(help.uber.com|8005928996|com|inc).*$', ''),
        # Remove special characters
        (r'[*]', '')
    ]
    
    # Apply all cleanup patterns
    clean_name = description
    for pattern, replacement in patterns:
        clean_name = re.sub(pattern, replacement, clean_name, flags=re.IGNORECASE)
    
    # Additional cleanup
    clean_name = clean_name.strip()
    
    # If empty after cleaning, use the original description
    if not clean_name:
        return description
    
    return clean_name

def add_transaction_month(date):
    """
    Extract month name from date for grouping by month.
    
    Args:
        date: Transaction date
        
    Returns:
        str: Month name (e.g., 'January')
    """
    if pd.isna(date):
        return "Unknown"
    return date.strftime('%B')

def add_transaction_day_of_week(date):
    """
    Extract day of week from date.
    
    Args:
        date: Transaction date
        
    Returns:
        str: Day of week (e.g., 'Monday')
    """
    if pd.isna(date):
        return "Unknown"
    return date.strftime('%A')

def add_is_weekend(date):
    """
    Determine if transaction occurred on a weekend.
    
    Args:
        date: Transaction date
        
    Returns:
        bool: True if weekend, False otherwise
    """
    if pd.isna(date):
        return False
    # 5 = Saturday, 6 = Sunday
    return date.weekday() >= 5

def identify_recurring_transactions(df):
    """
    Identify potential recurring transactions based on patterns.
    
    Args:
        df (pd.DataFrame): Transaction DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with added recurring transaction markers
    """
    # Create a copy of the dataframe
    df_recurring = df.copy()
    
    # Initialize columns
    df_recurring['is_recurring'] = False
    df_recurring['recurring_frequency'] = None
    
    # Look for common subscription services in descriptions
    subscription_keywords = [
        'netflix', 'spotify', 'hulu', 'prime', 'youtube', 'disney+', 'chatgpt', 
        'subscription', 'monthly', 'classpass', 'internet', 'bill', 'utilities',
        'insurance', 'membership', 'mobile', 'wireless', 'openai', 'robinhood'
    ]
    
    # Mark transactions with subscription keywords as recurring
    subscription_mask = df_recurring['description'].str.lower().str.contains(
        '|'.join(subscription_keywords), na=False
    )
    df_recurring.loc[subscription_mask, 'is_recurring'] = True
    df_recurring.loc[subscription_mask, 'recurring_frequency'] = 'Monthly (Probable)'
    
    # Find exact amount matches with identical descriptions (potential recurring transactions)
    # Group by description and amount
    potential_recurring = df_recurring.groupby(['description', 'amount']).size().reset_index(name='frequency')
    potential_recurring = potential_recurring[potential_recurring['frequency'] > 1]
    
    # Find frequency pattern (monthly, weekly)
    for _, row in potential_recurring.iterrows():
        description = row['description']
        amount = row['amount']
        
        # Find all transactions matching this description and amount
        matching_txns = df_recurring[
            (df_recurring['description'] == description) & 
            (df_recurring['amount'] == amount)
        ].sort_values('transaction_date')
        
        if len(matching_txns) >= 2:
            # Calculate average days between transactions
            dates = matching_txns['transaction_date'].tolist()
            if len(dates) >= 2:
                days_between = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_days = sum(days_between) / len(days_between)
                
                # Set the frequency based on average days between transactions
                frequency = None
                if 25 <= avg_days <= 35:
                    frequency = 'Monthly'
                elif 6 <= avg_days <= 10:
                    frequency = 'Weekly'
                elif 13 <= avg_days <= 17:
                    frequency = 'Bi-weekly'
                
                if frequency:
                    # Mark all matching transactions
                    matching_indices = matching_txns.index
                    df_recurring.loc[matching_indices, 'is_recurring'] = True
                    df_recurring.loc[matching_indices, 'recurring_frequency'] = frequency
    
    return df_recurring

def categorize_spending_type(row):
    """
    Categorize spending as discretionary or non-discretionary.
    
    Args:
        row: DataFrame row containing transaction data
        
    Returns:
        str: Spending type (Discretionary, Non-discretionary, Income, Transfer)
    """
    # Skip non-spending transactions
    if row['transaction_type'] in ['Income', 'Credit Payment Received', 'Refund']:
        return 'Income/Refund'
    
    if row['transaction_type'] in ['Credit Payment Sent']:
        return 'Credit Payment'
    
    # Handle transfers directly from transaction type
    if row['transaction_type'] in ['Transfer', 'Incoming Transfer', 'Outgoing Transfer']:
        return 'Transfer'
    
    # Check sub-category first
    sub_category = str(row['subcategory']).lower()
    
    # These are transfers, not spending
    if any(keyword in sub_category for keyword in ['transfer', 'withdrawal', 'bank', 'savings transfer']):
        return 'Transfer'
    
    # Essential/Non-discretionary categories
    non_discretionary_subcats = [
        'electricity', 'gas', 'internet', 'cable', 'utilities', 
        'supermarket', 'grocery', 'student loan', 'health', 'insurance'
    ]
    
    if any(keyword in sub_category for keyword in non_discretionary_subcats):
        return 'Non-discretionary'
    
    # Now check main category
    category = str(row['category']).lower()
    
    non_discretionary_cats = [
        'bills & utilities', 'groceries', 'health & wellness', 
        'education', 'essential services'
    ]
    
    if any(keyword in category for keyword in non_discretionary_cats):
        return 'Non-discretionary'
    
    # Default is discretionary
    return 'Discretionary'

def determine_transaction_type(df):
    """
    Determine the transaction type based on various patterns and conditions.
    This function categorizes transactions as:
    - Charge: Default for most transactions
    - Outgoing Transfer: Money leaving an account to another account or vault
    - Incoming Transfer: Money coming into an account from another account or vault
    - Credit Payment Sent: Payments made to credit cards
    - Payment: Payments received on credit cards
    - Income: Money received as income, salary, direct deposits
    - Refund: Refunded money from previous purchases
    """
    # Initialize with default value
    df['transaction_type'] = 'Charge'
    
    # NEW: Identify income transactions
    # Direct deposits are almost always income (salary, etc.)
    direct_deposit_mask = (df['category'] == 'Direct Deposit')
    df.loc[direct_deposit_mask, 'transaction_type'] = 'Income'
    
    # Regular deposits to checking accounts should be classified as income
    # unless they're transfers from other accounts
    general_deposit_mask = (df['account_type'] == 'Checkings') & \
                          (df['category'] == 'Deposit') & \
                          ~df['description'].str.contains('transfer|xfer|zelle|venmo', case=False, na=False)
    df.loc[general_deposit_mask, 'transaction_type'] = 'Income'
    
    # Income-like descriptions (e.g., payroll, salary, interest)
    income_keywords = ['inc', 'salary', 'payroll', 'direct dep', 'dd ', 'interest earned', 
                       'cashback', 'dividend', 'tax refund', 'commission']
    income_pattern = '|'.join(income_keywords)
    
    income_desc_mask = df['description'].str.contains(income_pattern, case=False, na=False)
    df.loc[income_desc_mask, 'transaction_type'] = 'Income'
    
    # Identify transfers to/from savings vaults or between accounts
    transfer_keywords = ['vault', 'to house', 'savings', 'transfer to', 'move to', 'moved to', 
                       'transfer', 'xfer', 'zelle', 'venmo', 'bank2bank', 'from bank']
    transfer_pattern = '|'.join(transfer_keywords)
    
    # NEW: Identify refund transactions
    refund_keywords = ['refund', 'reembolso', 'credit adj', 'credit adjustment', 'returned purchase', 
                      'returned item', 'return of purchase', 'chargeback']
    refund_pattern = '|'.join(refund_keywords)
    
    # Refund mask - applies to both credit cards and checking accounts
    refund_mask = df['description'].str.contains(refund_pattern, case=False, na=False)
    df.loc[refund_mask, 'transaction_type'] = 'Refund'
    
    # Identify transfers from checking accounts - negative amount means money leaving (outgoing)
    outgoing_transfer_mask = (df['account_type'] == 'Checkings') & \
                           (df['amount'] < 0) & \
                           (df['description'].str.contains(transfer_pattern, case=False))
    
    df.loc[outgoing_transfer_mask, 'transaction_type'] = 'Outgoing Transfer'
    
    # Identify transfers to checking accounts - positive amount means money coming in (incoming)
    incoming_transfer_mask = (df['account_type'] == 'Checkings') & \
                           (df['amount'] > 0) & \
                           (df['description'].str.contains(transfer_pattern, case=False))
    
    df.loc[incoming_transfer_mask, 'transaction_type'] = 'Incoming Transfer'
    
    # Identify credit card payments from checking accounts
    # These are typically outgoing payments (positive amounts) from checking accounts to credit cards
    credit_card_keywords = ['chase', 'amex', 'american express', 'citi', 'discover', 'capital one', 
                          'mastercard', 'visa', 'credit card', 'credit payment', 'card payment', 'epay']
    credit_payment_pattern = '|'.join(credit_card_keywords)
    
    # Special case for Wells Fargo "ONLINE TRANSFER TO" that reference credit cards
    # These should be identified as credit payments, not transfers
    wells_fargo_online_credit_payment_mask = (df['source'].str.contains('WellsFargo', case=False)) & \
                                     (df['amount'] < 0) & \
                                     ((df['description'].str.contains('ONLINE TRANSFER TO', case=False)) |
                                      (df['description'].str.contains('ONLINE TRANSFER.*TO', case=False, regex=True))) & \
                                     (df['description'].str.contains(credit_payment_pattern, case=False))
    
    # Special case for Wells Fargo "ONLINE TRANSFER TO" - these are outgoing transfers with negative amounts
    # BUT exclude credit card payments we've identified above
    wells_fargo_online_transfer_out_mask = (df['source'].str.contains('WellsFargo', case=False)) & \
                                     (df['amount'] < 0) & \
                                     ((df['description'].str.contains('ONLINE TRANSFER TO', case=False)) |
                                      (df['description'].str.contains('ONLINE TRANSFER.*TO', case=False, regex=True))) & \
                                     ~(df['description'].str.contains(credit_payment_pattern, case=False))
    
    df.loc[wells_fargo_online_transfer_out_mask, 'transaction_type'] = 'Outgoing Transfer'
    
    # PayPal charges for Wells Fargo (negative amounts that are not transfers but payments for services)
    wells_fargo_paypal_charge_mask = (df['source'].str.contains('WellsFargo', case=False)) & \
                                     (df['amount'] < 0) & \
                                     (df['description'].str.contains('PAYPAL', case=False)) & \
                                     ~(df['description'].str.contains('transfer from|payment from', case=False))
                                     
    df.loc[wells_fargo_paypal_charge_mask, 'transaction_type'] = 'Charge'
    
    # For transactions between different banks that are identified by bank name:
    bank_keywords = ['sofi bank', 'wells fargo', 'chase bank', 'bank of america', 'citi bank', 
                    'wells fargo bank', 'bank na', 'jpmorgan chase', 'citibank', 'us bank']
    bank_transfer_pattern = '|'.join(bank_keywords)
    
    # Identify bank-to-bank transfers
    bank_transfer_mask = (df['account_type'] == 'Checkings') & \
                        (df['description'].str.contains(bank_transfer_pattern, case=False)) & \
                        (df['description'].str.contains('transfer', case=False))
    
    # For bank transfers, determine direction based on amount sign
    outgoing_bank_transfer_mask = bank_transfer_mask & (df['amount'] < 0)
    incoming_bank_transfer_mask = bank_transfer_mask & (df['amount'] > 0)
    df.loc[outgoing_bank_transfer_mask, 'transaction_type'] = 'Outgoing Transfer'
    df.loc[incoming_bank_transfer_mask, 'transaction_type'] = 'Incoming Transfer'
                        
    # Identify bank withdrawals and deposits (without explicit transfer keyword)
    bank_withdrawal_mask = (df['account_type'] == 'Checkings') & \
                          (df['description'].str.contains(bank_transfer_pattern, case=False)) & \
                          (df['category'] == 'Withdrawal')
    
    bank_deposit_mask = (df['account_type'] == 'Checkings') & \
                       (df['description'].str.contains(bank_transfer_pattern, case=False)) & \
                       (df['category'] == 'Deposit')
    
    # For SoFi, bank withdrawals (money leaving) are positive and deposits (money coming in) are negative
    df.loc[bank_withdrawal_mask, 'transaction_type'] = 'Outgoing Transfer'
    df.loc[bank_deposit_mask, 'transaction_type'] = 'Incoming Transfer'
    
    # Combined masks for using in other classifications
    all_outgoing_transfer_mask = outgoing_transfer_mask | outgoing_bank_transfer_mask | bank_withdrawal_mask | wells_fargo_online_transfer_out_mask
    all_incoming_transfer_mask = incoming_transfer_mask | incoming_bank_transfer_mask | bank_deposit_mask
    
    # Credit card payments from checking accounts (positive amount + checking account + credit card keyword in description)
    credit_payment_mask = (df['amount'] > 0) & \
                        (df['account_type'] == 'Checkings') & \
                        ~all_outgoing_transfer_mask & \
                        ~all_incoming_transfer_mask & \
                        (df['description'].str.contains(credit_payment_pattern, case=False))
    
    # Special case for Wells Fargo - their outgoing credit card payments have negative amounts
    wells_fargo_credit_payment_mask = (df['amount'] < 0) & \
                                   (df['account_type'] == 'Checkings') & \
                                   (df['source'].str.contains('WellsFargo', case=False)) & \
                                   ~incoming_transfer_mask & \
                                   ~all_outgoing_transfer_mask & \
                                   ~all_incoming_transfer_mask & \
                                   (df['description'].str.contains(credit_payment_pattern, case=False) | 
                                   df['description'].str.contains('credit crd epay', case=False))
    
    # Special case for Wells Fargo ONLINE TRANSFER to credit cards - these should also be credit payments
    wells_fargo_online_credit_payment_mask = (df['source'].str.contains('WellsFargo', case=False)) & \
                                         (df['amount'] < 0) & \
                                         (df['description'].str.contains('ONLINE TRANSFER', case=False)) & \
                                         (df['description'].str.contains(credit_payment_pattern, case=False))
    
    # Special case for Wells Fargo bill payments - they also have negative amounts but should be charges
    wells_fargo_bill_payment_mask = (df['amount'] < 0) & \
                                  (df['account_type'] == 'Checkings') & \
                                  (df['source'].str.contains('WellsFargo', case=False)) & \
                                  (df['description'].str.contains('bill pay', case=False))
    
    df.loc[credit_payment_mask, 'transaction_type'] = 'Credit Payment Sent'
    df.loc[wells_fargo_credit_payment_mask, 'transaction_type'] = 'Credit Payment Sent'
    df.loc[wells_fargo_online_credit_payment_mask, 'transaction_type'] = 'Credit Payment Sent'
    
    # Set Wells Fargo bill payments as Charge (not Refund)
    df.loc[wells_fargo_bill_payment_mask, 'transaction_type'] = 'Charge'
    
    # NEW: Identify payments received on credit cards
    # These typically have negative amounts and descriptions containing payment-related terms
    payment_keywords = ['payment', 'thank you', 'pymt', 'autopay', 'automatic payment', 'web payment']
    payment_pattern = '|'.join(payment_keywords)
    
    # Credit card payment received mask (for credit card accounts)
    credit_payment_received_mask = (df['account_type'] == 'Credit Card') & \
                                 (df['amount'] < 0) & \
                                 (df['description'].str.contains(payment_pattern, case=False))
    
    df.loc[credit_payment_received_mask, 'transaction_type'] = 'Credit Payment Received'
    
    return df

def normalize_transaction_signs(df):
    """
    Normalize transaction signs according to intuitive financial conventions:
    - For all accounts: money leaving (outflow) is negative, money incoming (inflow) is positive
    - For credit cards: charges (spending) are negative, payments received are positive
    """
    # Create a copy of the amount before modification
    df['original_amount'] = df['amount'].copy()
    
    # 1. For credit cards: make charges negative and payments positive
    credit_card_mask = df['account_type'] == 'Credit Card'
    
    # Credit card charges should be negative (current convention is positive)
    charge_mask = credit_card_mask & (df['transaction_type'] == 'Charge')
    df.loc[charge_mask & (df['amount'] > 0), 'amount'] = -df.loc[charge_mask & (df['amount'] > 0), 'amount']
    
    # Credit card payments received should be positive (current convention is negative)
    payment_mask = credit_card_mask & (df['transaction_type'] == 'Credit Payment Received')
    df.loc[payment_mask & (df['amount'] < 0), 'amount'] = -df.loc[payment_mask & (df['amount'] < 0), 'amount']
    
    # 2. For checking accounts: outgoing money negative, incoming money positive
    checking_mask = df['account_type'] == 'Checkings'
    
    # Outgoing transfers should be negative
    outgoing_mask = checking_mask & (df['transaction_type'] == 'Outgoing Transfer')
    df.loc[outgoing_mask & (df['amount'] > 0), 'amount'] = -df.loc[outgoing_mask & (df['amount'] > 0), 'amount']
    
    # Incoming transfers should be positive
    incoming_mask = checking_mask & (df['transaction_type'] == 'Incoming Transfer')
    df.loc[incoming_mask & (df['amount'] < 0), 'amount'] = -df.loc[incoming_mask & (df['amount'] < 0), 'amount']
    
    # Credit payments sent should be negative (money leaving checking account)
    credit_payment_sent_mask = checking_mask & (df['transaction_type'] == 'Credit Payment Sent')
    df.loc[credit_payment_sent_mask & (df['amount'] > 0), 'amount'] = -df.loc[credit_payment_sent_mask & (df['amount'] > 0), 'amount']
    
    # NEW: Make sure all income transactions have positive amounts
    income_mask = df['transaction_type'] == 'Income'
    df.loc[income_mask & (df['amount'] < 0), 'amount'] = -df.loc[income_mask & (df['amount'] < 0), 'amount']
    
    # Direct deposits should be positive (current convention shows negative for some)
    direct_deposit_mask = checking_mask & (df['category'] == 'Direct Deposit')
    df.loc[direct_deposit_mask & (df['amount'] < 0), 'amount'] = -df.loc[direct_deposit_mask & (df['amount'] < 0), 'amount']
    
    # General principle for non-categorized transactions
    # For checking accounts, flip "Charge" transactions that are being treated as deposits
    charge_deposit_mask = checking_mask & (df['transaction_type'] == 'Charge') & (df['amount'] < 0) & \
                         df['description'].str.contains('Inc|Corp|LLC|Ltd|Deposit|Salary|Payroll|Payment received|Refund', case=False, regex=True)
    df.loc[charge_deposit_mask, 'amount'] = -df.loc[charge_deposit_mask, 'amount']
    
    # Update original_amount to match the normalized amount
    # This ensures consistent sign convention throughout the dataset
    df['original_amount'] = df['amount']
    
    return df

def enrich_transactions(df):
    """
    Enrich the transaction data by adding sub-categories, merchant name, etc.
    """
    # First determine the transaction type
    df = determine_transaction_type(df)
    
    df['subcategory'] = df.apply(lambda row: determine_subcategory(row), axis=1)
    
    # Extract merchant name from description
    df['merchant'] = df['description'].apply(add_merchant_name)
    
    # Identify recurring transactions
    df = identify_recurring_transactions(df)
    
    # Determine if transaction is discretionary or not
    df['spending_type'] = df.apply(lambda row: categorize_spending_type(row), axis=1)
    
    # Normalize transaction signs to be more intuitive
    df = normalize_transaction_signs(df)
    
    # Add absolute amount for easier analysis
    df['absolute_amount'] = df['amount'].abs()
    
    # Add amount category based on transaction size
    df['amount_category'] = pd.cut(
        df['absolute_amount'],
        bins=[0, 10, 50, 100, 250, 500, 1000, float('inf')],
        labels=['Under $10', '$10-$50', '$50-$100', '$100-$250', '$250-$500', '$500-$1000', 'Over $1000'],
        right=False
    )
    
    # Add time-based features
    df['transaction_month'] = df['transaction_date'].apply(lambda x: x.strftime('%Y-%m'))
    df['day_of_week'] = df['transaction_date'].apply(add_transaction_day_of_week)
    df['is_weekend'] = df['transaction_date'].apply(add_is_weekend)
    
    return df

def main():
    """
    Main function to run the transaction enrichment process.
    """
    print("Loading transactions...")
    transactions_df = load_transactions()
    
    print(f"Enriching {len(transactions_df)} transactions...")
    enriched_df = enrich_transactions(transactions_df)
    
    # Save enriched transactions to a new file
    enriched_df.to_csv('data/consolidated_transactions_enriched.csv', index=False)
    print(f"Saved enriched transactions to data/consolidated_transactions_enriched.csv")
    
    # Generate some statistics about the enriched data
    print("\n--- Enrichment Results ---")
    
    # Subcategory analysis
    subcategories = enriched_df['subcategory'].nunique()
    print(f"\nCreated {subcategories} sub-categories")
    print("Top sub-categories by transaction count:")
    subcategory_counts = enriched_df['subcategory'].value_counts().head(5)
    for subcategory, count in subcategory_counts.items():
        print(f"  {subcategory}: {count}")
    
    # Amount category analysis
    print(f"\n--- Amount Categories ---")
    amount_category_counts = enriched_df['amount_category'].value_counts()
    for category, count in amount_category_counts.items():
        print(f"  {category}: {count}")
    
    # Day of week analysis
    print(f"\n--- Day of Week Analysis ---")
    day_of_week_counts = enriched_df['day_of_week'].value_counts()
    for day, count in day_of_week_counts.items():
        print(f"  {day}: {count}")
    
    # Weekend vs weekday analysis
    weekend_count = enriched_df[enriched_df['is_weekend']].shape[0]
    weekday_count = enriched_df[~enriched_df['is_weekend']].shape[0]
    print(f"Weekend transactions: {weekend_count} ({weekend_count/len(enriched_df)*100:.1f}%)")
    print(f"Weekday transactions: {weekday_count} ({weekday_count/len(enriched_df)*100:.1f}%)")
    
    # Recurring transaction analysis
    recurring_count = enriched_df[enriched_df['is_recurring']].shape[0]
    print(f"\nIdentified {recurring_count} recurring transactions ({recurring_count/len(enriched_df)*100:.1f}%)")
    
    # Spending type analysis
    spending_type_counts = enriched_df['spending_type'].value_counts()
    print("\nTransaction counts by spending type:")
    for spending_type, count in spending_type_counts.items():
        print(f"  {spending_type}: {count}")
    
    # Calculate spending amounts by type
    print("\nTotal amounts by spending type:")
    spending_amounts = enriched_df.groupby('spending_type')['amount'].sum()
    for spending_type, amount in spending_amounts.items():
        # With our new sign convention, expenses are negative and income is positive
        # We should display the absolute value for expenses
        if spending_type in ['Discretionary', 'Non-discretionary', 'Credit Payment']:
            print(f"  {spending_type}: ${abs(amount):.2f}")
        else:
            print(f"  {spending_type}: ${amount:.2f}")
    
    # Monthly spending analysis
    print("\nMonthly spending:")
    # With new sign convention, expenses are negative so we filter for negative amounts
    monthly_spending = enriched_df[enriched_df['amount'] < 0].groupby('transaction_month')['amount'].sum()
    for month, amount in monthly_spending.items():
        print(f"  {month}: ${abs(amount):.2f}")
    
    # Top merchants by spending
    print("\nTop 10 merchants by spending:")
    # With new sign convention, expenses are negative so we filter for negative amounts
    merchant_spending = enriched_df[enriched_df['amount'] < 0].groupby('merchant')['amount'].sum().sort_values().head(10)
    for merchant, amount in merchant_spending.items():
        print(f"  {merchant}: ${abs(amount):.2f}")

if __name__ == "__main__":
    main() 