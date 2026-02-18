import json
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
import time
from datetime import datetime

# Configure Vertex AI
PROJECT_ID = "canvas-modem-471214-s5"
LOCATION = "us-central1"
SERVICE_ACCOUNT_KEY_FILE = "api_key.json"

def create_relevance_prompt(item, topic, criteria):
    """Create a prompt for Gemini to evaluate relevance"""
    headline = item.get('headline', '').strip()
    summary = item.get('summary', '').strip()
    
    # Skip entries with no meaningful content
    if not headline and not summary:
        return None
    
    # Combine available text
    text = f"Headline: {headline if headline else '(No headline)'}\nSummary: {summary if summary else '(No summary)'}"
    
    prompt = f"""You are evaluating whether an article is relevant to the topic: "{topic}"

{text}

Relevance Criteria:
{criteria}

Is this article relevant? Respond with ONLY "YES" or "NO" and nothing else."""
    
    return prompt

def evaluate_batch_relevance(items, topic, criteria):
    """Evaluate multiple items in one API call for efficiency"""
    # Filter out items with no content
    valid_items = []
    for item in items:
        headline = item.get('headline', '').strip()
        summary = item.get('summary', '').strip()
        if headline or summary:
            valid_items.append(item)
    
    if not valid_items:
        return None, []
    
    batch_prompt = f"""You are evaluating whether articles are relevant to the topic: "{topic}"

Relevance Criteria:
{criteria}

For each article below, respond with ONLY "YES" or "NO" on a new line.

"""
    
    for i, item in enumerate(valid_items, 1):
        headline = item.get('headline', '').strip()
        summary = item.get('summary', '').strip()
        
        batch_prompt += f"\nArticle {i}:\n"
        batch_prompt += f"Headline: {headline if headline else '(No headline)'}\n"
        
        if summary:
            # Truncate very long summaries
            if len(summary) > 500:
                summary = summary[:500] + "..."
            batch_prompt += f"Summary: {summary}\n"
    
    batch_prompt += "\nRespond with one YES or NO per line for each article:"
    
    return batch_prompt, valid_items

def filter_with_vertex_ai(input_file, output_file, topic, criteria, batch_size=10):
    """
    Filter JSON entries using Vertex AI Gemini for relevance
    """
    
    # Initialize Vertex AI with service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_KEY_FILE
    )
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    model = GenerativeModel("gemini-2.5-flash")
    
    # Read data
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total entries: {len(data)}")
    
    # First pass: filter out entries with no content
    data_with_content = []
    empty_count = 0
    for item in data:
        headline = item.get('headline', '').strip()
        summary = item.get('summary', '').strip()
        if headline or summary:
            data_with_content.append(item)
        else:
            empty_count += 1
    
    print(f"Entries with content: {len(data_with_content)}")
    print(f"Empty entries removed: {empty_count}")
    print(f"Topic: {topic}")
    print(f"Processing in batches of {batch_size}...")
    
    relevant_items = []
    total_batches = (len(data_with_content) + batch_size - 1) // batch_size
    
    # Process in batches
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(data_with_content))
        batch = data_with_content[start_idx:end_idx]
        
        print(f"\nProcessing batch {batch_num + 1}/{total_batches} (items {start_idx + 1}-{end_idx})...")
        
        try:
            # Create batch prompt
            prompt, valid_items = evaluate_batch_relevance(batch, topic, criteria)
            
            if not prompt:
                print("  No valid items in batch, skipping...")
                continue
            
            # Call Vertex AI
            response = model.generate_content(prompt)
            
            # Parse responses
            response_text = response.text.strip()
            responses = response_text.split('\n')
            
            # Match responses to items
            for i, item in enumerate(valid_items):
                if i < len(responses):
                    answer = responses[i].strip().upper()
                    headline = item.get('headline', 'N/A')[:60]
                    if 'YES' in answer:
                        relevant_items.append(item)
                        print(f"  ✓ Relevant: {headline}...")
                    else:
                        print(f"  ✗ Not relevant: {headline}...")
            
            # Rate limiting - wait between batches
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing batch: {e}")
            print("Continuing with next batch...")
            time.sleep(2)
    
    # Sort by date (most recent first)
    def parse_date(item):
        try:
            return datetime.strptime(item['date'], '%Y-%m-%d')
        except (ValueError, KeyError):
            return datetime.min
    
    relevant_items.sort(key=parse_date, reverse=True)
    
    # Write filtered data
    print(f"\nWriting filtered data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(relevant_items, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Filtering complete!")
    print(f"Original entries: {len(data)}")
    print(f"Entries with content: {len(data_with_content)}")
    print(f"Relevant entries: {len(relevant_items)}")
    print(f"Filtered out: {len(data_with_content) - len(relevant_items)}")
    print(f"Retention rate: {len(relevant_items) / len(data_with_content) * 100:.1f}%")
    print(f"{'='*60}")

def preview_filter(input_file, topic, criteria, sample_size=20):
    """
    Preview filtering on a small sample before processing all 55k entries
    """
    print("PREVIEW MODE - Testing on sample data")
    print("="*60)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter out empty entries first
    data_with_content = []
    for item in data:
        headline = item.get('headline', '').strip()
        summary = item.get('summary', '').strip()
        if headline or summary:
            data_with_content.append(item)
    
    print(f"Total entries in file: {len(data)}")
    print(f"Entries with content: {len(data_with_content)}")
    print(f"Empty entries: {len(data) - len(data_with_content)}")
    
    # Take a random sample from non-empty entries
    import random
    sample = random.sample(data_with_content, min(sample_size, len(data_with_content)))
    
    # Initialize Vertex AI with service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_KEY_FILE
    )
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    model = GenerativeModel("gemini-2.5-flash")
    
    relevant_count = 0
    
    print(f"\nEvaluating {len(sample)} sample entries...\n")
    
    for i, item in enumerate(sample, 1):
        prompt = create_relevance_prompt(item, topic, criteria)
        
        if not prompt:
            print(f"{i}. SKIPPED (no content)")
            continue
        
        try:
            response = model.generate_content(prompt)
            answer = response.text.strip().upper()
            
            is_relevant = 'YES' in answer
            if is_relevant:
                relevant_count += 1
            
            status = "✓ RELEVANT" if is_relevant else "✗ NOT RELEVANT"
            headline = item.get('headline', 'N/A')[:80]
            print(f"{i}. {status}")
            print(f"   Headline: {headline}...")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"{i}. Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Preview Results:")
    print(f"Sample size: {len(sample)}")
    print(f"Relevant: {relevant_count}")
    print(f"Not relevant: {len(sample) - relevant_count}")
    if len(sample) > 0:
        print(f"Estimated retention: {relevant_count / len(sample) * 100:.1f}%")
        print(f"\nProjected results for {len(data_with_content)} entries with content:")
        print(f"  ~{int(len(data_with_content) * relevant_count / len(sample))} relevant entries")
    print(f"{'='*60}")

if __name__ == "__main__":
    input_file = "gas_headlines.json"
    output_file = "filtered_output.json"
    
    # Define your filtering criteria - MORE SPECIFIC NOW
    topic = "natural gas industry, LNG markets, and energy infrastructure business"
    
    criteria = """
    INCLUDE articles that are PRIMARILY about:
    - Natural gas production, extraction, drilling operations, or exploration
    - LNG (liquefied natural gas) export/import facilities, terminals, and international trade
    - Gas pipeline construction, infrastructure projects, or transmission systems
    - Natural gas market prices, futures trading, supply/demand economics
    - Energy companies' natural gas operations, earnings, or strategy
    - Government policy, regulations, or legislation specifically affecting natural gas industry
    - Industry mergers, acquisitions, partnerships, or major business deals
    - Gas storage facilities, capacity expansions, or operations
    - International gas trade agreements, contracts, or geopolitical disputes
    - Shale gas development or unconventional gas resources
    
    EXCLUDE articles about:
    - Local gas leaks, utility emergencies, or accidents (unless major industry-wide impact)
    - Residential heating, cooking, or consumer appliance advice
    - General energy news where gas is only mentioned in passing
    - Weather forecasts or heating bills advice for homeowners
    - Advertisements or promotional content
    - Restaurant reviews, recipes, or food content
    - Real estate listings mentioning gas utilities
    - Small local utility repairs or maintenance
    
    KEY RULE: The article must be about natural gas as an INDUSTRY/BUSINESS topic, 
    not just incidental mention of gas. Focus on commercial, industrial, and market aspects.
    """
    
    # STEP 1: Preview on sample (recommended for 55k entries)
    print("Step 1: Running preview on sample data...")
    preview_filter(input_file, topic, criteria, sample_size=20)
    
    # STEP 2: Uncomment below to process all entries
    # print("\nStep 2: Processing all entries...")
    # filter_with_vertex_ai(input_file, output_file, topic, criteria, batch_size=10)