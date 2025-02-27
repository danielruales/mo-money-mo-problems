#!/usr/bin/env python3
"""
Transaction Data Processing Script

This script processes transaction data from various bank CSV files (Amex and Chase)
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
    account_id = os.path.basename(file_path).split('_')[0]
    
    # Read the Amex CSV file
    df = pd.read_csv(file_path)
    
    # Standardize the DataFrame
    standardized_df = pd.DataFrame({
        'transaction_date': pd.to_datetime(df['Date'], format='%m/%d/%Y'),
        'post_date': None,  # Amex doesn't provide post date
        'description': df['Description'],
        'amount': df['Amount'],  # Amex amounts are already in the correct format (debit positive, credit negative)
        'category': df['Category'],
        'source': f'Amex_{account_id}',
        'additional_details': df['Extended Details'].fillna('')
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
        'amount': df['Amount'] * -1,  # Convert Chase amounts (negative = debit, positive = credit) to match Amex format
        'category': df['Category'],
        'source': f'Chase_{account_id}',
        'additional_details': df['Memo'].fillna('')
    })
    
    return standardized_df

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
    Consolidate all transaction data from CSV files in the specified folder.
    
    Args:
        data_folder (str): Path to folder containing bank CSV files
        output_file (str): Name of output consolidated CSV file
        
    Returns:
        pd.DataFrame: Consolidated DataFrame of all transactions
    """
    all_transactions = []
    
    # Process Amex files
    for file_path in glob.glob(os.path.join(data_folder, 'Amex*.csv')):
        try:
            transactions = process_amex_transactions(file_path)
            if not transactions.empty:  # Only add non-empty DataFrames
                all_transactions.append(transactions)
                print(f"Processed {file_path}: {len(transactions)} transactions")
            else:
                print(f"No transactions found in {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Process Chase files
    for file_path in glob.glob(os.path.join(data_folder, 'Chase*.CSV')):
        try:
            transactions = process_chase_transactions(file_path)
            if not transactions.empty:  # Only add non-empty DataFrames
                all_transactions.append(transactions)
                print(f"Processed {file_path}: {len(transactions)} transactions")
            else:
                print(f"No transactions found in {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    if not all_transactions:
        print("No transaction files found!")
        return None
    
    # Combine all transactions - handle empty DataFrames to avoid FutureWarning
    if len(all_transactions) == 1:
        # If only one DataFrame, no need to concatenate
        consolidated_df = all_transactions[0]
    else:
        # Filter out empty or all-NA columns before concatenation
        filtered_transactions = []
        for df in all_transactions:
            # Drop columns that are all NA
            df_filtered = df.dropna(axis=1, how='all')
            filtered_transactions.append(df_filtered)
        
        # Concat with clear dtypes to avoid warnings
        consolidated_df = pd.concat(filtered_transactions, ignore_index=True, sort=False)
    
    # Add transaction_type column to categorize each transaction
    # Initialize with default value
    consolidated_df['transaction_type'] = 'Charge'
    
    # Mark payments (negative amounts that contain 'payment' in description)
    payment_mask = (consolidated_df['amount'] < 0) & consolidated_df['description'].str.contains('payment', case=False)
    consolidated_df.loc[payment_mask, 'transaction_type'] = 'Payment'
    
    # Mark refunds (negative amounts that don't contain 'payment' in description)
    refund_mask = (consolidated_df['amount'] < 0) & ~consolidated_df['description'].str.contains('payment', case=False)
    consolidated_df.loc[refund_mask, 'transaction_type'] = 'Refund'
    
    # Sort by transaction date
    consolidated_df = consolidated_df.sort_values('transaction_date', ascending=False)
    
    # Save to CSV
    output_path = os.path.join(data_folder, output_file)
    consolidated_df.to_csv(output_path, index=False)
    print(f"Consolidated {len(consolidated_df)} transactions from {len(all_transactions)} files to {output_path}")
    print(f"Transaction types: {consolidated_df['transaction_type'].value_counts().to_dict()}")
    
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
    
    # Create masks for different transaction types
    spent_mask = transactions_df['amount'] > 0
    negative_amount_mask = transactions_df['amount'] < 0
    
    # Identify payments vs refunds among negative amount transactions
    # Case-insensitive check for 'payment' in description
    payment_mask = negative_amount_mask & transactions_df['description'].str.contains('payment', case=False)
    refund_mask = negative_amount_mask & ~transactions_df['description'].str.contains('payment', case=False)
    
    # Calculate totals
    total_spent = transactions_df[spent_mask]['amount'].sum()
    total_payments = abs(transactions_df[payment_mask]['amount'].sum())
    total_refunds = abs(transactions_df[refund_mask]['amount'].sum())
    
    results = {
        "total_transactions": len(transactions_df),
        "date_range": {
            "start": transactions_df['transaction_date'].min().strftime('%Y-%m-%d'),
            "end": transactions_df['transaction_date'].max().strftime('%Y-%m-%d')
        },
        "by_source": transactions_df.groupby('source').size().to_dict(),
        "by_category": transactions_df.groupby('category').size().to_dict(),
        "spending_by_category": transactions_df.groupby('category')['amount'].sum().to_dict(),
        "total_spent": total_spent,
        "total_payments": total_payments,
        "total_refunds": total_refunds,
        "net_spending": total_spent - total_refunds,
        "transaction_counts": {
            "purchases": spent_mask.sum(),
            "payments": payment_mask.sum(),
            "refunds": refund_mask.sum()
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
        print(f"Total Payments: ${analysis['total_payments']:.2f}")
        print(f"Total Refunds: ${analysis['total_refunds']:.2f}")
        print(f"Net Spending (after refunds): ${analysis['net_spending']:.2f}")
        
        print("\nTransaction Counts:")
        print(f"  Purchases: {analysis['transaction_counts']['purchases']}")
        print(f"  Payments: {analysis['transaction_counts']['payments']}")
        print(f"  Refunds: {analysis['transaction_counts']['refunds']}")
        
        print("\nTop 5 Spending Categories:")
        spending_by_category = sorted(
            [(k, v) for k, v in analysis['spending_by_category'].items() if v > 0],
            key=lambda x: x[1], reverse=True
        )
        for category, amount in spending_by_category[:5]:
            print(f"  {category}: ${amount:.2f}")

if __name__ == "__main__":
    main()
