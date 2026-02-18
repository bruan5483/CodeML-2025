import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import random
from typing import List, Dict, Optional
import sqlite3
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

@dataclass
class NewsHeadline:
    """Lightweight data class for headlines only"""
    headline: str
    date: str
    summary: str = ""

class MassiveGasNewsScraper:
    """Aggressive multi-source scraper targeting 100,000+ headlines"""
    
    def __init__(self, db_path: str = "natural_gas_headlines.db", max_workers: int = 20):
        self.db_path = db_path
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.init_database()
    
    def _create_session(self):
        """Create session with retry logic"""
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=(500, 502, 504))
        session.mount('http://', HTTPAdapter(max_retries=retry))
        session.mount('https://', HTTPAdapter(max_retries=retry))
        return session
    
    def init_database(self):
        """Initialize SQLite database with migration support"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='headlines'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            cursor.execute("PRAGMA table_info(headlines)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'title' in columns and 'headline' not in columns:
                print("⚠ Migrating database from old schema...")
                cursor.execute("ALTER TABLE headlines RENAME TO headlines_old")
                cursor.execute('''
                    CREATE TABLE headlines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        headline TEXT NOT NULL,
                        date TEXT NOT NULL,
                        summary TEXT,
                        url TEXT UNIQUE NOT NULL,
                        source TEXT NOT NULL,
                        category TEXT,
                        scraped_at TEXT NOT NULL
                    )
                ''')
                
                cursor.execute("SELECT COUNT(*) FROM headlines_old")
                old_count = cursor.fetchone()[0]
                
                if old_count > 0:
                    cursor.execute("PRAGMA table_info(headlines_old)")
                    old_columns = {col[1] for col in cursor.fetchall()}
                    old_date_col = 'published_date' if 'published_date' in old_columns else 'date'
                    old_title_col = 'title' if 'title' in old_columns else 'headline'
                    
                    cursor.execute(f'''
                        INSERT INTO headlines (headline, date, summary, url, source, category, scraped_at)
                        SELECT {old_title_col}, {old_date_col}, summary, url, source, category, scraped_at
                        FROM headlines_old
                    ''')
                    print(f"✓ Migrated {old_count} records from old schema")
                
                cursor.execute("DROP TABLE headlines_old")
        else:
            cursor.execute('''
                CREATE TABLE headlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    headline TEXT NOT NULL,
                    date TEXT NOT NULL,
                    summary TEXT,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT,
                    scraped_at TEXT NOT NULL
                )
            ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON headlines(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON headlines(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_headline ON headlines(headline)')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized: {self.db_path}")
    
    # ============================================================
    # SCRAPERS (unchanged from original)
    # ============================================================
    
    def scrape_oilprice_extreme(self) -> List[NewsHeadline]:
        """OilPrice.com - Go to the absolute limit - FIXED"""
        headlines = []
        session = self._create_session()
        
        print("    Starting OilPrice scraper...")
        
        for page in range(1, 3000):
            try:
                if page == 1:
                    url = "https://oilprice.com/Energy/Natural-Gas/"
                else:
                    url = f"https://oilprice.com/Energy/Natural-Gas/?page={page}"
                
                response = session.get(url, headers=self.headers, timeout=12)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('div', class_='categoryArticle')
                
                if not articles:
                    articles = soup.find_all('article')
                
                if not articles:
                    articles = soup.find_all('div', class_=re.compile('article', re.I))
                
                if not articles:
                    break
                
                page_count = 0
                for article in articles:
                    try:
                        title_elem = article.find('a', class_=re.compile('title|headline', re.I))
                        if not title_elem:
                            title_elem = article.find('h2')
                        if not title_elem:
                            title_elem = article.find('h3')
                        if not title_elem:
                            title_elem = article.find('a', href=re.compile('Energy/Natural-Gas'))
                        
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        article_url = title_elem.get('href', '') if title_elem.name == 'a' else ''
                        
                        if not title and article_url:
                            url_parts = article_url.rstrip('/').split('/')
                            if url_parts:
                                title = url_parts[-1].replace('-', ' ').replace('.html', '').strip()
                        
                        if not title or len(title) < 10:
                            continue
                        
                        if not article_url.startswith('http') and article_url:
                            article_url = 'https://oilprice.com' + article_url
                        
                        summary_elem = article.find('p', class_=re.compile('summary|description|excerpt', re.I))
                        if not summary_elem:
                            summary_elem = article.find('p')
                        summary = summary_elem.get_text(strip=True) if summary_elem else ""
                        
                        date_elem = article.find('span', class_='article_byline')
                        if not date_elem:
                            date_elem = article.find('time')
                        if not date_elem:
                            date_elem = article.find(class_=re.compile('date', re.I))
                        
                        pub_date = self._parse_date(date_elem.get_text() if date_elem else "")
                        
                        headlines.append(NewsHeadline(
                            headline=title,
                            date=pub_date,
                            summary=summary[:300]
                        ))
                        page_count += 1
                        
                    except Exception as e:
                        continue
                
                if page_count == 0:
                    break
                
                time.sleep(0.2)
                
                if page % 100 == 0:
                    print(f"      OilPrice page {page}... ({len(headlines)} headlines)")
                    
            except Exception as e:
                break
        
        print(f"    OilPrice complete: {len(headlines)} headlines")
        return headlines
    
    def scrape_natural_gas_world_extreme(self) -> List[NewsHeadline]:
        """Natural Gas World - Maximum depth"""
        headlines = []
        session = self._create_session()
        
        for page in range(1, 2000):
            try:
                url = "https://www.naturalgasworld.com/" if page == 1 else f"https://www.naturalgasworld.com/page/{page}/"
                response = session.get(url, headers=self.headers, timeout=12)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('article')
                
                if not articles:
                    break
                
                for article in articles:
                    try:
                        title_elem = article.find(['h2', 'h3', 'h1'])
                        if not title_elem:
                            title_elem = article.find('a')
                        
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        date_elem = article.find('time')
                        if date_elem and date_elem.get('datetime'):
                            pub_date = date_elem['datetime'][:10]
                        else:
                            date_text = article.find(class_=re.compile('date|time', re.I))
                            pub_date = self._parse_date(date_text.get_text() if date_text else "")
                        
                        summary_elem = article.find('p')
                        summary = summary_elem.get_text(strip=True)[:300] if summary_elem else ""
                        
                        headlines.append(NewsHeadline(
                            headline=title,
                            date=pub_date,
                            summary=summary
                        ))
                    except:
                        continue
                
                time.sleep(0.2)
                
                if page % 100 == 0:
                    print(f"      NGWorld page {page}... ({len(headlines)} headlines)")
                    
            except:
                break
        
        return headlines
    
    def scrape_google_news_massive(self) -> List[NewsHeadline]:
        """Google News - MASSIVE multi-query scraping"""
        headlines = []
        session = self._create_session()
        
        queries = [
            "natural gas prices", "natural gas futures", "Henry Hub", 
            "natural gas storage", "natural gas inventory", "LNG exports",
            "LNG prices", "natural gas production", "natural gas demand",
            "natural gas supply", "Russia natural gas", "Europe natural gas",
            "natural gas pipeline", "shale gas", "Marcellus shale",
            "Permian basin gas", "natural gas exports", "natural gas winter",
            "natural gas power", "natural gas weather", "gas market",
            "gas trading", "Cheniere LNG", "Sabine Pass", "Freeport LNG",
            "gas drilling", "gas rigs", "gas storage report", "EIA gas",
            "natural gas shortage", "gas surplus"
        ]
        
        current_year = datetime.now().year
        
        for query in queries:
            for year in range(1997, current_year + 1):
                for month_start in [1, 7]:
                    try:
                        if month_start == 1:
                            after_date = f"{year}-01-01"
                            before_date = f"{year}-06-30"
                        else:
                            after_date = f"{year}-07-01"
                            before_date = f"{year}-12-31"
                        
                        date_query = f"{query} after:{after_date} before:{before_date}"
                        rss_url = f"https://news.google.com/rss/search?q={quote_plus(date_query)}&hl=en-US&gl=US&ceid=US:en"
                        response = session.get(rss_url, timeout=10)
                        
                        if response.status_code != 200:
                            continue
                        
                        soup = BeautifulSoup(response.content, 'xml')
                        items = soup.find_all('item')[:100]
                        
                        for item in items:
                            try:
                                title = item.title.text if item.title else ""
                                pub_date = item.pubDate.text if item.pubDate else ""
                                description = item.description.text if item.description else ""
                                
                                if description:
                                    description = BeautifulSoup(description, 'html.parser').get_text(strip=True)
                                
                                headlines.append(NewsHeadline(
                                    headline=title,
                                    date=self._parse_date(pub_date),
                                    summary=description[:300] if description else ""
                                ))
                            except:
                                continue
                        
                        time.sleep(0.4)
                        
                    except:
                        continue
            
            print(f"      Google: '{query}' complete - {len(headlines)} total")
        
        return headlines
    
    def scrape_spglobal_extreme(self) -> List[NewsHeadline]:
        """S&P Global - Maximum extraction with strict timeout"""
        headlines = []
        session = self._create_session()
        
        search_terms = ['natural gas', 'LNG']
        
        start_time = time.time()
        max_time = 1200
        
        for term in search_terms:
            for page in range(0, 200):
                try:
                    if time.time() - start_time > max_time:
                        print(f"      S&P Global: timeout reached, collected {len(headlines)} headlines")
                        return headlines
                    
                    url = f"https://www.spglobal.com/commodityinsights/en/search-results?q={quote_plus(term)}&page={page}"
                    response = session.get(url, headers=self.headers, timeout=8)
                    
                    if response.status_code != 200:
                        break
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    articles = soup.find_all(['div', 'article'], class_=re.compile('search-result|article|card'))
                    
                    if not articles:
                        break
                    
                    for article in articles:
                        try:
                            link = article.find('a', href=True)
                            if not link:
                                continue
                            
                            title = link.get_text(strip=True)
                            if not title or len(title) < 15:
                                continue
                            
                            date_elem = article.find('time')
                            if not date_elem:
                                date_elem = article.find(class_=re.compile('date', re.I))
                            
                            pub_date = self._parse_date(date_elem.get_text() if date_elem else "")
                            
                            headlines.append(NewsHeadline(
                                headline=title,
                                date=pub_date,
                                summary=""
                            ))
                        except:
                            continue
                    
                    time.sleep(0.2)
                    
                    if page % 50 == 0:
                        print(f"      S&P Global: '{term}' page {page}...")
                    
                except Exception as e:
                    break
            
            print(f"      S&P Global: '{term}' complete - {len(headlines)} total")
        
        return headlines
    
    def scrape_marketwatch_deep(self) -> List[NewsHeadline]:
        """MarketWatch - Deep search"""
        headlines = []
        session = self._create_session()
        
        for page in range(1, 500):
            try:
                url = f"https://www.marketwatch.com/search?q=natural%20gas&page={page}"
                response = session.get(url, headers=self.headers, timeout=12)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all(['div', 'article'], class_=re.compile('article|searchresult|result'))
                
                if not articles:
                    break
                
                for article in articles:
                    try:
                        link = article.find('a', href=True)
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue
                        
                        date_elem = article.find('time')
                        if not date_elem:
                            date_elem = article.find(class_=re.compile('date|time', re.I))
                        
                        pub_date = self._parse_date(date_elem.get_text() if date_elem else "")
                        
                        headlines.append(NewsHeadline(
                            headline=title,
                            date=pub_date,
                            summary=""
                        ))
                    except:
                        continue
                
                time.sleep(0.3)
                
            except:
                break
        
        return headlines
    
    def scrape_seeking_alpha(self) -> List[NewsHeadline]:
        """Seeking Alpha natural gas articles"""
        headlines = []
        session = self._create_session()
        
        for page in range(1, 200):
            try:
                url = f"https://seekingalpha.com/market-news/all?page={page}&q=natural%20gas"
                response = session.get(url, headers=self.headers, timeout=12)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all(['article', 'div'], class_=re.compile('article'))
                
                if not articles:
                    break
                
                for article in articles:
                    try:
                        link = article.find('a', href=True)
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue
                        
                        date_elem = article.find('time')
                        pub_date = self._parse_date(date_elem.get_text() if date_elem else "")
                        
                        headlines.append(NewsHeadline(
                            headline=title,
                            date=pub_date,
                            summary=""
                        ))
                    except:
                        continue
                
                time.sleep(0.5)
                
            except:
                break
        
        return headlines
    
    def scrape_yahoo_finance(self) -> List[NewsHeadline]:
        """Yahoo Finance natural gas news"""
        headlines = []
        session = self._create_session()
        
        for offset in range(0, 1000, 20):
            try:
                url = f"https://finance.yahoo.com/search?p=natural+gas&offset={offset}"
                response = session.get(url, headers=self.headers, timeout=12)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all(['div', 'li'], class_=re.compile('search|result|article'))
                
                if not articles:
                    break
                
                for article in articles:
                    try:
                        link = article.find('a', href=True)
                        if not link:
                            continue
                        
                        title = link.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue
                        
                        headlines.append(NewsHeadline(
                            headline=title,
                            date=datetime.now().strftime('%Y-%m-%d'),
                            summary=""
                        ))
                    except:
                        continue
                
                time.sleep(0.4)
                
            except:
                break
        
        return headlines
    
    # ============================================================
    # MULTI-THREADED EXECUTION
    # ============================================================
    
    def run_all_scrapers(self) -> List[NewsHeadline]:
        """Execute all scrapers in parallel"""
        
        scraper_tasks = [
            ("Google News MASSIVE", self.scrape_google_news_massive),
            ("Natural Gas World EXTREME", self.scrape_natural_gas_world_extreme),
            ("OilPrice EXTREME", self.scrape_oilprice_extreme),
            ("MarketWatch DEEP", self.scrape_marketwatch_deep),
            ("S&P Global", self.scrape_spglobal_extreme),
            ("Seeking Alpha", self.scrape_seeking_alpha),
            ("Yahoo Finance", self.scrape_yahoo_finance),
        ]
        
        all_headlines = []
        
        print("\n" + "="*80)
        print("EXTREME NATURAL GAS NEWS SCRAPER - TARGETING 100,000+ HEADLINES")
        print("="*80)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {executor.submit(func): name for name, func in scraper_tasks}
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    headlines = future.result(timeout=600)
                    with self.lock:
                        all_headlines.extend(headlines)
                    print(f"\n  ✓ {source_name}: {len(headlines):,} headlines")
                except Exception as e:
                    print(f"\n  ✗ {source_name}: {str(e)[:80]}")
        
        print(f"\n{'='*80}")
        print(f"TOTAL COLLECTED: {len(all_headlines):,} raw headlines")
        print("="*80)
        
        return all_headlines
    
    # ============================================================
    # HELPERS - THIS IS WHERE THE NEW FUNCTIONS GO
    # ============================================================
    
    def _is_summary_useful(self, headline: str, summary: str) -> bool:
        """Check if summary adds meaningful information beyond the headline"""
        if not summary or len(summary.strip()) < 20:
            return False
        
        headline_norm = headline.lower().strip()
        summary_norm = summary.lower().strip()
        
        summary_clean = re.sub(r'^(summary:|description:|excerpt:)', '', summary_norm).strip()
        summary_clean = re.sub(r'\s*(read more|continue reading|full story).*$', '', summary_clean).strip()
        
        if summary_clean == headline_norm:
            return False
        
        if summary_clean.startswith(headline_norm):
            remainder = summary_clean[len(headline_norm):].strip()
            if len(remainder) < 30:
                return False
        
        headline_words = set(headline_norm.split())
        summary_words = set(summary_clean.split())
        
        if len(summary_words) > 0:
            overlap = len(headline_words & summary_words) / len(summary_words)
            if overlap > 0.8:
                return False
        
        return True
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        formats = [
            '%Y-%m-%d', '%b %d, %Y', '%B %d, %Y', '%m/%d/%Y', '%d/%m/%Y',
            '%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z',
            '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ',
            '%d %b %Y', '%d %B %Y', '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except:
                continue
        
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', date_str)
        if year_match:
            month_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', date_str, re.I)
            if month_match:
                months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
                month_num = months.get(month_match.group().lower()[:3], 6)
                return f"{year_match.group()}-{month_num:02d}-15"
            return f"{year_match.group()}-06-15"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def save_headlines(self, headlines: List[NewsHeadline]):
        """Save to database with cleaned summaries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved = 0
        duplicates = 0
        summaries_kept = 0
        summaries_removed = 0
        
        for h in headlines:
            try:
                unique_url = f"internal://{h.date}/{h.headline[:100]}"
                
                # Clean summary - only keep if it adds value
                cleaned_summary = ""
                if h.summary:
                    if self._is_summary_useful(h.headline, h.summary):
                        cleaned_summary = h.summary
                        summaries_kept += 1
                    else:
                        summaries_removed += 1
                
                cursor.execute('''INSERT OR IGNORE INTO headlines 
                    (headline, date, summary, url, source, category, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (h.headline, h.date, cleaned_summary, unique_url, 
                     "Various", "commodity", datetime.now().isoformat()))
                
                if cursor.rowcount > 0:
                    saved += 1
                else:
                    duplicates += 1
            except:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Saved {saved:,} new headlines")
        if duplicates > 0:
            print(f"  ⓘ Skipped {duplicates:,} duplicates")
        print(f"  ⓘ Summaries: {summaries_kept:,} kept, {summaries_removed:,} removed (redundant)")
    
    def get_statistics(self):
        """Show detailed database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM headlines')
        total = cursor.fetchone()[0]
        
        cursor.execute('''SELECT strftime('%Y', date) as year, COUNT(*) as cnt 
                         FROM headlines 
                         WHERE date >= '1997-01-01'
                         GROUP BY year 
                         ORDER BY year''')
        by_year = cursor.fetchall()
        
        cursor.execute('''SELECT MIN(date), MAX(date) FROM headlines''')
        date_range = cursor.fetchone()  # FIXED: Removed [0]
        
        cursor.execute('''SELECT COUNT(DISTINCT date) FROM headlines WHERE date >= '1997-01-01' ''')
        distinct_days = cursor.fetchone()[0]
        
        start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
        end_date = datetime.now()
        total_days = (end_date - start_date).days
        
        conn.close()
        
        print("\n" + "="*80)
        print("DATABASE STATISTICS")
        print("="*80)
        print(f"Total headlines: {total:,}")
        print(f"Date range: {date_range[0]} to {datetime.now().strftime('%Y-%m-%d')}")
        print(f"Days with headlines: {distinct_days:,} out of {total_days:,} total days")
        print(f"Coverage: {distinct_days/total_days*100:.1f}% of days have headlines")
        print(f"Average headlines per day: {total/max(distinct_days, 1):.1f}")
        
        print("\n" + "-"*80)
        print("COVERAGE BY YEAR:")
        print("-"*80)
        for year, count in by_year:
            if year:
                days_in_year = 366 if int(year) % 4 == 0 else 365
                avg_per_day = count / days_in_year
                print(f"  {year}: {count:,} headlines ({avg_per_day:.1f} avg/day)")
        
        print("\n" + "-"*80)
        print("COVERAGE BY DECADE:")
        print("-"*80)
        decades = {}
        for year, count in by_year:
            if year:
                decade = f"{year[:3]}0s"
                decades[decade] = decades.get(decade, 0) + count
        
        for decade in sorted(decades.keys()):
            print(f"  {decade}: {decades[decade]:,} headlines")
    
    def export_to_csv(self, output_file: str = "gas_headlines.csv"):
        """Export to CSV"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM headlines ORDER BY date DESC, scraped_at DESC', conn)
        conn.close()
        df.to_csv(output_file, index=False)
        print(f"\n✓ Exported {len(df):,} headlines to {output_file}")
    
    def export_to_json(self, output_file: str = "gas_headlines.json"):
        """Export to JSON with only headline, date, summary"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT headline, date, summary FROM headlines ORDER BY date DESC', conn)
        conn.close()
        df.to_json(output_file, orient='records', indent=2)
        print(f"✓ Exported {len(df):,} headlines to {output_file}")
    
    def run(self):
        """Main execution"""
        print("\n" + "="*80)
        print("EXTREME MULTI-SOURCE NATURAL GAS NEWS SCRAPER")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Workers: {self.max_workers}")
        print(f"Target: 100,000+ headlines from 1997-2025")
        
        start_time = time.time()
        
        headlines = self.run_all_scrapers()
        
        if headlines:
            self.save_headlines(headlines)
            self.get_statistics()
            self.export_to_csv()
            self.export_to_json()
        else:
            print("\n⚠ No headlines collected!")
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*80)
        print(f"✓ COMPLETE in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print("="*80)
        print(f"Database: {self.db_path}")
        print("CSV: gas_headlines.csv")
        print("JSON: gas_headlines.json")
        print("="*80)
        print("\nREADY FOR MODEL TRAINING!")
        print("You now have comprehensive daily coverage for price prediction.")
        print("="*80)


def main():
    scraper = MassiveGasNewsScraper(max_workers=20)
    scraper.run()


if __name__ == "__main__":
    main()