#!/usr/bin/env python3
"""
Extract unique categories from News_Category_Dataset_v3.json

This script reads the JSONL file (one JSON object per line) and extracts
all unique values from the "category" field.
"""

import json
from pathlib import Path
from typing import Set


def extract_unique_categories(json_file_path: str) -> Set[str]:
    """
    Extract all unique categories from the JSON file.

    Args:
        json_file_path: Path to the JSONL file

    Returns:
        Set of unique category strings
    """
    categories = set()

    with open(json_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                category = data.get('category')

                if category:
                    categories.add(category)

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue

    return categories


def main():
    """Main entry point"""
    # Path to the data file
    data_file = Path(__file__).parent.parent / "data" / "News_Category_Dataset_v3.json"

    if not data_file.exists():
        print(f"Error: File not found: {data_file}")
        return

    print(f"Reading categories from: {data_file}")
    print("Processing...")

    # Extract categories
    categories = extract_unique_categories(str(data_file))

    # Sort and display results
    sorted_categories = sorted(categories)

    print(f"\nFound {len(sorted_categories)} unique categories:\n")
    print("=" * 50)

    for i, category in enumerate(sorted_categories, 1):
        print(f"{i:2d}. {category}")

    print("=" * 50)
    print(f"\nTotal unique categories: {len(sorted_categories)}")


if __name__ == "__main__":
    main()
