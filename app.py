#!/usr/bin/env python3
"""
Transaction Data Analysis Web Application

A Flask-based web interface for analyzing and visualizing transaction data.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
from data_eda import analyze_transactions
from trx_consolidation import consolidate_transactions

app = Flask(__name__)

# Configuration
DATA_FOLDER = 'data'
ANALYSIS_FOLDER = 'static/analysis_results'
TRANSACTION_FILE = 'consolidated_transactions.csv'

@app.route('/')
def index():
    """Render the main dashboard page."""
    # Ensure transaction data exists
    ensure_transaction_data()
    
    # Calculate default date range (previous month)
    today = datetime.date.today()
    first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
    last_day_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
    
    # Format dates as strings for form values
    default_start_date = first_day_prev_month.strftime('%Y-%m-%d')
    default_end_date = last_day_prev_month.strftime('%Y-%m-%d')
    
    # Get date filters from request, defaulting to previous month
    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)
    
    # Get transaction data
    transactions = load_transactions()
    
    # Apply date filters
    filtered_transactions = transactions.copy()
    if start_date:
        filtered_transactions = filtered_transactions[filtered_transactions['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        filtered_transactions = filtered_transactions[filtered_transactions['transaction_date'] <= pd.to_datetime(end_date)]
    
    # Perform basic analysis for the dashboard
    analysis = analyze_transactions(filtered_transactions)
    
    # Get counts by transaction type
    txn_counts = {
        'charges': filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'charge'].shape[0],
        'payments': filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'payment'].shape[0],
        'refunds': filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'refund'].shape[0]
    }
    
    # Get financial summary
    total_spent = filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'charge']['amount'].sum()
    total_refunded = filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'refund']['amount'].abs().sum()
    total_paid = filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'payment']['amount'].abs().sum()
    
    # Get top 5 categories
    charges = filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'charge']
    top_categories = charges.groupby('category')['amount'].sum().sort_values(ascending=False).head(5).to_dict()
    
    # Create date range string and date filter object
    date_range = f"{start_date} to {end_date}"
    date_filter = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': date_range
    }
    
    return render_template('index.html',
                          txn_counts=txn_counts,
                          total_spent=total_spent,
                          total_refunded=total_refunded,
                          total_paid=total_paid,
                          net_spending=total_spent - total_refunded,
                          top_categories=top_categories,
                          date_range=date_range,
                          date_filter=date_filter)

@app.route('/analyze')
def analyze():
    """Generate and display detailed spending analysis."""
    # Ensure transaction data exists
    ensure_transaction_data()
    
    # Load transaction data
    transactions = load_transactions()
    
    # Filter to only include charges for spending analysis
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
    
    # 3. Top merchants
    charges.loc[:, 'merchant'] = charges['description'].apply(lambda x: x.split()[0] if pd.notna(x) and len(x.split()) > 0 else 'Unknown')
    merchant_spending = charges.groupby('merchant')['amount'].agg(['sum', 'count']).reset_index()
    merchant_spending = merchant_spending.sort_values('sum', ascending=False)
    results['top_merchants'] = merchant_spending.head(15).to_dict('records')
    
    # 3.5 Top 10 Transactions by Amount
    top_transactions = charges.sort_values('amount', ascending=False).head(10).copy()
    top_transactions['transaction_date'] = top_transactions['transaction_date'].dt.strftime('%Y-%m-%d')
    results['top_transactions'] = top_transactions[['transaction_date', 'description', 'amount', 'category', 'source']].to_dict('records')
    
    # 4. Spending over time
    charges.loc[:, 'day_of_week'] = charges['transaction_date'].dt.day_name()
    charges.loc[:, 'week'] = charges['transaction_date'].dt.isocalendar().week
    charges.loc[:, 'day_of_month'] = charges['transaction_date'].dt.day
    
    # Daily spending totals
    daily_spending = charges.groupby(charges['transaction_date'].dt.date)['amount'].sum().reset_index()
    daily_spending['transaction_date'] = daily_spending['transaction_date'].astype(str)
    results['daily_spending'] = daily_spending.to_dict('records')
    
    # Spending by day of week
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_spending = charges.groupby('day_of_week')['amount'].agg(['sum', 'count']).reindex(dow_order).reset_index()
    results['spending_by_weekday'] = day_spending.to_dict('records')
    
    # 5. Spending by account source
    source_spending = charges.groupby('source')['amount'].agg(['sum', 'count', 'mean']).reset_index()
    source_spending = source_spending.sort_values('sum', ascending=False)
    results['spending_by_source'] = source_spending.to_dict('records')
    
    # 6. Transaction size distribution
    bin_edges = np.histogram_bin_edges(charges['amount'], bins=20)
    hist, _ = np.histogram(charges['amount'], bins=bin_edges)
    results['transaction_distribution'] = {
        'counts': hist.tolist(),
        'bin_labels': [f"${edge:.0f}" for edge in bin_edges[:-1]]
    }
    
    return render_template('analysis.html', analysis=results)

@app.route('/categories')
def categories():
    """Display spending breakdown by category."""
    transactions = load_transactions()
    
    # Calculate default date range (previous month)
    today = datetime.date.today()
    first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
    last_day_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
    
    # Format dates as strings for form values
    default_start_date = first_day_prev_month.strftime('%Y-%m-%d')
    default_end_date = last_day_prev_month.strftime('%Y-%m-%d')
    
    # Get date filters from request, defaulting to previous month
    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)
    
    # Filter transactions by date
    filtered_transactions = transactions.copy()
    if start_date:
        filtered_transactions = filtered_transactions[filtered_transactions['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        filtered_transactions = filtered_transactions[filtered_transactions['transaction_date'] <= pd.to_datetime(end_date)]
    
    charges = filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'charge']
    
    # Get spending by category
    category_data = charges.groupby('category').agg({
        'amount': ['sum', 'count', 'mean'],
        'transaction_date': ['min', 'max']
    })
    
    category_data.columns = ['total', 'count', 'average', 'first_date', 'last_date']
    category_data = category_data.sort_values('total', ascending=False).reset_index()
    
    # Convert to dictionary for template
    categories_list = []
    for _, row in category_data.iterrows():
        categories_list.append({
            'name': row['category'],
            'total': row['total'],
            'count': row['count'],
            'average': row['average'],
            'first_date': row['first_date'].strftime('%Y-%m-%d'),
            'last_date': row['last_date'].strftime('%Y-%m-%d')
        })
    
    # Date range information for template
    date_filter = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date} to {end_date}"
    }
    
    return render_template('categories.html', 
                          categories=categories_list, 
                          date_filter=date_filter)

@app.route('/merchants')
def merchants():
    """Display spending breakdown by merchant."""
    transactions = load_transactions()
    
    # Calculate default date range (previous month)
    today = datetime.date.today()
    first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
    last_day_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
    
    # Format dates as strings for form values
    default_start_date = first_day_prev_month.strftime('%Y-%m-%d')
    default_end_date = last_day_prev_month.strftime('%Y-%m-%d')
    
    # Get date filters from request, defaulting to previous month
    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)
    
    # Filter transactions by date
    filtered_transactions = transactions.copy()
    if start_date:
        filtered_transactions = filtered_transactions[filtered_transactions['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        filtered_transactions = filtered_transactions[filtered_transactions['transaction_date'] <= pd.to_datetime(end_date)]
    
    charges = filtered_transactions[filtered_transactions['transaction_type'].str.lower() == 'charge'].copy()
    
    # Extract merchant name (first word of description)
    charges.loc[:, 'merchant'] = charges['description'].apply(
        lambda x: x.split()[0] if pd.notna(x) and len(x.split()) > 0 else 'Unknown'
    )
    
    # Get spending by merchant
    merchant_data = charges.groupby('merchant').agg({
        'amount': ['sum', 'count', 'mean'],
        'transaction_date': ['min', 'max']
    })
    
    merchant_data.columns = ['total', 'count', 'average', 'first_date', 'last_date']
    merchant_data = merchant_data.sort_values('total', ascending=False).reset_index()
    
    # Convert to dictionary for template
    merchants_list = []
    for _, row in merchant_data.iterrows():
        merchants_list.append({
            'name': row['merchant'],
            'total': row['total'],
            'count': row['count'],
            'average': row['average'],
            'first_date': row['first_date'].strftime('%Y-%m-%d'),
            'last_date': row['last_date'].strftime('%Y-%m-%d')
        })
    
    # Date range information for template
    date_filter = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date} to {end_date}"
    }
    
    return render_template('merchants.html', 
                          merchants=merchants_list,
                          date_filter=date_filter)

@app.route('/transactions')
def transactions():
    """Display all transactions with filtering capability."""
    transactions_df = load_transactions()
    
    # Calculate default date range (previous month)
    today = datetime.date.today()
    first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
    last_day_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
    
    # Format dates as strings for form values
    default_start_date = first_day_prev_month.strftime('%Y-%m-%d')
    default_end_date = last_day_prev_month.strftime('%Y-%m-%d')
    
    # Get date filters from request, defaulting to previous month
    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)
    
    # Apply filters if provided
    txn_type = request.args.get('type')
    category = request.args.get('category')
    source = request.args.get('source')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    filtered_df = transactions_df.copy()
    
    # Apply date filters
    if start_date:
        filtered_df = filtered_df[filtered_df['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        filtered_df = filtered_df[filtered_df['transaction_date'] <= pd.to_datetime(end_date)]
    
    if txn_type:
        filtered_df = filtered_df[filtered_df['transaction_type'].str.lower() == txn_type.lower()]
    
    if category:
        filtered_df = filtered_df[filtered_df['category'] == category]
    
    if source:
        filtered_df = filtered_df[filtered_df['source'] == source]
    
    if min_amount:
        filtered_df = filtered_df[filtered_df['amount'] >= float(min_amount)]
    
    if max_amount:
        filtered_df = filtered_df[filtered_df['amount'] <= float(max_amount)]
    
    # Sort by amount descending instead of date
    filtered_df = filtered_df.sort_values('amount', ascending=False)
    
    # Convert to list of dictionaries for template
    transactions_list = []
    for _, row in filtered_df.iterrows():
        transactions_list.append({
            'date': row['transaction_date'].strftime('%Y-%m-%d'),
            'description': row['description'],
            'amount': row['amount'],
            'category': row['category'] if pd.notna(row['category']) else '',
            'source': row['source'],
            'type': row['transaction_type']
        })
    
    # Get unique values for filters
    filter_options = {
        'categories': transactions_df['category'].dropna().unique().tolist(),
        'sources': transactions_df['source'].unique().tolist(),
        'types': ['charge', 'payment', 'refund'],
        'start_date': start_date,
        'end_date': end_date
    }
    
    # Get date range for display
    date_range = f"{start_date} to {end_date}"
    
    return render_template('transactions.html', 
                          transactions=transactions_list, 
                          filter_options=filter_options,
                          date_range=date_range,
                          count=len(transactions_list))

@app.route('/deep-dive/<category>')
def deep_dive_category(category):
    """Perform a deep-dive analysis on a specific category."""
    transactions = load_transactions()
    charges = transactions[transactions['transaction_type'].str.lower() == 'charge'].copy()
    
    # Calculate default date range (previous month)
    today = datetime.date.today()
    first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
    last_day_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
    
    # Format dates as strings for form values
    default_start_date = first_day_prev_month.strftime('%Y-%m-%d')
    default_end_date = last_day_prev_month.strftime('%Y-%m-%d')
    
    # Get date filters from request, defaulting to previous month
    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)
    
    # Apply date filters
    if start_date:
        charges = charges[charges['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        charges = charges[charges['transaction_date'] <= pd.to_datetime(end_date)]
    
    # Filter to the requested category
    category_txns = charges[charges['category'] == category].copy()
    
    if category_txns.empty:
        return render_template('error.html', message=f"No transactions found for category: {category}")
    
    # Summary statistics
    summary = {
        'total_spent': category_txns['amount'].sum(),
        'transaction_count': len(category_txns),
        'average_amount': category_txns['amount'].mean(),
        'largest_transaction': category_txns['amount'].max(),
        'first_transaction': category_txns['transaction_date'].min().strftime('%Y-%m-%d'),
        'last_transaction': category_txns['transaction_date'].max().strftime('%Y-%m-%d')
    }
    
    # Get transactions sorted by amount descending
    txns = []
    for _, row in category_txns.sort_values('amount', ascending=False).iterrows():
        txns.append({
            'date': row['transaction_date'].strftime('%Y-%m-%d'),
            'description': row['description'],
            'amount': row['amount'],
            'source': row['source']
        })
    
    # Get spending by source for this category
    by_source = category_txns.groupby('source')['amount'].sum().sort_values(ascending=False).to_dict()
    
    # Get time series data
    time_data = category_txns.groupby(category_txns['transaction_date'].dt.date)['amount'].sum()
    
    # Format time series data for chart.js
    time_series_data = {
        'labels': [date.strftime('%Y-%m-%d') for date in time_data.index],
        'values': time_data.values.tolist()
    }
    
    # Date range information for template
    date_filter = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date} to {end_date}"
    }
    
    return render_template('deep_dive_category.html', 
                          category=category,
                          summary=summary,
                          transactions=txns,
                          by_source=by_source,
                          time_series_data=time_series_data,
                          date_filter=date_filter)

@app.route('/deep-dive/merchant/<merchant>')
def deep_dive_merchant(merchant):
    """Perform a deep-dive analysis on a specific merchant."""
    transactions = load_transactions()
    charges = transactions[transactions['transaction_type'].str.lower() == 'charge'].copy()
    
    # Calculate default date range (previous month)
    today = datetime.date.today()
    first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
    last_day_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
    
    # Format dates as strings for form values
    default_start_date = first_day_prev_month.strftime('%Y-%m-%d')
    default_end_date = last_day_prev_month.strftime('%Y-%m-%d')
    
    # Get date filters from request, defaulting to previous month
    start_date = request.args.get('start_date', default_start_date)
    end_date = request.args.get('end_date', default_end_date)
    
    # Apply date filters
    if start_date:
        charges = charges[charges['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        charges = charges[charges['transaction_date'] <= pd.to_datetime(end_date)]
    
    # Extract merchant name (first word of description)
    charges.loc[:, 'merchant'] = charges['description'].apply(
        lambda x: x.split()[0] if pd.notna(x) and len(x.split()) > 0 else 'Unknown'
    )
    
    # Filter by merchant
    merchant_txns = charges[charges['merchant'] == merchant].copy()
    
    if merchant_txns.empty:
        return render_template('error.html', message=f"No transactions found for merchant: {merchant}")
    
    # Summary statistics
    summary = {
        'total_spent': merchant_txns['amount'].sum(),
        'transaction_count': len(merchant_txns),
        'average_amount': merchant_txns['amount'].mean(),
        'largest_transaction': merchant_txns['amount'].max(),
        'smallest_transaction': merchant_txns['amount'].min(),
        'first_transaction': merchant_txns['transaction_date'].min().strftime('%Y-%m-%d'),
        'last_transaction': merchant_txns['transaction_date'].max().strftime('%Y-%m-%d')
    }
    
    # Get transactions sorted by amount descending
    txns = []
    for _, row in merchant_txns.sort_values('amount', ascending=False).iterrows():
        txns.append({
            'date': row['transaction_date'].strftime('%Y-%m-%d'),
            'description': row['description'],
            'amount': row['amount'],
            'category': row['category'] if pd.notna(row['category']) else '',
            'source': row['source']
        })
    
    # Get spending by category for this merchant
    by_category = merchant_txns.groupby('category')['amount'].sum().sort_values(ascending=False).to_dict()
    
    # Get time series data
    time_data = merchant_txns.groupby(merchant_txns['transaction_date'].dt.date)['amount'].sum()
    
    # Format time series data for chart.js
    time_series_data = {
        'labels': [date.strftime('%Y-%m-%d') for date in time_data.index],
        'values': time_data.values.tolist()
    }
    
    # Date range information for template
    date_filter = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date} to {end_date}"
    }
    
    return render_template('deep_dive_merchant.html', 
                          merchant=merchant,
                          summary=summary,
                          transactions=txns,
                          by_category=by_category,
                          time_series_data=time_series_data,
                          date_filter=date_filter)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/api/data')
def api_data():
    """API endpoint for getting transaction data in JSON format."""
    transactions = load_transactions()
    
    # Apply filters
    txn_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if txn_type:
        transactions = transactions[transactions['transaction_type'].str.lower() == txn_type.lower()]
    
    if category:
        transactions = transactions[transactions['category'] == category]
    
    # Apply date filters
    if start_date:
        transactions = transactions[transactions['transaction_date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        transactions = transactions[transactions['transaction_date'] <= pd.to_datetime(end_date)]
    
    # Convert dates to strings for JSON serialization
    transactions['transaction_date'] = transactions['transaction_date'].dt.strftime('%Y-%m-%d')
    if 'post_date' in transactions.columns:
        transactions['post_date'] = transactions['post_date'].apply(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None
        )
    
    return jsonify(transactions.to_dict(orient='records'))

def ensure_transaction_data():
    """Ensure transaction data exists, consolidate if needed."""
    file_path = os.path.join(DATA_FOLDER, TRANSACTION_FILE)
    if not os.path.exists(file_path):
        print(f"Consolidated transaction file not found. Creating it...")
        consolidate_transactions(DATA_FOLDER, TRANSACTION_FILE)

def load_transactions():
    """Load transaction data from the consolidated CSV file."""
    file_path = os.path.join(DATA_FOLDER, TRANSACTION_FILE)
    transactions = pd.read_csv(file_path)
    transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])
    if 'post_date' in transactions.columns:
        transactions['post_date'] = pd.to_datetime(transactions['post_date'], errors='coerce')
    return transactions

# Create necessary folders
def create_necessary_folders():
    """Create necessary folders for the application."""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(ANALYSIS_FOLDER, exist_ok=True)

# Add missing import for numpy
import numpy as np

if __name__ == '__main__':
    create_necessary_folders()
    app.run(debug=True, port=5001) 