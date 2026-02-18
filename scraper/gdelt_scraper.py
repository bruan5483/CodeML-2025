"""
Historical News Scraper for Natural Gas Articles
- Fetches full article content for better summaries
- Outputs only: title, date (YYYY-MM-DD), summary
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import time
import json
import requests
from typing import List, Dict
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class EnhancedNewsScraper:
    """
    Scrapes historical news with enhanced summaries and translation
    """
    
    def __init__(self, newsapi_key=None, max_workers=5):
        self.max_workers = max_workers
        self.articles = []
        self.newsapi_key = newsapi_key or os.getenv('NEWSAPI_KEY')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def translate_text(self, text, target_lang='en'):
        """
        Translate text to English using LibreTranslate (free, no API key)
        Fallback to MyMemory API if needed
        """
        if not text or not text.strip():
            return text
        
        # Convert to string if not already
        text = str(text) if not isinstance(text, str) else text
            
        # Check if already English (simple heuristic)
        if all(ord(char) < 128 for char in text if char.isalpha()):
            return text
        
        try:
            # LibreTranslate
            url = "https://libretranslate.de/translate"
            payload = {
                'q': text,
                'source': 'auto',
                'target': target_lang,
                'format': 'text'
            }
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('translatedText', text)
        except:
            pass
        
        try:
            # Fallback to MyMemory API
            url = f"https://api.mymemory.translated.net/get"
            params = {
                'q': text[:500],
                'langpair': f'auto|{target_lang}'
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('responseStatus') == 200:
                    return result.get('responseData', {}).get('translatedText', text)
        except:
            pass
        
        return text  # Return original if translation fails
    
    def extract_article_content(self, url):
        """
        Fetch and extract article content from URL for better summaries
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try common article content selectors
            content = None
            selectors = [
                'article',
                '[class*="article-body"]',
                '[class*="article-content"]',
                '[class*="story-body"]',
                '[class*="post-content"]',
                '[itemprop="articleBody"]',
                'div.content',
                'div.body',
                'main'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(separator=' ', strip=True)
                    break
            
            # Fallback: get all paragraph text
            if not content or len(content) < 100:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Clean up the content
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content if len(content) > 50 else None
            
        except Exception as e:
            return None
    
    def create_summary(self, content, max_length=300):
        """
        Create a summary from article content
        Takes first few sentences up to max_length
        """
        if not content:
            return ""
        
        # Convert to string if needed
        content = str(content) if not isinstance(content, str) else content
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence + " "
            else:
                break
        
        return summary.strip()
    
    def parse_date(self, date_str):
        """
        Parse various date formats and return YYYY-MM-DD
        """
        if not date_str or pd.isna(date_str):
            return ""
        
        # Convert to string
        date_str = str(date_str)
        
        # Remove timezone info and extra text
        date_str = date_str.split('T')[0].split(' ')[0]
        
        # Try to extract YYYYMMDD format
        if len(date_str) == 8 and date_str.isdigit():
            try:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                pass
        
        # Try standard formats
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%Y%m%d']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str
    
    def fetch_gdelt_articles(self, query="natural gas", start_date="1997-01-01", 
                            end_date="2025-10-11", max_records=250):
        """
        Fetch articles from GDELT DOC API
        """
        print(f"Fetching GDELT: {start_date} to {end_date}...")
        
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
        articles = []
        
        params = {
            'query': query,
            'mode': 'ArtList',
            'maxrecords': max_records,
            'format': 'json',
            'startdatetime': start_date.replace('-', '') + '000000',
            'enddatetime': end_date.replace('-', '') + '235959',
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'articles' in data:
                    for article in data['articles']:
                        articles.append({
                            'title': article.get('title', ''),
                            'url': article.get('url', ''),
                            'date': article.get('seendate', ''),
                            'language': article.get('language', 'en'),
                            'source': 'GDELT'
                        })
                    
                    print(f"  ✓ Found {len(articles)} articles")
            else:
                print(f"  ✗ Status {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        return articles
    
    def fetch_newsapi_articles(self, query="natural gas", from_date=None, to_date=None):
        """
        Fetch articles from NewsAPI
        """
        
        if not self.newsapi_key:
            print("⚠ NewsAPI key not found, skipping...")
            return []
        
        print(f"Fetching NewsAPI articles...")
        
        base_url = "https://newsapi.org/v2/everything"
        
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        if not from_date:
            from_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
        
        articles = []
        
        headers = {'X-Api-Key': self.newsapi_key}
        params = {
            'q': query,
            'from': from_date,
            'to': to_date,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 100,
        }
        
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    for article in data.get('articles', []):
                        articles.append({
                            'title': article.get('title', ''),
                            'url': article.get('url', ''),
                            'date': article.get('publishedAt', '').split('T')[0],
                            'summary': article.get('description', ''),
                            'content': article.get('content', ''),
                            'language': 'en',
                            'source': 'NewsAPI'
                        })
                    
                    print(f"  ✓ Found {len(articles)} articles")
            else:
                print(f"  ✗ Status {response.status_code}")
                    
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        return articles
    
    def process_article(self, article):
        """
        Process a single article: translate title, fetch content, create summary
        """
        try:
            # Convert all fields to strings and handle NaN
            article['title'] = str(article.get('title', '')) if pd.notna(article.get('title')) else ''
            article['date'] = str(article.get('date', '')) if pd.notna(article.get('date')) else ''
            article['summary'] = str(article.get('summary', '')) if pd.notna(article.get('summary')) else ''
            article['language'] = str(article.get('language', 'en')) if pd.notna(article.get('language')) else 'en'
            article['url'] = str(article.get('url', '')) if pd.notna(article.get('url')) else ''
            
            # Translate title if needed
            if article.get('language', 'en').lower() != 'en':
                original_title = article['title']
                article['title'] = self.translate_text(original_title)
            
            # Parse date to YYYY-MM-DD
            article['date'] = self.parse_date(article.get('date', ''))
            
            # Get better summary
            if not article.get('summary') or len(article.get('summary', '')) < 50:
                # Try to fetch article content
                content = self.extract_article_content(article['url'])
                
                if content:
                    article['summary'] = self.create_summary(content, max_length=300)
                elif article.get('content'):
                    article['summary'] = self.create_summary(article['content'], max_length=300)
                else:
                    article['summary'] = article.get('summary', 'No summary available')
            
            # Keep only required fields
            return {
                'title': article.get('title', ''),
                'date': article.get('date', ''),
                'summary': article.get('summary', '')
            }
            
        except Exception as e:
            print(f"  ✗ Error processing article: {e}")
            return {
                'title': article.get('title', ''),
                'date': article.get('date', ''),
                'summary': article.get('summary', '')
            }
    
    def fetch_gdelt_batch_by_year(self, query="natural gas", start_year=1997, end_year=2025):
        """
        Fetch GDELT articles in yearly batches
        """
        print(f"\n{'='*80}")
        print(f"Fetching GDELT data from {start_year} to {end_year}")
        print(f"{'='*80}\n")
        
        all_articles = []
        
        year_ranges = []
        for year in range(start_year, end_year + 1):
            start = f"{year}-01-01"
            end = f"{year}-12-31"
            year_ranges.append((query, start, end))
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.fetch_gdelt_articles, q, s, e, 250): (q, s, e)
                for q, s, e in year_ranges
            }
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                query, start, end = futures[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    print(f"Progress: {completed}/{len(year_ranges)} years")
                except Exception as e:
                    print(f"✗ Error: {e}")
                
                time.sleep(0.5)
        
        return all_articles
    
    def scrape_and_process(self, queries=['natural gas'], start_year=1997, end_year=2025):
        """
        Main function: scrape, translate, enhance summaries
        """
        print("\n" + "="*80)
        print("ENHANCED NEWS SCRAPER - Natural Gas Articles")
        print("="*80)
        
        raw_articles = []
        
        for query in queries:
            print(f"\n--- Query: '{query}' ---")
            
            # Fetch from GDELT
            gdelt_articles = self.fetch_gdelt_batch_by_year(
                query=query,
                start_year=start_year,
                end_year=end_year
            )
            raw_articles.extend(gdelt_articles)
            
            # Fetch from NewsAPI
            newsapi_articles = self.fetch_newsapi_articles(query=query)
            raw_articles.extend(newsapi_articles)
        
        print(f"\n{'='*80}")
        print(f"Total raw articles: {len(raw_articles)}")
        print(f"{'='*80}\n")
        
        # Remove duplicates by URL
        df = pd.DataFrame(raw_articles)
        if not df.empty:
            df = df.drop_duplicates(subset=['url'], keep='first')
            raw_articles = df.to_dict('records')
            print(f"After deduplication: {len(raw_articles)} articles\n")
        
        # Process articles in parallel (translate + enhance summaries)
        print(f"Processing articles with {self.max_workers} threads...")
        print("(This may take a while - fetching full articles for summaries)\n")
        
        processed_articles = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_article, article): article 
                      for article in raw_articles}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 10 == 0:
                    print(f"  Processed: {completed}/{len(raw_articles)}")
                
                try:
                    result = future.result()
                    if result and result.get('title'):
                        processed_articles.append(result)
                except Exception as e:
                    pass
                
                time.sleep(0.1) 
        
        self.articles = processed_articles
        
        print(f"\n{'='*80}")
        print(f"FINAL COUNT: {len(processed_articles)} articles")
        print(f"{'='*80}")
        
        return processed_articles
    
    def save_to_csv(self, filename='natural_gas_news.csv'):
        """Save articles to CSV with only: title, date, summary"""
        if self.articles:
            df = pd.DataFrame(self.articles)
            df = df[['title', 'date', 'summary']]
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"\n✓ Saved {len(self.articles)} articles to {filename}")
            
            if not df.empty and 'date' in df.columns:
                valid_dates = df[df['date'] != '']['date']
                if len(valid_dates) > 0:
                    print(f"  Date range: {valid_dates.min()} to {valid_dates.max()}")
        else:
            print("\n⚠ No articles to save")
    
    def save_to_json(self, filename='natural_gas_news.json'):
        """Save articles to JSON with only: title, date, summary"""
        if self.articles:
            clean_articles = [
                {
                    'title': a.get('title', ''),
                    'date': a.get('date', ''),
                    'summary': a.get('summary', '')
                }
                for a in self.articles
            ]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(clean_articles, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(self.articles)} articles to {filename}")
        else:
            print("⚠ No articles to save")


def main():
    """
    Set NEWSAPI_KEY=your_key (Windows) or export NEWSAPI_KEY=your_key (Mac/Linux)
    """
    
    # Initialize scraper
    scraper = EnhancedNewsScraper(
        newsapi_key='ea3c774f7f404e02bcc26f43f5c3db5c',
        max_workers=3 
    )
    
    # Search queries
    queries = [
        'natural gas',
        'natural gas prices',
        'LNG'
    ]
    
    # Scrape and process articles from 1997 to 2025
    articles = scraper.scrape_and_process(
        queries=queries,
        start_year=1997,
        end_year=2025
    )
    
    # Save results (only title, date, summary)
    scraper.save_to_csv('natural_gas_news.csv')
    scraper.save_to_json('natural_gas_news.json')
    
    # Print samples
    if articles:
        print("\n" + "="*80)
        print("SAMPLE ARTICLES")
        print("="*80)
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. Title: {article.get('title', 'No title')}")
            print(f"   Date: {article.get('date', 'Unknown')}")
            print(f"   Summary: {article.get('summary', 'No summary')[:200]}...")


if __name__ == "__main__":
    main()