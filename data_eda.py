import os
import pandas as pd
import glob
import re
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import Counter
from trx_consolidation import consolidate_transactions, analyze_transactions

def analyze_spending_habits(transactions_file='consolidated_transactions.csv', data_folder='data', output_folder='analysis_results'):
    """
    Perform detailed analysis of spending habits from consolidated transaction data.
    
    Args:
        transactions_file (str): Name of the consolidated transactions CSV file
        data_folder (str): Path to the folder containing the transactions file
        output_folder (str): Path to save analysis results and charts
        
    Returns:
        dict: Dictionary containing various spending analysis metrics
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Load transactions
    file_path = os.path.join(data_folder, transactions_file)
    if not os.path.exists(file_path):
        print(f"Error: Transaction file {file_path} not found!")
        return None
    
    transactions = pd.read_csv(file_path)
    transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])
    
    # Filter to only include charges (exclude payments and refunds for spending analysis)
    charges = transactions[transactions['transaction_type'].str.lower() == 'charge'].copy()
    
    # Create various analysis metrics
    results = {}
    
    # 1. Overall spending summary
    results['total_transactions'] = len(transactions)
    results['total_charges'] = len(charges)
    results['total_payments'] = len(transactions[transactions['transaction_type'].str.lower() == 'payment'])
    results['total_refunds'] = len(transactions[transactions['transaction_type'].str.lower() == 'refund'])
    
    results['total_spent'] = charges['amount'].sum()
    results['total_refunded'] = transactions[transactions['transaction_type'].str.lower() == 'refund']['amount'].abs().sum()
    results['total_payments_amount'] = transactions[transactions['transaction_type'].str.lower() == 'payment']['amount'].abs().sum()
    results['net_spending'] = results['total_spent'] - results['total_refunded']
    
    results['avg_transaction'] = charges['amount'].mean()
    results['median_transaction'] = charges['amount'].median()
    results['max_transaction'] = charges['amount'].max()
    
    # 2. Spending by category
    category_spending = charges.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
    category_spending = category_spending.sort_values('sum', ascending=False)
    category_spending = category_spending.rename(columns={'sum': 'total_amount', 'count': 'transaction_count', 'mean': 'avg_amount'})
    results['spending_by_category'] = category_spending.to_dict('records')
    
    # Create pie chart of category spending
    plt.figure(figsize=(12, 8))
    top_categories = category_spending.head(8)
    remaining = pd.DataFrame({
        'category': ['Other'],
        'total_amount': [category_spending.iloc[8:]['total_amount'].sum() if len(category_spending) > 8 else 0],
        'transaction_count': [category_spending.iloc[8:]['transaction_count'].sum() if len(category_spending) > 8 else 0],
        'avg_amount': [0]
    })
    plot_data = pd.concat([top_categories, remaining])
    
    plt.pie(plot_data['total_amount'], labels=plot_data['category'], autopct='%1.1f%%', 
            startangle=90, shadow=False, wedgeprops={'edgecolor': 'white'})
    plt.axis('equal')
    plt.title('Spending by Category')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'spending_by_category_pie.png'))
    plt.close()
    
    # Bar chart of category spending
    plt.figure(figsize=(14, 8))
    sns.barplot(x='total_amount', y='category', data=category_spending.head(12))
    plt.title('Top Categories by Spending Amount')
    plt.xlabel('Total Amount ($)')
    plt.ylabel('Category')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'top_categories_bar.png'))
    plt.close()
    
    # 3. Top merchants
    charges.loc[:, 'merchant'] = charges['description'].apply(lambda x: x.split()[0] if pd.notna(x) and len(x.split()) > 0 else 'Unknown')
    merchant_spending = charges.groupby('merchant')['amount'].agg(['sum', 'count']).reset_index()
    merchant_spending = merchant_spending.sort_values('sum', ascending=False)
    results['top_merchants'] = merchant_spending.head(10).to_dict('records')
    
    # Bar chart of top merchants
    plt.figure(figsize=(14, 8))
    top_merchants = merchant_spending.head(15)
    sns.barplot(x='sum', y='merchant', data=top_merchants)
    plt.title('Top 15 Merchants by Spending')
    plt.xlabel('Total Amount ($)')
    plt.ylabel('Merchant')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'top_merchants_bar.png'))
    plt.close()
    
    # 3.5 Top 10 Transactions by Amount
    top_transactions = charges.sort_values('amount', ascending=False).head(10).copy()
    top_transactions['transaction_date'] = top_transactions['transaction_date'].dt.strftime('%Y-%m-%d')
    results['top_transactions'] = top_transactions[['transaction_date', 'description', 'amount', 'category', 'source']].to_dict('records')
    
    # Create bar chart of top transactions
    plt.figure(figsize=(14, 8))
    top_txn_plot = top_transactions.copy()
    # Truncate long descriptions for better display
    top_txn_plot['short_desc'] = top_txn_plot['description'].apply(lambda x: (x[:25] + '...') if len(x) > 25 else x)
    sns.barplot(x='amount', y='short_desc', data=top_txn_plot)
    plt.title('Top 10 Transactions by Amount')
    plt.xlabel('Amount ($)')
    plt.ylabel('Description')
    for i, row in enumerate(top_txn_plot.itertuples()):
        plt.text(row.amount + 10, i, f"${row.amount:.2f}", va='center')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'top_transactions.png'))
    plt.close()
    
    # 4. Spending over time
    charges.loc[:, 'day_of_week'] = charges['transaction_date'].dt.day_name()
    charges.loc[:, 'week'] = charges['transaction_date'].dt.isocalendar().week
    charges.loc[:, 'day_of_month'] = charges['transaction_date'].dt.day
    
    # Daily spending totals
    daily_spending = charges.groupby('transaction_date')['amount'].sum().reset_index()
    results['spending_by_day'] = daily_spending.to_dict('records')
    
    # Daily spending line chart
    plt.figure(figsize=(14, 6))
    plt.plot(daily_spending['transaction_date'], daily_spending['amount'], marker='o')
    plt.title('Daily Spending')
    plt.xlabel('Date')
    plt.ylabel('Total Amount ($)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'daily_spending.png'))
    plt.close()
    
    # Spending by day of week
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_spending = charges.groupby('day_of_week')['amount'].agg(['sum', 'count']).reindex(dow_order).reset_index()
    results['spending_by_weekday'] = day_spending.to_dict('records')
    
    # Weekday spending bar chart
    plt.figure(figsize=(10, 6))
    sns.barplot(x='day_of_week', y='sum', data=day_spending)
    plt.title('Spending by Day of Week')
    plt.xlabel('Day of Week')
    plt.ylabel('Total Amount ($)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'weekday_spending.png'))
    plt.close()
    
    # 5. Spending by account source
    source_spending = charges.groupby('source')['amount'].agg(['sum', 'count', 'mean']).reset_index()
    source_spending = source_spending.sort_values('sum', ascending=False)
    results['spending_by_source'] = source_spending.to_dict('records')
    
    # Source spending pie chart
    plt.figure(figsize=(10, 6))
    plt.pie(source_spending['sum'], labels=source_spending['source'], autopct='%1.1f%%', 
            startangle=90, shadow=False, wedgeprops={'edgecolor': 'white'})
    plt.axis('equal')
    plt.title('Spending by Account Source')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'source_spending_pie.png'))
    plt.close()
    
    # 6. Transaction size distribution
    plt.figure(figsize=(12, 6))
    sns.histplot(charges['amount'], bins=30, kde=True)
    plt.title('Distribution of Transaction Amounts')
    plt.xlabel('Transaction Amount ($)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'transaction_distribution.png'))
    plt.close()
    
    # 7. Day of month spending pattern
    day_of_month_spending = charges.groupby('day_of_month')['amount'].sum().reset_index()
    
    plt.figure(figsize=(14, 6))
    sns.barplot(x='day_of_month', y='amount', data=day_of_month_spending)
    plt.title('Spending by Day of Month')
    plt.xlabel('Day of Month')
    plt.ylabel('Total Amount ($)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'day_of_month_spending.png'))
    plt.close()
    
    # 8. Payment patterns analysis
    payments = transactions[transactions['transaction_type'].str.lower() == 'payment']
    payment_amounts = payments.groupby('transaction_date')['amount'].sum().abs().reset_index()
    
    if not payment_amounts.empty:
        plt.figure(figsize=(14, 6))
        plt.plot(payment_amounts['transaction_date'], payment_amounts['amount'], marker='o', color='green')
        plt.title('Payment Amounts Over Time')
        plt.xlabel('Date')
        plt.ylabel('Payment Amount ($)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'payment_patterns.png'))
        plt.close()
    
    return results

def print_spending_analysis(analysis_results):
    """
    Print a detailed report from the spending analysis results.
    
    Args:
        analysis_results (dict): Results from analyze_spending_habits
    """
    if not analysis_results:
        print("No analysis results to display.")
        return
    
    print("\n" + "="*80)
    print(" "*30 + "SPENDING ANALYSIS REPORT")
    print("="*80)
    
    print("\n## OVERVIEW ##")
    print(f"Total Transactions: {analysis_results['total_transactions']}")
    print(f"  - Charges: {analysis_results['total_charges']}")
    print(f"  - Payments: {analysis_results['total_payments']}")
    print(f"  - Refunds: {analysis_results['total_refunds']}")
    print(f"Total Spent: ${analysis_results['total_spent']:.2f}")
    print(f"Total Refunded: ${analysis_results['total_refunded']:.2f}")
    print(f"Net Spending: ${analysis_results['net_spending']:.2f}")
    print(f"Total Payments Made: ${analysis_results['total_payments_amount']:.2f}")
    
    print("\nTransaction Amounts:")
    print(f"  - Average: ${analysis_results['avg_transaction']:.2f}")
    print(f"  - Median: ${analysis_results['median_transaction']:.2f}")
    print(f"  - Largest: ${analysis_results['max_transaction']:.2f}")
    
    print("\n## TOP SPENDING CATEGORIES ##")
    for i, category in enumerate(analysis_results['spending_by_category'][:8], 1):
        print(f"{i}. {category['category']}: ${category['total_amount']:.2f} ({category['transaction_count']} transactions, avg ${category['avg_amount']:.2f})")
    
    print("\n## TOP MERCHANTS ##")
    for i, merchant in enumerate(analysis_results['top_merchants'][:10], 1):
        print(f"{i}. {merchant['merchant']}: ${merchant['sum']:.2f} ({merchant['count']} transactions)")
    
    # Add section for top 10 transactions
    print("\n## TOP 10 TRANSACTIONS ##")
    for i, txn in enumerate(analysis_results['top_transactions'], 1):
        print(f"{i}. {txn['transaction_date']} | {txn['description']} | ${txn['amount']:.2f} | {txn['category']} | {txn['source']}")
    
    print("\n## SPENDING BY DAY OF WEEK ##")
    for day in analysis_results['spending_by_weekday']:
        print(f"{day['day_of_week']}: ${day['sum']:.2f} ({day['count']} transactions)")
    
    print("\n## SPENDING BY ACCOUNT ##")
    for source in analysis_results['spending_by_source']:
        print(f"{source['source']}: ${source['sum']:.2f} ({source['count']} transactions, avg ${source['mean']:.2f})")
    
    print("\nVisual charts have been saved to the 'analysis_results' folder.")
    print("="*80)

def load_and_analyze_transactions(data_folder='data', csv_file='consolidated_transactions.csv'):
    """
    Load consolidated transactions and perform spending analysis.
    
    Args:
        data_folder (str): Path to the data folder
        csv_file (str): Name of the consolidated CSV file
        
    Returns:
        dict: Analysis results
    """
    file_path = os.path.join(data_folder, csv_file)
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return None
    
    print(f"Loading transactions from {file_path}...")
    
    # Perform spending analysis
    analysis_results = analyze_spending_habits(csv_file, data_folder)
    
    # Print detailed report
    print_spending_analysis(analysis_results)
    
    print(f"Analysis complete. Visual charts saved to 'analysis_results' folder.")
    
    return analysis_results

def main():
    """Main function to run the transaction consolidation and analysis process."""
    # Set data folder path
    data_folder = 'data'
    
    # Check if consolidated file exists already
    consolidated_file = 'consolidated_transactions.csv'
    consolidated_path = os.path.join(data_folder, consolidated_file)
    
    if not os.path.exists(consolidated_path):
        # Consolidate transactions if file doesn't exist
        print("Consolidated transactions file not found. Creating it...")
        transactions = consolidate_transactions(data_folder)
    else:
        print(f"Found existing consolidated file at {consolidated_path}")
        transactions = pd.read_csv(consolidated_path)
        transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Basic transaction analysis")
    print("2. Detailed spending habits analysis")
    print("3. Both")
    print("4. Regenerate consolidated file")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == '1' or choice == '3':
        # Perform basic analysis
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
    
    if choice == '2' or choice == '3':
        # Perform detailed spending habits analysis
        load_and_analyze_transactions(data_folder, consolidated_file)
    
    if choice == '4':
        # Regenerate consolidated file
        transactions = consolidate_transactions(data_folder)
        if transactions is not None:
            print("Consolidated file regenerated successfully.")

if __name__ == "__main__":
    main()
