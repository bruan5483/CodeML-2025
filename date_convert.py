import json
from datetime import datetime

def convert_date_format(date_string):
    """Convert date from 'Month DD, YYYY' to 'YYYY-MM-DD' format."""
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_string, "%B %d, %Y")
        # Convert to YYYY-MM-DD format
        return date_obj.strftime("%Y-%m-%d")
    except ValueError as e:
        print(f"Warning: Could not parse date '{date_string}': {e}")
        return date_string  # Return original if parsing fails

def process_json_file(input_file, output_file):
    """Read JSON file, convert dates, and write to output file."""
    # Read input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process each item in the array
    for item in data:
        if 'date' in item:
            item['date'] = convert_date_format(item['date'])
    
    # Write to output JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(data)} items. Output written to {output_file}")

def process_json_string(json_string):
    """Process JSON string and return converted data."""
    data = json.loads(json_string)
    
    for item in data:
        if 'date' in item:
            item['date'] = convert_date_format(item['date'])
    
    return json.dumps(data, indent=2, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    # Example 1: Process from file
    process_json_file('input2.json', 'input3.json')
    
#     # Example 2: Process string directly
#     sample_json = '''[
#   {
#     "headline": "Natural Gas Futures Freefall into Holiday Weekend on Stout Supply, Mild Weather",
#     "date": "October 10, 2025",
#     "summary": "Ample supply and a lackluster near-term demand outlook pushed natural gas futures lower for a third straight session heading into Columbus Day weekend."
#   }
# ]'''
    
#     result = process_json_string(sample_json)
#     print("Converted JSON:")
#     print(result)