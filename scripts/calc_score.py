#!/usr/bin/env python3
"""
Calculate evaluation scores for price predictions.

Compares predictions from price_predictions_formatted.csv against
actual prices from DHHNGSP.csv and calculates MAE, RMSE, and performance score.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def calculate_scores(predictions_file: str, actual_prices_file: str):
    """
    Calculate evaluation scores by comparing predictions with actual prices.

    Args:
        predictions_file: Path to formatted predictions CSV
        actual_prices_file: Path to actual prices CSV (DHHNGSP.csv)
    """

    # Load predictions
    predictions_df = pd.read_csv(predictions_file)

    # Load actual prices
    actual_df = pd.read_csv(actual_prices_file)

    # Convert dates to datetime
    predictions_df['id'] = pd.to_datetime(predictions_df['id'])
    actual_df['observation_date'] = pd.to_datetime(actual_df['observation_date'])

    # Convert DHHNGSP to numeric, handling any non-numeric values
    actual_df['DHHNGSP'] = pd.to_numeric(actual_df['DHHNGSP'], errors='coerce')

    # Sort actual prices by date to ensure correct ordering
    actual_df = actual_df.sort_values('observation_date').reset_index(drop=True)

    # Merge predictions with actual prices
    # The prediction id is already the date for which the price is predicted
    # So we directly match prediction id with observation_date
    merged_df = pd.merge(
        predictions_df,
        actual_df,
        left_on='id',
        right_on='observation_date',
        how='inner'
    )

    original_rows = len(merged_df)

    print(f"Rows after merge: {original_rows}")

    # Drop rows where actual price is NaN
    merged_df = merged_df.dropna(subset=['DHHNGSP'])
    print(f"Rows after removing NaN actual prices: {len(merged_df)}")
    print(f"Rows removed: {original_rows - len(merged_df)}")

    # Calculate MAE and RMSE
    # Compare predictions with actual prices
    mae = mean_absolute_error(merged_df['DHHNGSP'], merged_df['price_usd_per_mmbtu'])
    rmse = np.sqrt(mean_squared_error(merged_df['DHHNGSP'], merged_df['price_usd_per_mmbtu']))

    print(f"\nMean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"Performance Score: {100 / (1 + rmse):.2f}")
    print("="*60)

def main():
    """Main entry point"""
    predictions_file = "data/price_predictions_formatted.csv"
    actual_prices_file = "data/DHHNGSP.csv"

    calculate_scores(predictions_file, actual_prices_file)


if __name__ == "__main__":
    main()
