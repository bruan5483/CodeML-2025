#!/usr/bin/env python3
"""
Format price_predictions.csv to simplified format with date filtering.

Converts price predictions to a simple format with:
- id: Date in yyyy-mm-dd format
- price_usd_per_mmbtu: Predicted tomorrow price

Only includes dates from 2020-01-02 to 2025-09-22 (inclusive).
"""

import pandas as pd
from datetime import datetime


def format_price_predictions(input_file: str, output_file: str):
    """
    Format price predictions CSV to simplified format.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
    """
    # Define date range
    start_date = pd.Timestamp('2020-01-01')
    end_date = pd.Timestamp('2025-09-22')

    print(f"Reading from: {input_file}")

    # Read the CSV file
    df = pd.read_csv(input_file)

    print(f"Total rows loaded: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    # Convert today_news_date to datetime
    df['today_news_date'] = pd.to_datetime(df['today_news_date'])

    # Filter date range (2020-01-02 to 2025-09-22 inclusive)
    filtered_df = df[
        (df['today_news_date'] >= start_date) &
        (df['today_news_date'] <= end_date)
    ].copy()

    print(f"\nRows after date filtering ({start_date.date()} to {end_date.date()}): {len(filtered_df)}")

    # Sort by date to ensure proper ordering before shifting
    filtered_df = filtered_df.sort_values('today_news_date').reset_index(drop=True)

    # Shift to get next trading day (accounts for weekends/holidays)
    # predicted_tomorrow_price should be paired with the next date in sequence
    filtered_df['next_trading_date'] = filtered_df['today_news_date'].shift(-1)

    # Drop last row where next_trading_date is NaN
    filtered_df = filtered_df.dropna(subset=['next_trading_date'])

    print(f"Rows after shifting for trading days: {len(filtered_df)}")

    # Create new formatted DataFrame
    formatted_df = pd.DataFrame({
        'id': filtered_df['next_trading_date'].dt.strftime('%Y-%m-%d'),
        'price_usd_per_mmbtu': filtered_df['predicted_tomorrow_price']
    })

    # Sort by date
    formatted_df = formatted_df.sort_values('id')

    # Save to CSV
    formatted_df.to_csv(output_file, index=False)

    print(f"\n{'='*60}")
    print(f"Formatted CSV saved to: {output_file}")
    print(f"Total rows saved: {len(formatted_df)}")
    print(f"{'='*60}")

    # Display sample
    print(f"\nFirst 10 rows:")
    print(formatted_df.head(10).to_string(index=False))

    print(f"\nLast 10 rows:")
    print(formatted_df.tail(10).to_string(index=False))

    # Display date range in output
    print(f"\nDate range in output:")
    print(f"  Start: {formatted_df['id'].min()}")
    print(f"  End: {formatted_df['id'].max()}")


def main():
    """Main entry point"""
    input_file = "data/price_predictions.csv"
    output_file = "data/price_predictions_formatted.csv"

    format_price_predictions(input_file, output_file)


if __name__ == "__main__":
    main()
