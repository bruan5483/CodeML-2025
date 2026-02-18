#!/usr/bin/env python3
"""
Combine multiple filtered news JSON files into a single unified format.

This script reads three filtered JSON files (./data/eia_filtered.json, ./data/nig_filtered.json,
./data/gas_headlines_filtered.json) and combines them into a single output file with
standardized fields: date, headline, and summary.

Output: ./data/news_filtered_combined.json
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    """Load JSON file and return as list of dictionaries."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # If it's a single dict, wrap it in a list
                return [data]
            else:
                print(f"Warning: Unexpected data type in {filepath}")
                return []
    except FileNotFoundError:
        print(f"Warning: File not found - {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath} - {e}")
        return []


def normalize_entry(entry: Dict[str, Any], source_file: str) -> Dict[str, str]:
    """
    Normalize an entry to standard format: date, headline, summary.

    Args:
        entry: Dictionary with news data
        source_file: Name of source file for context

    Returns:
        Dictionary with 'date', 'headline', 'summary' keys
    """
    normalized = {
        'date': '',
        'headline': '',
        'summary': ''
    }

    # Extract date - try common field names
    date_fields = ['date', 'observation_date', 'time_published', 'published_date', 'timestamp']
    for field in date_fields:
        if field in entry and entry[field]:
            normalized['date'] = str(entry[field])
            break

    # Extract headline - try common field names
    headline_fields = ['headline', 'title', 'name', 'text']
    for field in headline_fields:
        if field in entry and entry[field]:
            normalized['headline'] = str(entry[field])
            break

    # Extract summary - try common field names
    summary_fields = ['summary', 'description', 'content', 'body', 'text']
    for field in summary_fields:
        if field in entry and entry[field]:
            normalized['summary'] = str(entry[field])
            break

    return normalized


def combine_filtered_files(
    input_files: List[str],
    output_file: str = 'news_filtered_combined.json'
) -> None:
    """
    Combine multiple filtered JSON files into a single standardized output.

    Args:
        input_files: List of input file paths
        output_file: Output file path
    """
    all_entries = []
    stats = {
        'total_entries': 0,
        'entries_per_file': {},
        'entries_with_summary': 0,
        'entries_without_summary': 0
    }

    print("="*80)
    print("COMBINING FILTERED NEWS FILES")
    print("="*80)

    # Load and normalize each file
    for filepath in input_files:
        filename = Path(filepath).name
        print(f"\nProcessing: {filename}")

        entries = load_json_file(filepath)
        print(f"  Loaded: {len(entries)} entries")

        # Normalize each entry
        normalized_entries = []
        for entry in entries:
            normalized = normalize_entry(entry, filename)

            # Only include entries that have at least a headline
            if normalized['headline']:
                normalized_entries.append(normalized)

                # Track summary statistics
                if normalized['summary']:
                    stats['entries_with_summary'] += 1
                else:
                    stats['entries_without_summary'] += 1

        all_entries.extend(normalized_entries)
        stats['entries_per_file'][filename] = len(normalized_entries)
        print(f"  Normalized: {len(normalized_entries)} entries")

    stats['total_entries'] = len(all_entries)

    # Sort by date (if dates are available)
    try:
        all_entries.sort(key=lambda x: x['date'] if x['date'] else '0')
        print("\nEntries sorted by date")
    except Exception as e:
        print(f"\nWarning: Could not sort by date - {e}")

    # Save combined output
    print(f"\n{'='*80}")
    print("SAVING COMBINED OUTPUT")
    print(f"{'='*80}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    # Display statistics
    print(f"\n{'='*80}")
    print("STATISTICS")
    print(f"{'='*80}")
    print(f"Total entries combined: {stats['total_entries']}")
    print(f"\nEntries per file:")
    for filename, count in stats['entries_per_file'].items():
        print(f"  {filename}: {count}")
    print(f"\nSummary field:")
    print(f"  With summary: {stats['entries_with_summary']}")
    print(f"  Without summary: {stats['entries_without_summary']}")

    # Verify output
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print(f"{'='*80}")

    with open(output_file, 'r', encoding='utf-8') as f:
        verification_data = json.load(f)
        print(f"Verified {len(verification_data)} entries in output file")

        if verification_data:
            print(f"\nFirst entry sample:")
            print(json.dumps(verification_data[0], indent=2, ensure_ascii=False))

    print(f"\n{'='*80}")
    print("COMBINE COMPLETE")
    print(f"{'='*80}")


def main():
    """Main entry point."""
    # Define input files
    input_files = [
        './data/eia_filtered.json',
        './data/nig_filtered.json',
        './data/gas_headlines_filtered.json'
    ]

    output_file = './data/news_filtered_combined.json'

    # Run combination
    combine_filtered_files(input_files, output_file)


if __name__ == '__main__':
    main()
