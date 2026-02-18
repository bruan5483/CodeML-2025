import json
from deep_translator import GoogleTranslator
import time

def translate_text(text, translator):
    """Translate text to English, return original if empty or translation fails"""
    if not text or text.strip() == "":
        return text
    
    try:
        # Google Translate has a character limit, so split long texts
        max_length = 4500
        if len(text) <= max_length:
            return translator.translate(text)
        
        # Split long text into chunks
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        translated_chunks = [translator.translate(chunk) for chunk in chunks]
        return " ".join(translated_chunks)
    
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def translate_json_file(input_file, output_file):
    """Read JSON file, translate all text fields to English, save to new file"""
    
    # Initialize translator
    translator = GoogleTranslator(source='auto', target='en')
    
    # Read input JSON
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Translating {len(data)} items...")
    
    # Translate each item
    for i, item in enumerate(data):
        print(f"Processing item {i+1}/{len(data)}...")
        
        # Translate title
        if 'title' in item:
            item['title'] = translate_text(item['title'], translator)
        
        # Translate summary
        if 'summary' in item:
            item['summary'] = translate_text(item['summary'], translator)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Write output JSON
    print(f"Writing to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Translation complete!")

if __name__ == "__main__":
    # Usage
    input_file = "natural_gas_news.json"  # Change to your input file name
    output_file = "translated.json"
    
    translate_json_file(input_file, output_file)