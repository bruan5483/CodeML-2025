import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import argparse


def get_headlines_coverage(db_path: str = "natural_gas_headlines.db", 
                           output_file: str = None,
                           missing_output: str = None,
                           start_date: str = "1997-01-01",
                           end_date: str = None):
    """
    Analyze headlines coverage and identify missing days.
    
    Args:
        db_path: Path to SQLite database
        output_file: Optional CSV file to save all days (with counts)
        missing_output: Optional CSV file to save only missing days
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD), defaults to today
    """
    conn = sqlite3.connect(db_path)
    
    # Get headline counts per day
    query = '''
        SELECT 
            date,
            COUNT(*) as headline_count
        FROM headlines
        GROUP BY date
        ORDER BY date ASC
    '''
    
    df_headlines = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert to datetime
    df_headlines['date'] = pd.to_datetime(df_headlines['date'])
    
    # Create complete date range
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Generate all dates in range
    all_dates = pd.date_range(start=start, end=end, freq='D')
    df_all = pd.DataFrame({'date': all_dates})
    
    # Merge with headlines data
    df_complete = df_all.merge(df_headlines, on='date', how='left')
    df_complete['headline_count'] = df_complete['headline_count'].fillna(0).astype(int)
    
    # Identify missing days
    df_missing = df_complete[df_complete['headline_count'] == 0].copy()
    df_has_data = df_complete[df_complete['headline_count'] > 0].copy()
    
    # Calculate statistics
    total_days = len(df_complete)
    days_with_data = len(df_has_data)
    days_missing = len(df_missing)
    coverage_pct = (days_with_data / total_days) * 100
    
    total_headlines = df_complete['headline_count'].sum()
    avg_per_day = df_has_data['headline_count'].mean() if days_with_data > 0 else 0
    median_per_day = df_has_data['headline_count'].median() if days_with_data > 0 else 0
    
    # Print results
    print("\n" + "="*80)
    print("HEADLINES COVERAGE ANALYSIS")
    print("="*80)
    print(f"Database: {db_path}")
    print(f"Analysis period: {start_date} to {end_date}")
    print(f"\nTotal days in range: {total_days:,}")
    print(f"Days WITH headlines: {days_with_data:,} ({coverage_pct:.1f}%)")
    print(f"Days WITHOUT headlines: {days_missing:,} ({100-coverage_pct:.1f}%)")
    print(f"\nTotal headlines: {total_headlines:,}")
    print(f"Average per day (when present): {avg_per_day:.1f}")
    print(f"Median per day (when present): {median_per_day:.0f}")
    
    # Show distribution of days with data
    print("\n" + "-"*80)
    print("DISTRIBUTION OF DAYS WITH HEADLINES:")
    print("-"*80)
    bins = [0, 1, 5, 10, 25, 50, 100, 500, float('inf')]
    labels = ['1', '2-5', '6-10', '11-25', '26-50', '51-100', '101-500', '500+']
    df_has_data['bin'] = pd.cut(df_has_data['headline_count'], bins=bins, labels=labels, right=True)
    distribution = df_has_data['bin'].value_counts().sort_index()
    
    for label, count in distribution.items():
        pct = (count / days_with_data) * 100 if days_with_data > 0 else 0
        print(f"  {label:8s} headlines: {count:5,} days ({pct:5.1f}%)")
    
    # Find gaps (consecutive missing days)
    print("\n" + "-"*80)
    print("LARGEST COVERAGE GAPS:")
    print("-"*80)
    
    if len(df_missing) > 0:
        df_missing = df_missing.sort_values('date')
        df_missing['gap_id'] = (df_missing['date'].diff() > timedelta(days=1)).cumsum()
        
        gaps = []
        for gap_id, group in df_missing.groupby('gap_id'):
            gap_start = group['date'].min()
            gap_end = group['date'].max()
            gap_days = len(group)
            gaps.append({
                'start': gap_start,
                'end': gap_end,
                'days': gap_days
            })
        
        # Sort by number of days
        gaps_sorted = sorted(gaps, key=lambda x: x['days'], reverse=True)
        
        for i, gap in enumerate(gaps_sorted[:10], 1):
            print(f"  {i:2d}. {gap['start'].strftime('%Y-%m-%d')} to {gap['end'].strftime('%Y-%m-%d')}: "
                  f"{gap['days']:,} days missing")
        
        if len(gaps_sorted) > 10:
            print(f"  ... and {len(gaps_sorted) - 10} more gaps")
        
        print(f"\nTotal number of gaps: {len(gaps_sorted)}")
    else:
        print("  No missing days! Perfect coverage!")
    
    # Recent missing days
    print("\n" + "-"*80)
    print("RECENT MISSING DAYS (last 30 days):")
    print("-"*80)
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_missing = df_missing[df_missing['date'] >= thirty_days_ago]
    
    if len(recent_missing) > 0:
        for idx, row in recent_missing.iterrows():
            print(f"  {row['date'].strftime('%Y-%m-%d')} ({row['date'].strftime('%A')})")
    else:
        print("  No missing days in the last 30 days!")
    
    # Coverage by year
    print("\n" + "-"*80)
    print("COVERAGE BY YEAR:")
    print("-"*80)
    
    df_complete['year'] = df_complete['date'].dt.year
    yearly_stats = df_complete.groupby('year').agg({
        'headline_count': ['count', 'sum', lambda x: (x > 0).sum()]
    }).round(1)
    yearly_stats.columns = ['total_days', 'total_headlines', 'days_with_data']
    yearly_stats['coverage_pct'] = (yearly_stats['days_with_data'] / yearly_stats['total_days'] * 100).round(1)
    yearly_stats['avg_per_day'] = (yearly_stats['total_headlines'] / yearly_stats['days_with_data']).round(1)
    
    for year, row in yearly_stats.iterrows():
        print(f"  {year}: {row['days_with_data']:.0f}/{row['total_days']:.0f} days "
              f"({row['coverage_pct']:.1f}% coverage), "
              f"{row['total_headlines']:.0f} headlines "
              f"({row['avg_per_day']:.1f} avg/day)")
    
    # Save outputs
    if output_file:
        df_output = df_complete[['date', 'headline_count']].copy()
        df_output['date'] = df_output['date'].dt.strftime('%Y-%m-%d')
        df_output.to_csv(output_file, index=False)
        print(f"\n✓ Saved complete day-by-day results to {output_file}")
    
    if missing_output:
        df_missing_output = df_missing[['date']].copy()
        df_missing_output['date'] = df_missing_output['date'].dt.strftime('%Y-%m-%d')
        df_missing_output['day_of_week'] = pd.to_datetime(df_missing_output['date']).dt.strftime('%A')
        df_missing_output.to_csv(missing_output, index=False)
        print(f"✓ Saved {len(df_missing_output):,} missing days to {missing_output}")
    
    print("\n" + "="*80)
    
    return df_complete, df_missing


def main():
    parser = argparse.ArgumentParser(description='Analyze headlines coverage and find missing days')
    parser.add_argument('--db', default='natural_gas_headlines.db', 
                       help='Path to SQLite database (default: natural_gas_headlines.db)')
    parser.add_argument('--output', '-o', 
                       help='Save complete results to CSV file')
    parser.add_argument('--missing', '-m',
                       help='Save only missing days to CSV file')
    parser.add_argument('--start-date', default='1997-01-01',
                       help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date',
                       help='End date for analysis (YYYY-MM-DD), defaults to today')
    
    args = parser.parse_args()
    
    df_complete, df_missing = get_headlines_coverage(
        db_path=args.db,
        output_file=args.output,
        missing_output=args.missing,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    return df_complete, df_missing


if __name__ == '__main__':
    main()