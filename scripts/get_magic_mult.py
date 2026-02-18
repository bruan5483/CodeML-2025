#!/usr/bin/env python3
"""
Find optimal magic multiplier for price prediction formula.

Formula: predicted_price = today_price + (aggregated_score * abs(aggregated_score) * magic)

Uses various optimization techniques to find the magic value that minimizes
the difference between predictions and actual_tomorrow_price.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.optimize import minimize_scalar, minimize


def calculate_prediction(today_price, aggregated_score, magic):
    """Calculate prediction using the formula."""
    return today_price + (aggregated_score * np.abs(aggregated_score) * magic)


def objective_function(magic, today_prices, aggregated_scores, actual_prices):
    """
    Objective function to minimize (RMSE).

    Args:
        magic: The magic multiplier value
        today_prices: Array of today's prices
        aggregated_scores: Array of aggregated sentiment scores
        actual_prices: Array of actual tomorrow prices

    Returns:
        RMSE between predictions and actual prices
    """
    predictions = calculate_prediction(today_prices, aggregated_scores, magic)
    rmse = np.sqrt(mean_squared_error(actual_prices, predictions))
    return rmse


def find_magic_multiplier(data_file: str):
    """
    Find optimal magic multiplier using various methods.

    Args:
        data_file: Path to price_predictions.csv
    """
    print("="*80)
    print("MAGIC MULTIPLIER OPTIMIZATION")
    print("="*80)

    # Load data
    print(f"\nLoading data from: {data_file}")
    df = pd.read_csv(data_file)

    # Drop rows with NaN in actual_tomorrow_price
    df = df.dropna(subset=['actual_tomorrow_price'])

    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    # Extract data
    today_prices = df['today_price'].values
    aggregated_scores = df['aggregated_score'].values
    actual_prices = df['actual_tomorrow_price'].values

    # Create feature for regression: aggregated_score * abs(aggregated_score)
    X = (aggregated_scores * np.abs(aggregated_scores)).reshape(-1, 1)

    # Target is the price change: actual_tomorrow_price - today_price
    y = actual_prices - today_prices

    print("\n" + "="*80)
    print("METHOD 1: LINEAR REGRESSION (No Intercept)")
    print("="*80)

    # Linear regression without intercept (force through origin)
    lr = LinearRegression(fit_intercept=False)
    lr.fit(X, y)
    magic_lr = lr.coef_[0]

    predictions_lr = calculate_prediction(today_prices, aggregated_scores, magic_lr)
    mae_lr = mean_absolute_error(actual_prices, predictions_lr)
    rmse_lr = np.sqrt(mean_squared_error(actual_prices, predictions_lr))

    print(f"Magic multiplier (Linear Regression): {magic_lr:.6f}")
    print(f"MAE: {mae_lr:.4f}")
    print(f"RMSE: {rmse_lr:.4f}")
    print(f"Performance Score: {100 / (1 + rmse_lr):.2f}")

    print("\n" + "="*80)
    print("METHOD 2: RIDGE REGRESSION (No Intercept)")
    print("="*80)

    # Ridge regression (L2 regularization)
    ridge = Ridge(alpha=1.0, fit_intercept=False)
    ridge.fit(X, y)
    magic_ridge = ridge.coef_[0]

    predictions_ridge = calculate_prediction(today_prices, aggregated_scores, magic_ridge)
    mae_ridge = mean_absolute_error(actual_prices, predictions_ridge)
    rmse_ridge = np.sqrt(mean_squared_error(actual_prices, predictions_ridge))

    print(f"Magic multiplier (Ridge): {magic_ridge:.6f}")
    print(f"MAE: {mae_ridge:.4f}")
    print(f"RMSE: {rmse_ridge:.4f}")
    print(f"Performance Score: {100 / (1 + rmse_ridge):.2f}")

    print("\n" + "="*80)
    print("METHOD 3: LASSO REGRESSION (No Intercept)")
    print("="*80)

    # Lasso regression (L1 regularization)
    lasso = Lasso(alpha=0.1, fit_intercept=False)
    lasso.fit(X, y)
    magic_lasso = lasso.coef_[0]

    predictions_lasso = calculate_prediction(today_prices, aggregated_scores, magic_lasso)
    mae_lasso = mean_absolute_error(actual_prices, predictions_lasso)
    rmse_lasso = np.sqrt(mean_squared_error(actual_prices, predictions_lasso))

    print(f"Magic multiplier (Lasso): {magic_lasso:.6f}")
    print(f"MAE: {mae_lasso:.4f}")
    print(f"RMSE: {rmse_lasso:.4f}")
    print(f"Performance Score: {100 / (1 + rmse_lasso):.2f}")

    print("\n" + "="*80)
    print("METHOD 4: SCIPY OPTIMIZATION (Minimize RMSE)")
    print("="*80)

    # Direct optimization to minimize RMSE
    result = minimize_scalar(
        lambda m: objective_function(m, today_prices, aggregated_scores, actual_prices),
        bounds=(-100, 100),
        method='bounded'
    )

    magic_scipy = result.x
    predictions_scipy = calculate_prediction(today_prices, aggregated_scores, magic_scipy)
    mae_scipy = mean_absolute_error(actual_prices, predictions_scipy)
    rmse_scipy = np.sqrt(mean_squared_error(actual_prices, predictions_scipy))

    print(f"Magic multiplier (Scipy): {magic_scipy:.6f}")
    print(f"MAE: {mae_scipy:.4f}")
    print(f"RMSE: {rmse_scipy:.4f}")
    print(f"Performance Score: {100 / (1 + rmse_scipy):.2f}")

    print("\n" + "="*80)
    print("METHOD 5: GRID SEARCH")
    print("="*80)

    # Grid search for best magic value
    magic_values = np.linspace(-10, 10, 1000)
    best_rmse = float('inf')
    best_magic_grid = 0

    for magic in magic_values:
        predictions = calculate_prediction(today_prices, aggregated_scores, magic)
        rmse = np.sqrt(mean_squared_error(actual_prices, predictions))
        if rmse < best_rmse:
            best_rmse = rmse
            best_magic_grid = magic

    predictions_grid = calculate_prediction(today_prices, aggregated_scores, best_magic_grid)
    mae_grid = mean_absolute_error(actual_prices, predictions_grid)
    rmse_grid = np.sqrt(mean_squared_error(actual_prices, predictions_grid))

    print(f"Magic multiplier (Grid Search): {best_magic_grid:.6f}")
    print(f"MAE: {mae_grid:.4f}")
    print(f"RMSE: {rmse_grid:.4f}")
    print(f"Performance Score: {100 / (1 + rmse_grid):.2f}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - ALL METHODS")
    print("="*80)

    methods = [
        ("Linear Regression", magic_lr, rmse_lr),
        ("Ridge Regression", magic_ridge, rmse_ridge),
        ("Lasso Regression", magic_lasso, rmse_lasso),
        ("Scipy Optimization", magic_scipy, rmse_scipy),
        ("Grid Search", best_magic_grid, rmse_grid)
    ]

    # Sort by RMSE (best first)
    methods.sort(key=lambda x: x[2])

    print(f"\n{'Method':<25} {'Magic Value':<15} {'RMSE':<10} {'Score':<10}")
    print("-" * 60)
    for method, magic, rmse in methods:
        score = 100 / (1 + rmse)
        print(f"{method:<25} {magic:<15.6f} {rmse:<10.4f} {score:<10.2f}")

    # Best method
    best_method, best_magic, best_rmse = methods[0]
    print("\n" + "="*80)
    print(f"BEST METHOD: {best_method}")
    print(f"RECOMMENDED MAGIC MULTIPLIER: {best_magic:.6f}")
    print("="*80)

    # Show sample predictions with best magic
    print("\nSample Predictions (First 10 rows with best magic):")
    print("-" * 80)
    sample_size = min(10, len(df))
    for i in range(sample_size):
        pred = calculate_prediction(today_prices[i], aggregated_scores[i], best_magic)
        actual = actual_prices[i]
        error = pred - actual
        print(f"Date: {df.iloc[i]['today_news_date']}")
        print(f"  Today: ${today_prices[i]:.2f}, Score: {aggregated_scores[i]:.4f}")
        print(f"  Predicted: ${pred:.2f}, Actual: ${actual:.2f}, Error: ${error:.2f}")

    return best_magic


def main():
    """Main entry point"""
    data_file = "data/price_predictions.csv"
    best_magic = find_magic_multiplier(data_file)

    print(f"\n\nFINAL RECOMMENDATION:")
    print(f"Use magic multiplier = {best_magic:.6f}")
    print(f"Formula: predicted_price = today_price + (aggregated_score * abs(aggregated_score) * {best_magic:.6f})")


if __name__ == "__main__":
    main()
