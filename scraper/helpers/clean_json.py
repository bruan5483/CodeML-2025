import json
import re
from difflib import SequenceMatcher

def normalize_text(text):
    """Normalize text for comparison by removing punctuation and extra spaces."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_redundant_summary(headline, summary, similarity_threshold=0.85):
    """Check if summary is essentially the same as headline."""
    if not summary or not headline:
        return False
    
    # Normalize both texts
    norm_headline = normalize_text(headline)
    norm_summary = normalize_text(summary)
    
    if norm_headline == norm_summary:
        return True
    
    # Check similarity ratio
    ratio = SequenceMatcher(None, norm_headline, norm_summary).ratio()
    if ratio >= similarity_threshold:
        return True
    
    return False

def clean_json_file(input_file, output_file=None, similarity_threshold=0.85):
    """Process JSON file and clear redundant summaries."""
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Track statistics
    total = len(data)
    cleared = 0
    
    # Process each item
    for item in data:
        headline = item.get('headline', '')
        summary = item.get('summary', '')
        
        if is_redundant_summary(headline, summary, similarity_threshold):
            item['summary'] = ''
            cleared += 1
    
    # Write output
    output_file = output_file or input_file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {total} items")
    print(f"Cleared {cleared} redundant summaries")
    print(f"Output written to: {output_file}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 clean_json.py input.json [output.json]")
        print("If output.json is not provided, input file will be overwritten")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    clean_json_file(input_file, output_file)