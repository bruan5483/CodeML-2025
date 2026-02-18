import json
from datetime import datetime

def merge_json_files(file1, file2, output_file):
    """
    Merge two JSON files and sort by date (most recent first)
    
    Args:
        file1: Path to first JSON file
        file2: Path to second JSON file
        output_file: Path for merged output file
    """
    
    # Read first JSON file
    print(f"Reading {file1}...")
    with open(file1, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    
    # Read second JSON file
    print(f"Reading {file2}...")
    with open(file2, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    
    # Combine both lists
    merged_data = data1 + data2
    print(f"Total items before merge: {len(merged_data)}")
    
    # Sort by date (most recent first)
    # Convert date string to datetime for proper sorting
    def parse_date(item):
        try:
            return datetime.strptime(item['date'], '%Y-%m-%d')
        except (ValueError, KeyError):
            # If date parsing fails, put item at the end
            return datetime.min
    
    merged_data.sort(key=parse_date, reverse=True)
    
    # Write merged and sorted data
    print(f"Writing merged data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"Merge complete! {len(merged_data)} total items")
    print(f"Date range: {merged_data[-1]['date']} to {merged_data[0]['date']}")

if __name__ == "__main__":
    # Usage
    file1 = "input1.json"
    file2 = "input3.json"
    output_file = "merged_output.json"
    
    merge_json_files(file1, file2, output_file)