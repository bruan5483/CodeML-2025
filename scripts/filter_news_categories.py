#!/usr/bin/env python3
"""
Filter News_Category_Dataset_v3.json to extract only specific categories.

This script reads the JSONL file and outputs only entries that match
the specified categories to a new JSONL file.
"""

import json
from pathlib import Path
from typing import Set, List


# Categories to extract
TARGET_CATEGORIES = {
    # "BUSINESS",
    "MONEY",
    "ENVIRONMENT",
    "GREEN",
    "POLITICS",
    "SCIENCE",
    "WORLD NEWS",
    "U.S. NEWS"
}


def filter_by_categories(input_file: str, output_file: str, categories: Set[str]) -> int:
    """
    Filter JSON entries by category and write to output file.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSONL file
        categories: Set of category names to keep

    Returns:
        Number of entries written
    """
    count = 0
    category_counts = {cat: 0 for cat in categories}

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                category = data.get('category')

                # Check if category matches our target categories
                if category in categories:
                    # Write the entry to output file
                    json.dump(data, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    count += 1
                    category_counts[category] += 1

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue

    return count, category_counts


def main():
    """Main entry point"""
    # Paths
    input_file = Path(__file__).parent.parent / "data" / "News_Category_Dataset_v3.json"
    output_file = Path(__file__).parent.parent / "data" / "filtered.json"

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"\nFiltering for {len(TARGET_CATEGORIES)} categories:")
    for cat in sorted(TARGET_CATEGORIES):
        print(f"  - {cat}")

    print("\nProcessing...")

    # Filter the data
    total_count, category_counts = filter_by_categories(
        str(input_file),
        str(output_file),
        TARGET_CATEGORIES
    )

    # Display results
    print(f"\n{'='*60}")
    print(f"Filtering complete!")
    print(f"{'='*60}")
    print(f"\nTotal entries written: {total_count:,}")
    print(f"\nBreakdown by category:")
    for category in sorted(TARGET_CATEGORIES):
        count = category_counts[category]
        print(f"  {category:15s}: {count:,}")
    print(f"\n{'='*60}")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
