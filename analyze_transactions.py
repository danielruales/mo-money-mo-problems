import pandas as pd

# Read the CSV file
df = pd.read_csv('data/consolidated_transactions_enriched.csv')

# Group by source and transaction_type together and get counts
grouped = df.groupby(['account_type', 'transaction_type']).size().reset_index(name='count')

# Sort by count in descending order
grouped = grouped.sort_values(['account_type', 'count'], ascending=False)

print('\nTransaction Counts by Account Type and Transaction Type Combined:')
print(grouped)

print('\nTotal counts by transaction type:')
print(df['transaction_type'].value_counts()) 