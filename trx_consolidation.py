#!/usr/bin/env python3
"""
Transaction Data Processing Script

This script processes transaction data from various bank CSV files (Amex, Chase, SoFi, and Wells Fargo)
and consolidates them into a standardized format in a single CSV file.
"""

import os
import pandas as pd
import glob
import re
from datetime import datetime

def process_amex_transactions(file_path):
    """
    Process Amex transaction CSV files and convert to a standardized format.
    
    Args:
        file_path (str): Path to the Amex CSV file
        
    Returns:
        pd.DataFrame: Standardized DataFrame of transactions
    """
    # Extract account identifier from filename
    account_id = re.search(r'Amex(\d+)', os.path.basename(file_path))
    account_id = account_id.group(1) if account_id else 'Unknown'
    
    # Read the Amex CSV file
    df = pd.read_csv(file_path)
    
    # Standardize the DataFrame
    standardized_df = pd.DataFrame({
        'transaction_date': pd.to_datetime(df['Date'], format='%m/%d/%Y'),
        'post_date': None,  # Amex doesn't provide post date
        'description': df['Description'],
        'amount': df['Amount'],  # Amex amounts are already in the correct format (debit positive, credit negative)
        'category': df['Category'],
        'source': 'Amex',
        'account_id': f'Amex_{account_id}',
        'additional_details': df['Extended Details'].fillna(''),
        'account_type': 'Credit Card'  # Add account type
    })
    
    return standardized_df

def process_chase_transactions(file_path):
    """
    Process Chase transaction CSV files and convert to a standardized format.
    
    Args:
        file_path (str): Path to the Chase CSV file
        
    Returns:
        pd.DataFrame: Standardized DataFrame of transactions
    """
    # Extract account identifier from filename
    account_id = re.search(r'Chase(\d+)', os.path.basename(file_path))
    account_id = account_id.group(1) if account_id else 'Unknown'
    
    # Read the Chase CSV file
    df = pd.read_csv(file_path)
    
    # Standardize the DataFrame
    standardized_df = pd.DataFrame({
        'transaction_date': pd.to_datetime(df['Transaction Date'], format='%m/%d/%Y'),
        'post_date': pd.to_datetime(df['Post Date'], format='%m/%d/%Y'),
        'description': df['Description'],
        'amount': df['Amount'],
        'category': df['Category'],
        'source': 'Chase',
        'account_id': f'Chase_{account_id}',
        'additional_details': df['Memo'].fillna(''),
        'account_type': 'Credit Card'  # Add account type
    })
    
    return standardized_df

def process_sofi_transactions(file_path):
    """
    Process SoFi transaction CSV files and convert to a standardized format.
    
    Args:
        file_path (str): Path to the SoFi CSV file
        
    Returns:
        pd.DataFrame: Standardized DataFrame of transactions
    """
    # Extract account identifier from filename
    account_id = re.search(r'Sofi-Checking-(\d+)', os.path.basename(file_path))
    account_id = account_id.group(1) if account_id else 'Unknown'
    
    # Read the SoFi CSV file
    df = pd.read_csv(file_path)
    
    # Standardize the DataFrame
    standardized_df = pd.DataFrame({
        'transaction_date': pd.to_datetime(df['Date'], format='%Y-%m-%d'),
        'post_date': None,  # SoFi doesn't provide separate post date in this format
        'description': df['Description'],
        'amount': df['Amount'],
        'category': df['Type'],  # Use 'Type' as category since SoFi doesn't provide explicit categories
        'source': 'SoFi',
        'account_id': f'SoFi_{account_id}',
        'additional_details': df['Status'].fillna(''),
        'account_type': 'Checkings'  # Add account type
    })
    
    return standardized_df

def process_wells_fargo_transactions(file_path):
    """
    Process Wells Fargo transaction CSV files and convert to a standardized format.
    Handles both checking and credit card accounts.
    
    Args:
        file_path (str): Path to the Wells Fargo CSV file
        
    Returns:
        pd.DataFrame: Standardized DataFrame of transactions
    """
    # Extract account identifier from filename
    file_name = os.path.basename(file_path).lower()
    if 'cc' in file_name:
        account_id = 'CC'  # Credit Card identifier
        account_type = 'Credit Card'
    else:
        account_id = 'WF'  # Default checking identifier
        account_type = 'Checkings'
    
    # Read the Wells Fargo CSV file - note it has no header
    # The format appears to be Date, Amount, Flag, Empty field, Description
    df = pd.read_csv(file_path, header=None, names=['Date', 'Amount', 'Flag', 'Empty', 'Description'],
                    quoting=1)  # quoting=1 for QUOTE_ALL to handle the quoted fields
    
    # Standardize the DataFrame
    standardized_df = pd.DataFrame({
        'transaction_date': pd.to_datetime(df['Date'], format='%m/%d/%Y'),
        'post_date': None,  # Wells Fargo doesn't provide post date in this format
        'description': df['Description'],
        'amount': df['Amount'].astype(float),  # No need to invert sign - Wells Fargo negatives (outgoing) should remain negative
                                              # and positives (incoming) should remain positive in our standardized format
        'category': 'Uncategorized',  # Wells Fargo doesn't provide categories in this format
        'source': 'WellsFargo',
        'account_id': f'WellsFargo_{account_id}',
        'additional_details': df['Flag'].fillna(''),
        'account_type': account_type  # Use the determined account type
    })
    
    return standardized_df

def process_file(file_path):
    """
    Process a transaction file based on its type (Amex, Chase, SoFi, Wells Fargo)
    
    Args:
        file_path (str): Path to the transaction file
        
    Returns:
        pd.DataFrame: Standardized DataFrame of transactions
    """
    file_name = os.path.basename(file_path).lower()
    
    if 'amex' in file_name:
        return process_amex_transactions(file_path)
    elif 'chase' in file_name:
        return process_chase_transactions(file_path)
    elif 'sofi' in file_name:
        return process_sofi_transactions(file_path)
    elif 'wellsfargo' in file_name:
        return process_wells_fargo_transactions(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return None

def get_date_range_from_filename(file_path):
    """
    Extract date range from filename to identify statement period.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        tuple: (start_date, end_date) as datetime objects or None if not found
    """
    date_match = re.search(r'(\d{8})_(\d{8})', os.path.basename(file_path))
    if date_match:
        start_date_str, end_date_str = date_match.groups()
        try:
            start_date = datetime.strptime(start_date_str, '%Y%m%d')
            end_date = datetime.strptime(end_date_str, '%Y%m%d')
            return start_date, end_date
        except ValueError:
            return None, None
    return None, None

def consolidate_transactions(data_folder, output_file='consolidated_transactions.csv'):
    """
    Consolidate transaction data from multiple sources into a single DataFrame.
    
    Args:
        data_folder (str): Path to folder containing transaction files
        output_file (str): Name of output CSV file
        
    Returns:
        pd.DataFrame: Consolidated transactions DataFrame
    """
    # Get all CSV files in the data folder
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv') or f.endswith('.CSV')]
    
    # Filter out the consolidated output file if it exists
    csv_files = [f for f in csv_files if f != output_file and f != 'consolidated_transactions_enriched.csv']
    
    if not csv_files:
        raise ValueError(f"No transaction files found in {data_folder}")
    
    # Process each file
    filtered_transactions = []
    for filename in csv_files:
        filepath = os.path.join(data_folder, filename)
        transactions = process_file(filepath)
        
        if transactions is not None and not transactions.empty:
            print(f"Processed {filepath}: {len(transactions)} transactions")
            filtered_transactions.append(transactions)
        else:
            print(f"Warning: No transactions processed from {filepath}")
    
    # Concat with clear dtypes to avoid warnings
    consolidated_df = pd.concat(filtered_transactions, ignore_index=True, sort=False)
    
    # Sort by transaction date
    consolidated_df = consolidated_df.sort_values('transaction_date', ascending=False)
    
    # Save to CSV
    output_path = os.path.join(data_folder, output_file)
    consolidated_df.to_csv(output_path, index=False)
    
    print(f"Consolidated {len(consolidated_df)} transactions from {len(filtered_transactions)} files to {output_path}")
    return consolidated_df

def analyze_transactions(transactions_df):
    """
    Perform basic analysis on transaction data.
    
    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data
        
    Returns:
        dict: Dictionary containing analysis results
    """
    if transactions_df is None or transactions_df.empty:
        return {"error": "No transaction data available"}
    
    # Create masks for different transaction amounts
    spent_mask = transactions_df['amount'] > 0
    income_mask = transactions_df['amount'] < 0
    
    # Calculate totals
    total_spent = transactions_df[spent_mask]['amount'].sum()
    
    # Calculate interest separately (for informational purposes)
    interest_mask = (transactions_df['amount'] < 0) & transactions_df['description'].str.contains('interest', case=False)
    total_interest = abs(transactions_df[interest_mask]['amount'].sum())
    
    results = {
        "total_transactions": len(transactions_df),
        "date_range": {
            "start": transactions_df['transaction_date'].min().strftime('%Y-%m-%d'),
            "end": transactions_df['transaction_date'].max().strftime('%Y-%m-%d')
        },
        "by_account_id": transactions_df.groupby('account_id').size().to_dict(),
        "by_category": transactions_df.groupby('category').size().to_dict(),
        "spending_by_category": transactions_df.groupby('category')['amount'].sum().to_dict(),
        "total_spent": total_spent,
        "total_interest": total_interest,
        "transaction_counts": {
            "total": len(transactions_df),
            "spent": spent_mask.sum(),
            "income": income_mask.sum()
        }
    }
    
    return results

def main():
    """Main function to run the transaction consolidation process."""
    # Set data folder path
    data_folder = 'data'
    
    # Consolidate transactions
    transactions = consolidate_transactions(data_folder)
    
    # Perform analysis if transactions were found
    if transactions is not None:
        analysis = analyze_transactions(transactions)
        print("\nTransaction Analysis:")
        print(f"Total Transactions: {analysis['total_transactions']}")
        print(f"Date Range: {analysis['date_range']['start']} to {analysis['date_range']['end']}")
        print(f"Total Spent: ${analysis['total_spent']:.2f}")
        print(f"Total Interest: ${analysis['total_interest']:.2f}")
        
        print("\nTransaction Counts:")
        print(f"  Spent: {analysis['transaction_counts']['spent']}")
        print(f"  Income: {analysis['transaction_counts']['income']}")
        
        print("\nTop 5 Spending Categories:")
        spending_by_category = sorted(
            [(k, v) for k, v in analysis['spending_by_category'].items() if v > 0],
            key=lambda x: x[1], reverse=True
        )
        for category, amount in spending_by_category[:5]:
            print(f"  {category}: ${amount:.2f}")

if __name__ == "__main__":
    main()
