#!/usr/bin/env python3
"""
Convert Qwen3 prediction results to submission format.

Input: ./data/qwen3_predictions.csv
Output: ./data/qwen3_predictions_formatted.csv

Format:
- id: Date from the prediction (YYYY-MM-DD format)
- price_usd_per_mmbtu: Predicted next day price
"""

import pandas as pd
import sys
from pathlib import Path

# Configuration
INPUT_FILE = "./data/qwen3_predictions.csv"
OUTPUT_FILE = "./data/qwen3_predictions_formatted.csv"
TEST_TEMPLATE_FILE = "./data/test-template.csv"
PRICE_DATA_FILE = "./data/DHHNGSP.csv"

def convert_predictions(input_path: str, output_path: str):
    """
    Convert predictions to required format.

    Args:
        input_path: Path to input CSV with predictions
        output_path: Path to save formatted output
    """
    print("="*80)
    print("QWEN3 PREDICTIONS CONVERTER")
    print("="*80)

    # Track missing dates statistics
    total_missing_dates = 0
    total_filled_dates = 0

    # Check if input file exists
    if not Path(input_path).exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    # Load predictions
    print(f"\nLoading predictions from: {input_path}")
    df = pd.read_csv(input_path)
    print(f"✓ Loaded {len(df)} predictions")

    # Display input columns
    print(f"\nInput columns: {df.columns.tolist()}")

    # Validate required columns exist
    if 'predicted_next_price' not in df.columns:
        print(f"ERROR: 'predicted_next_price' column not found in input file")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)

    if 'date' not in df.columns:
        print(f"ERROR: 'date' column not found in input file")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)

    # IMPORTANT: The 'date' column represents the day the prediction was made
    # The 'predicted_next_price' is for the NEXT trading day
    # We need to shift dates forward by one trading day
    print(f"\nShifting dates by one trading day...")
    print(f"  Note: 'predicted_next_price' on date X becomes the price for date X+1 trading day")

    # Sort by date first
    df = df.sort_values('date').reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])

    # Shift dates forward by one position (next trading day)
    # This aligns the predicted_next_price with the correct date
    df['next_trading_date'] = df['date'].shift(-1)

    # Remove the last row (has no next trading date)
    df = df[:-1].copy()

    print(f"✓ Shifted {len(df)} predictions to align with correct dates")

    # Create formatted output
    print(f"\nFormatting output...")
    formatted_df = pd.DataFrame({
        'id': df['next_trading_date'].dt.strftime('%Y-%m-%d'),
        'price_usd_per_mmbtu': df['predicted_next_price'].values
    })

    # Sort by date
    print(f"Sorting by date...")
    formatted_df = formatted_df.sort_values('id').reset_index(drop=True)

    # Load test template to check for missing dates
    print(f"\n{'='*80}")
    print("CHECKING FOR MISSING DATES")
    print(f"{'='*80}")

    if Path(TEST_TEMPLATE_FILE).exists():
        print(f"\nLoading test template from: {TEST_TEMPLATE_FILE}")
        template_df = pd.read_csv(TEST_TEMPLATE_FILE)
        print(f"✓ Loaded {len(template_df)} required dates")

        # Get required dates
        required_dates = set(template_df['id'].astype(str))
        existing_dates = set(formatted_df['id'].astype(str))
        missing_dates = required_dates - existing_dates

        if missing_dates:
            total_missing_dates = len(missing_dates)
            print(f"\n⚠ Found {total_missing_dates} missing dates (not in predictions)")
            print(f"Missing dates: {sorted(list(missing_dates))[:10]}{'...' if len(missing_dates) > 10 else ''}")
            print(f"\nNote: These dates will be filled using DHHNGSP.csv (previous day's price)")

            # Load price data
            if Path(PRICE_DATA_FILE).exists():
                print(f"\nLoading price data from: {PRICE_DATA_FILE}")
                prices_df = pd.read_csv(PRICE_DATA_FILE)
                prices_df['observation_date'] = pd.to_datetime(prices_df['observation_date'])
                prices_df = prices_df.sort_values('observation_date')
                print(f"✓ Loaded {len(prices_df)} price records")

                # Create price lookup dictionary with datetime objects
                price_dict = dict(zip(prices_df['observation_date'], prices_df['DHHNGSP']))

                # Fill missing dates
                print(f"\nFilling missing dates with previous day prices...")
                missing_rows = []
                filled_count = 0
                unfilled_count = 0

                for missing_date_str in sorted(missing_dates):
                    # Convert missing date to datetime
                    missing_date = pd.to_datetime(missing_date_str)

                    # Look for previous day's price, going back up to 30 days if needed
                    # Skip null/zero values
                    price_found = False
                    for days_back in range(1, 31):
                        prev_date = missing_date - pd.Timedelta(days=days_back)
                        if prev_date in price_dict:
                            price_value = price_dict[prev_date]
                            # Check if price is valid (not null and not zero)
                            if pd.notna(price_value) and price_value != 0:
                                missing_rows.append({
                                    'id': missing_date_str,
                                    'price_usd_per_mmbtu': price_value
                                })
                                filled_count += 1
                                price_found = True
                                if days_back >= 1:
                                    print(f"  → {missing_date_str}: using price ${price_value:.2f} from {days_back} days earlier ({prev_date.strftime('%Y-%m-%d')})")
                                break
                            # else: continue to next day back (skip null/zero values)

                    if not price_found:
                        print(f"  ⚠ Warning: No valid price found for {missing_date_str} (checked 30 days back)")
                        unfilled_count += 1

                if missing_rows:
                    # Append missing rows
                    missing_df = pd.DataFrame(missing_rows)
                    formatted_df = pd.concat([formatted_df, missing_df], ignore_index=True)

                    # Re-sort by date
                    formatted_df = formatted_df.sort_values('id').reset_index(drop=True)

                    total_filled_dates = filled_count
                    print(f"✓ Filled {filled_count} missing dates")
                    if unfilled_count > 0:
                        print(f"⚠ Could not fill {unfilled_count} dates (no price data available)")
            else:
                print(f"⚠ Warning: Price data file not found: {PRICE_DATA_FILE}")
                print(f"Cannot fill missing dates")
        else:
            print(f"\n✓ All required dates are present")
    else:
        print(f"\n⚠ Warning: Test template not found: {TEST_TEMPLATE_FILE}")
        print(f"Skipping missing date check")

    # Display sample
    print(f"\n{'='*80}")
    print("FORMATTED OUTPUT SAMPLE")
    print(f"{'='*80}")
    print(f"\nFirst 5 rows:")
    print(formatted_df.head().to_string(index=False))
    print(f"\nLast 5 rows:")
    print(formatted_df.tail().to_string(index=False))

    # Save output
    print(f"\nSaving formatted predictions to: {output_path}")

    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    formatted_df.to_csv(output_path, index=False)
    print(f"✓ Saved {len(formatted_df)} predictions")

    # Verification
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print(f"{'='*80}")
    verification_df = pd.read_csv(output_path)
    print(f"  Rows: {len(verification_df)}")
    print(f"  Columns: {verification_df.columns.tolist()}")
    print(f"  Date range: {verification_df['id'].min()} to {verification_df['id'].max()}")
    print(f"  Price range: ${verification_df['price_usd_per_mmbtu'].min():.2f} - ${verification_df['price_usd_per_mmbtu'].max():.2f}")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"  Total predictions saved: {len(verification_df)}")
    if total_missing_dates > 0:
        print(f"  Missing dates found: {total_missing_dates}")
        print(f"  Missing dates filled: {total_filled_dates}")
        if total_missing_dates > total_filled_dates:
            print(f"  Missing dates NOT filled: {total_missing_dates - total_filled_dates}")
    else:
        print(f"  Missing dates: 0 (all dates present)")

    print(f"\n{'='*80}")
    print("CONVERSION COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    # Check if custom paths provided via command line
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    output_file = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE

    print(f"\nConfiguration:")
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_file}")

    convert_predictions(input_file, output_file)
