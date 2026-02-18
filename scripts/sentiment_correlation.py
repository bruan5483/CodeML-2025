#!/usr/bin/env python3
"""
Analyze correlation between sentiment scores and actual price movements.

Calculates correlation between aggregated_score and actual price change
(actual_tomorrow_price - today_price) from price_predictions.csv.
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt


def calculate_sentiment_correlation(data_file: str):
    """
    Calculate correlation between sentiment and price movements.

    Args:
        data_file: Path to price_predictions.csv
    """
    print("="*80)
    print("SENTIMENT-PRICE CORRELATION ANALYSIS")
    print("="*80)

    # Load data
    print(f"\nLoading data from: {data_file}")
    df = pd.read_csv(data_file)

    # Drop rows with NaN values
    df = df.dropna(subset=['actual_tomorrow_price', 'aggregated_score'])

    print(f"Total rows loaded: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    # Calculate actual price movement
    df['actual_price_change'] = df['actual_tomorrow_price'] - df['today_price']

    # Extract variables
    sentiment = df['aggregated_score'].values
    price_change = df['actual_price_change'].values

    print("\n" + "="*80)
    print("DESCRIPTIVE STATISTICS")
    print("="*80)

    print("\nAggregated Sentiment Score:")
    print(f"  Mean: {sentiment.mean():.6f}")
    print(f"  Std Dev: {sentiment.std():.6f}")
    print(f"  Min: {sentiment.min():.6f}")
    print(f"  Max: {sentiment.max():.6f}")
    print(f"  Median: {np.median(sentiment):.6f}")

    print("\nActual Price Change:")
    print(f"  Mean: ${price_change.mean():.4f}")
    print(f"  Std Dev: ${price_change.std():.4f}")
    print(f"  Min: ${price_change.min():.4f}")
    print(f"  Max: ${price_change.max():.4f}")
    print(f"  Median: ${np.median(price_change):.4f}")

    print("\n" + "="*80)
    print("CORRELATION ANALYSIS")
    print("="*80)

    # Pearson correlation (linear relationship)
    pearson_corr, pearson_pval = stats.pearsonr(sentiment, price_change)
    print(f"\nPearson Correlation Coefficient: {pearson_corr:.6f}")
    print(f"P-value: {pearson_pval:.6e}")
    print(f"Significance: {'Significant' if pearson_pval < 0.05 else 'Not Significant'} (α=0.05)")

    # Spearman correlation (monotonic relationship, rank-based)
    spearman_corr, spearman_pval = stats.spearmanr(sentiment, price_change)
    print(f"\nSpearman Correlation Coefficient: {spearman_corr:.6f}")
    print(f"P-value: {spearman_pval:.6e}")
    print(f"Significance: {'Significant' if spearman_pval < 0.05 else 'Not Significant'} (α=0.05)")

    # Kendall's Tau (another rank-based correlation)
    kendall_corr, kendall_pval = stats.kendalltau(sentiment, price_change)
    print(f"\nKendall's Tau Coefficient: {kendall_corr:.6f}")
    print(f"P-value: {kendall_pval:.6e}")
    print(f"Significance: {'Significant' if kendall_pval < 0.05 else 'Not Significant'} (α=0.05)")

    print("\n" + "="*80)
    print("CORRELATION INTERPRETATION")
    print("="*80)

    # Interpret Pearson correlation strength
    abs_pearson = abs(pearson_corr)
    if abs_pearson < 0.1:
        strength = "Negligible"
    elif abs_pearson < 0.3:
        strength = "Weak"
    elif abs_pearson < 0.5:
        strength = "Moderate"
    elif abs_pearson < 0.7:
        strength = "Strong"
    else:
        strength = "Very Strong"

    direction = "positive" if pearson_corr > 0 else "negative"

    print(f"\nPearson Correlation Strength: {strength}")
    print(f"Direction: {direction}")
    print(f"\nInterpretation:")
    if abs_pearson < 0.1:
        print("  There is almost no linear relationship between sentiment and price change.")
    elif pearson_corr > 0:
        print("  Higher sentiment scores tend to be associated with larger price increases.")
    else:
        print("  Higher sentiment scores tend to be associated with larger price decreases.")

    print("\n" + "="*80)
    print("DIRECTIONAL ACCURACY")
    print("="*80)

    # Check if sentiment direction matches price change direction
    sentiment_direction = np.sign(sentiment)
    price_direction = np.sign(price_change)
    direction_matches = (sentiment_direction == price_direction)

    accuracy = direction_matches.sum() / len(direction_matches) * 100

    print(f"\nDirectional Accuracy: {accuracy:.2f}%")
    print(f"  (How often sentiment direction matches price movement direction)")

    # Break down by direction
    positive_sentiment = sentiment > 0
    negative_sentiment = sentiment < 0
    neutral_sentiment = sentiment == 0

    if positive_sentiment.sum() > 0:
        positive_accuracy = ((sentiment_direction[positive_sentiment] == price_direction[positive_sentiment]).sum() /
                            positive_sentiment.sum() * 100)
        print(f"\nPositive Sentiment Cases: {positive_sentiment.sum()}")
        print(f"  Accuracy: {positive_accuracy:.2f}%")
        print(f"  Avg Price Change: ${price_change[positive_sentiment].mean():.4f}")

    if negative_sentiment.sum() > 0:
        negative_accuracy = ((sentiment_direction[negative_sentiment] == price_direction[negative_sentiment]).sum() /
                            negative_sentiment.sum() * 100)
        print(f"\nNegative Sentiment Cases: {negative_sentiment.sum()}")
        print(f"  Accuracy: {negative_accuracy:.2f}%")
        print(f"  Avg Price Change: ${price_change[negative_sentiment].mean():.4f}")

    if neutral_sentiment.sum() > 0:
        print(f"\nNeutral Sentiment Cases: {neutral_sentiment.sum()}")
        print(f"  Avg Price Change: ${price_change[neutral_sentiment].mean():.4f}")

    print("\n" + "="*80)
    print("QUARTILE ANALYSIS")
    print("="*80)

    # Analyze price changes by sentiment quartiles
    sentiment_quartiles = pd.qcut(sentiment, q=4, labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'], duplicates='drop')

    print("\nAverage Price Change by Sentiment Quartile:")
    for quartile in sentiment_quartiles.unique():
        mask = sentiment_quartiles == quartile
        avg_change = price_change[mask].mean()
        count = mask.sum()
        print(f"  {quartile}: ${avg_change:.4f} (n={count})")

    print("\n" + "="*80)
    print("SAMPLE DATA")
    print("="*80)

    # Show some examples
    print("\nTop 10 Most Positive Sentiment Scores:")
    top_positive = df.nlargest(10, 'aggregated_score')[['today_news_date', 'aggregated_score', 'actual_price_change', 'today_price', 'actual_tomorrow_price']]
    print(top_positive.to_string(index=False))

    print("\nTop 10 Most Negative Sentiment Scores:")
    top_negative = df.nsmallest(10, 'aggregated_score')[['today_news_date', 'aggregated_score', 'actual_price_change', 'today_price', 'actual_tomorrow_price']]
    print(top_negative.to_string(index=False))

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print(f"""
Correlation Summary:
  - Pearson:  {pearson_corr:+.6f} ({strength} {direction} relationship)
  - Spearman: {spearman_corr:+.6f}
  - Kendall:  {kendall_corr:+.6f}

Directional Accuracy: {accuracy:.2f}%

Key Insight:
  {"Strong" if abs_pearson >= 0.5 else "Moderate" if abs_pearson >= 0.3 else "Weak"} correlation suggests that sentiment
  {"is a good" if abs_pearson >= 0.5 else "may be a useful" if abs_pearson >= 0.3 else "has limited"} predictor of price movements.
    """)

    return {
        'pearson': pearson_corr,
        'spearman': spearman_corr,
        'kendall': kendall_corr,
        'directional_accuracy': accuracy
    }


def main():
    """Main entry point"""
    data_file = "data/price_predictions.csv"
    results = calculate_sentiment_correlation(data_file)


if __name__ == "__main__":
    main()
