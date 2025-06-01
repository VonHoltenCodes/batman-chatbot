import requests
import time
import random
import logging
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import json
import sqlite3
from typing import List, Dict, Optional
import os
import re

class BatmanStorylinescraper:
    def __init__(self, base_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize the storylines scraper with complexity management
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        
        # Respectful headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BatmanStorylinescraper/1.0; Educational Purpose)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('storylines_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track requests for politeness
        self.request_count = 0
        self.last_request_time = 0
    
    def respectful_delay(self):
        """Add random delay between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        delay = random.uniform(self.base_delay, self.max_delay)
        
        if time_since_last < self.base_delay:
            delay += (self.base_delay - time_since_last)
        
        self.logger.info(f"Waiting {delay:.2f} seconds before next request...")
        time.sleep(delay)
        self.last_request_time = time.time()
    
    def safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a safe request with error handling and retries"""
        self.respectful_delay()
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Requesting: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 429:
                    wait_time = 60 * (attempt + 1)
                    self.logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 200:
                    self.request_count += 1
                    self.logger.info(f"Success! Total requests: {self.request_count}")
                    return response
                
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def simplify_storyline_content(self, text: str) -> str:
        """Simplify complex storyline text to avoid confusion"""
        
        # Remove overly complex sentences and jargon
        complexity_indicators = [
            'continuity', 'retcon', 'timeline', 'parallel universe', 'alternate reality',
            'pre-crisis', 'post-crisis', 'new 52', 'rebirth', 'flashpoint',
            'earth-1', 'earth-2', 'multiverse', 'dimensional', 'reality-altering'
        ]
        
        # Split into sentences
        sentences = text.split('. ')
        simplified_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Skip sentences with too many complexity indicators
            complexity_count = sum(1 for indicator in complexity_indicators if indicator in sentence_lower)
            
            # Skip overly complex sentences
            if (complexity_count <= 1 and 
                len(sentence) < 200 and  # Reasonable length
                not sentence_lower.startswith('in an alternate') and
                not sentence_lower.startswith('this was later retconned') and
                'however' not in sentence_lower[:50]):  # Avoid contradiction sentences
                simplified_sentences.append(sentence.strip())
        
        # Reconstruct simplified text
        simplified_text = '. '.join(simplified_sentences)
        
        # Clean up
        simplified_text = re.sub(r'\s+', ' ', simplified_text)
        
        return simplified_text[:500] + '...' if len(simplified_text) > 500 else simplified_text
    
    def extract_storyline_details(self, soup: BeautifulSoup) -> Dict:
        """Extract clean storyline information avoiding complexity"""
        details = {
            'publication_year': '',
            'story_type': '',  # arc, event, miniseries, graphic novel
            'timeline_era': '',  # Golden Age, Silver Age, Modern Age, etc.
            'main_characters': [],
            'main_villains': [],
            'key_events': [],
            'consequences': '',
            'reading_order': '',
            'complexity_level': 'moderate'  # simple, moderate, complex
        }
        
        # Extract from infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            storyline_fields = {
                'publication_year': ['published', 'publication date', 'year', 'date'],
                'story_type': ['type', 'format', 'series type'],
                'timeline_era': ['era', 'continuity', 'timeline'],
                'reading_order': ['reading order', 'order', 'sequence']
            }
            
            for data_div in infobox.find_all('div', {'data-source': True}):
                data_source = data_div.get('data-source', '').lower()
                text_content = data_div.get_text(strip=True)
                
                for detail_key, field_names in storyline_fields.items():
                    if any(field in data_source for field in field_names):
                        details[detail_key] = text_content
                        break
        
        # Extract characters and events from content (carefully)
        content = soup.find('div', class_='mw-parser-output')
        if content:
            text = content.get_text().lower()
            
            # Main Batman characters (limit to core cast)
            main_characters = [
                'batman', 'bruce wayne', 'robin', 'dick grayson', 'tim drake',
                'jason todd', 'damian wayne', 'batgirl', 'barbara gordon', 
                'nightwing', 'alfred pennyworth', 'commissioner gordon'
            ]
            
            # Major villains
            main_villains = [
                'joker', 'two-face', 'penguin', 'riddler', 'catwoman', 'bane',
                'scarecrow', 'ra\'s al ghul', 'talia al ghul', 'harley quinn',
                'poison ivy', 'mr. freeze', 'clayface', 'killer croc'
            ]
            
            # Key story events (simple, clear events)
            story_events = [
                'origin story', 'first appearance', 'death', 'resurrection', 'retirement',
                'identity revealed', 'team formation', 'betrayal', 'redemption',
                'marriage', 'partnership', 'villain origin', 'hero\'s journey'
            ]
            
            # Find main characters (limit to avoid noise)
            for character in main_characters:
                if character in text and character not in details['main_characters']:
                    details['main_characters'].append(character)
                    if len(details['main_characters']) >= 6:  # Limit to 6 main characters
                        break
            
            # Find main villains (limit to avoid noise)
            for villain in main_villains:
                if villain in text and villain not in details['main_villains']:
                    details['main_villains'].append(villain)
                    if len(details['main_villains']) >= 4:  # Limit to 4 main villains
                        break
            
            # Find key events (simple ones only)
            for event in story_events:
                if event in text and event not in details['key_events']:
                    details['key_events'].append(event)
                    if len(details['key_events']) >= 3:  # Limit to 3 key events
                        break
            
            # Assess complexity level
            complexity_indicators = [
                'multiverse', 'alternate timeline', 'retcon', 'continuity error',
                'parallel universe', 'dimensional', 'crisis event', 'reality-altering'
            ]
            
            complexity_count = sum(1 for indicator in complexity_indicators if indicator in text)
            
            if complexity_count == 0:
                details['complexity_level'] = 'simple'
            elif complexity_count <= 2:
                details['complexity_level'] = 'moderate'
            else:
                details['complexity_level'] = 'complex'
        
        return details
    
    def scrape_batman_storyline(self, storyline_name: str) -> Optional[Dict]:
        """Scrape a Batman storyline with complexity management"""
        base_url = "https://batman.fandom.com"
        url = f"{base_url}/wiki/{storyline_name.replace(' ', '_')}"
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        storyline_data = {
            'name': storyline_name,
            'url': url,
            'category': '',
            'description': '',
            'simple_summary': '',  # Simplified version for chatbot
            'details': {},
            'related_stories': [],
            'recommended_reading': []
        }
        
        try:
            # Get storyline category
            categories = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
            for cat in categories:
                cat_text = cat.get_text().lower()
                if any(story_type in cat_text for story_type in ['story', 'storyline', 'arc', 'event', 'comic', 'graphic novel']):
                    storyline_data['category'] = cat.get_text()
                    break
            
            # Get full description
            content = soup.find('div', class_='mw-parser-output')
            if content:
                # Remove infobox and unwanted elements
                for unwanted in content.find_all(['aside', 'table'], class_=['portable-infobox', 'infobox']):
                    unwanted.decompose()
                
                paragraphs = content.find_all('p')
                for para in paragraphs:
                    text = para.get_text(strip=True)
                    
                    if (len(text) > 100 and 
                        not text.startswith('For ') and 
                        any(word in text.lower() for word in ['batman', 'story', 'comic', 'storyline', 'arc', 'event'])):
                        storyline_data['description'] = text[:800] + '...' if len(text) > 800 else text
                        
                        # Create simplified version
                        storyline_data['simple_summary'] = self.simplify_storyline_content(text)
                        break
            
            # Extract detailed storyline information
            storyline_data['details'] = self.extract_storyline_details(soup)
            
            # Mark as complex if needed
            if storyline_data['details']['complexity_level'] == 'complex':
                self.logger.warning(f"⚠️ {storyline_name} marked as complex storyline")
            
            self.logger.info(f"Successfully scraped storyline data for {storyline_name}")
            return storyline_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {storyline_name}: {e}")
            return None
    
    def get_batman_storylines_list(self, use_categories: bool = True, focus_on_simple: bool = True) -> List[str]:
        """Get curated list of Batman storylines, focusing on clear, well-known stories"""
        
        discovered_storylines = []
        
        # Start with category discovery if requested
        if use_categories:
            self.logger.info("Discovering storylines from categories...")
            discovered_storylines = self.get_storylines_from_categories()
        
        # Curated storylines list - focusing on clear, iconic stories
        if focus_on_simple:
            # Simple, iconic storylines first
            curated_storylines = [
                # Foundational/Origin Stories
                "Batman:_Year_One", "Batman_Begins", "The_Man_Who_Falls", "Batman:_Zero_Year",
                
                # Classic Storylines (well-defined)
                "The_Killing_Joke", "The_Dark_Knight_Returns", "Batman:_The_Long_Halloween",
                "Batman:_Dark_Victory", "Batman:_Hush", "Batman:_Under_the_Red_Hood",
                
                # Major Villain Arcs
                "Death_in_the_Family", "A_Lonely_Place_of_Dying", "Knightfall", "No_Man's_Land",
                "The_Court_of_Owls", "Death_of_the_Family", "Endgame", "I_Am_Gotham",
                
                # Character Development
                "Robin:_Year_One", "Batgirl:_Year_One", "Nightwing:_Year_One",
                "Red_Hood:_The_Lost_Days", "Batman_and_Robin:_Born_to_Kill",
                
                # Team Stories
                "JLA:_Tower_of_Babel", "Batman_and_the_Outsiders", "Birds_of_Prey",
                
                # Movie/TV Adaptations
                "Batman_'89", "Batman_Returns", "Batman_Forever", "Batman_&_Robin",
                "The_Dark_Knight_Trilogy", "Batman_Begins_(comic)", "Batman_v_Superman",
                
                # Animated Stories
                "Batman:_The_Animated_Series", "Batman_Beyond", "Justice_League_Animated",
                
                # Recent Clear Stories
                "Batman:_White_Knight", "Batman:_Black_Mirror", "Batman:_Earth_One",
                "All-Star_Batman_and_Robin", "Batman:_The_Brave_and_the_Bold"
            ]
        else:
            # Include more complex storylines
            curated_storylines = [
                # Add complex crossover events
                "Crisis_on_Infinite_Earths", "Zero_Hour", "Final_Crisis", "Flashpoint",
                "The_New_52", "DC_Rebirth", "Dark_Nights:_Metal", "Dark_Nights:_Death_Metal",
                
                # Complex Batman events
                "Batman:_Cataclysm", "Batman:_Legacy", "Bruce_Wayne:_Murderer?",
                "Bruce_Wayne:_Fugitive", "War_Games", "Face_the_Face", "Batman_R.I.P.",
                "Battle_for_the_Cowl", "Batman_Incorporated", "Night_of_the_Owls"
            ]
        
        # Merge discovered and curated storylines
        all_storylines = discovered_storylines.copy()
        for storyline in curated_storylines:
            if storyline not in all_storylines:
                all_storylines.append(storyline)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_storylines = []
        for storyline in all_storylines:
            if storyline not in seen:
                seen.add(storyline)
                unique_storylines.append(storyline)
        
        self.logger.info(f"Found {len(unique_storylines)} Batman storylines to scrape")
        self.logger.info(f"Focus mode: {'Simple/Iconic' if focus_on_simple else 'Including Complex'}")
        return unique_storylines
    
    def get_storylines_from_categories(self) -> List[str]:
        """Get storylines from Batman Wiki categories"""
        storyline_names = []
        
        # Batman storyline category pages
        category_urls = [
            "https://batman.fandom.com/wiki/Category:Comic_Stories",
            "https://batman.fandom.com/wiki/Category:Batman_Stories",
            "https://batman.fandom.com/wiki/Category:Story_Arcs",
            "https://batman.fandom.com/wiki/Category:Graphic_Novels"
        ]
        
        for url in category_urls:
            self.logger.info(f"Getting storyline list from: {url}")
            response = self.safe_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find storyline links in category
                category_content = soup.find('div', class_='category-page__members')
                if not category_content:
                    category_content = soup.find('div', class_='mw-category')
                
                if category_content:
                    storyline_links = category_content.find_all('a', href=True)
                    for link in storyline_links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        # Filter for actual storyline pages
                        if ('/wiki/' in href and 
                            ':' not in href and 
                            'Category:' not in href and
                            'Template:' not in href and
                            'File:' not in href and
                            title and len(title) > 1):
                            storyline_name = href.replace('/wiki/', '')
                            if storyline_name and storyline_name not in storyline_names:
                                storyline_names.append(storyline_name)
        
        return storyline_names
    
    def scrape_batman_storylines_comprehensive(self, limit: int = None, simple_mode: bool = True) -> List[Dict]:
        """Scrape comprehensive Batman storylines database with complexity management"""
        
        storyline_names = self.get_batman_storylines_list(use_categories=True, focus_on_simple=simple_mode)
        storylines_data = []
        
        # If no limit specified, scrape ALL discovered storylines
        if limit is None:
            total_storylines = len(storyline_names)
            mode_text = "SIMPLE" if simple_mode else "COMPLEX"
            self.logger.info(f"Starting COMPLETE {mode_text} scrape of ALL {total_storylines} Batman storylines...")
        else:
            total_storylines = min(limit, len(storyline_names))
            self.logger.info(f"Starting to scrape {total_storylines} Batman storylines...")
        
        storylines_to_scrape = storyline_names if limit is None else storyline_names[:limit]
        successful_scrapes = 0
        failed_scrapes = 0
        complex_storylines = 0
        
        for i, storyline in enumerate(storylines_to_scrape):
            self.logger.info(f"Scraping storyline {i+1}/{total_storylines}: {storyline}")
            data = self.scrape_batman_storyline(storyline)
            
            if data:
                storylines_data.append(data)
                successful_scrapes += 1
                
                # Track complexity
                if data['details'].get('complexity_level') == 'complex':
                    complex_storylines += 1
                
                self.logger.info(f"✅ Successfully scraped {storyline}")
            else:
                failed_scrapes += 1
                self.logger.warning(f"❌ Failed to scrape {storyline}")
            
            # Save periodically (every 5 storylines - smaller batches)
            if (i + 1) % 5 == 0:
                self.save_to_json(storylines_data, f'batman_storylines_partial_{i+1}.json')
                self.logger.info(f"💾 Saved partial storyline data: {successful_scrapes} storylines")
                self.logger.info(f"📊 Progress: {successful_scrapes} success, {failed_scrapes} failed, {complex_storylines} complex")
            
            # Politeness break every 20 storylines
            if (i + 1) % 20 == 0:
                self.logger.info("😴 Taking a 3-minute politeness break...")
                time.sleep(180)
        
        # Final summary
        self.logger.info(f"🏁 STORYLINES SCRAPING COMPLETE!")
        self.logger.info(f"📊 Final Results: {successful_scrapes} successful, {failed_scrapes} failed")
        self.logger.info(f"📈 Success Rate: {(successful_scrapes/total_storylines)*100:.1f}%")
        self.logger.info(f"⚠️ Complex Storylines: {complex_storylines} ({(complex_storylines/successful_scrapes)*100:.1f}% of successful)")
        
        return storylines_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'batman_storylines.json'):
        """Save scraped storyline data to JSON file"""
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Storyline data saved to {filepath}")

if __name__ == "__main__":
    import sys
    
    print("Batman Storylines Scraper")
    print("=" * 40)
    print("1. Quick test (3 iconic storylines, ~45 seconds)")
    print("2. SIMPLE mode (iconic storylines only, 1-2 hours)")
    print("3. COMPLETE mode (all storylines including complex, 3-5 hours)")
    print("4. Custom amount")
    
    mode = input("\nChoose mode (1/2/3/4): ").strip()
    
    scraper = BatmanStorylinescraper(base_delay=2.0, max_delay=4.0)
    
    if mode == "1":
        print("\nStarting quick storyline test...")
        # Test with clear, iconic storylines
        test_storylines = ["Batman:_Year_One", "The_Killing_Joke", "The_Dark_Knight_Returns"]
        storylines_data = []
        for storyline in test_storylines:
            data = scraper.scrape_batman_storyline(storyline)
            if data:
                storylines_data.append(data)
        scraper.save_to_json(storylines_data, 'test_batman_storylines.json')
        filename = 'test_batman_storylines.json'
        
    elif mode == "2":
        print("\nStarting SIMPLE storylines scrape...")
        print("This focuses on iconic, well-known storylines with clear plots")
        print("Avoids complex multiverse/continuity stories")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        storylines = scraper.scrape_batman_storylines_comprehensive(limit=None, simple_mode=True)
        scraper.save_to_json(storylines, 'batman_storylines_SIMPLE.json')
        filename = 'batman_storylines_SIMPLE.json'
        
    elif mode == "3":
        print("\nStarting COMPLETE storylines scrape...")
        print("This includes ALL storylines, including complex crossover events")
        print("Warning: Some stories may have confusing continuity issues")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        storylines = scraper.scrape_batman_storylines_comprehensive(limit=None, simple_mode=False)
        scraper.save_to_json(storylines, 'batman_storylines_COMPLETE.json')
        filename = 'batman_storylines_COMPLETE.json'
        
    elif mode == "4":
        try:
            limit = int(input("How many storylines? "))
            simple_mode = input("Simple mode only? (y/n): ").strip().lower() == 'y'
            storylines = scraper.scrape_batman_storylines_comprehensive(limit=limit, simple_mode=simple_mode)
            mode_suffix = "_SIMPLE" if simple_mode else "_COMPLEX"
            scraper.save_to_json(storylines, f'batman_storylines_{limit}{mode_suffix}.json')
            filename = f'batman_storylines_{limit}{mode_suffix}.json'
        except ValueError:
            print("Invalid number")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if 'storylines' in locals() or 'storylines_data' in locals():
        data = storylines if 'storylines' in locals() else storylines_data
        print(f"\n✅ Successfully scraped {len(data)} storylines!")
        print(f"📁 Saved to: data/{filename}")
        print(f"📋 Log file: storylines_scraper.log")
        
        if data:
            print(f"\nSample storyline: {data[0]['name']}")
            complexity = data[0].get('details', {}).get('complexity_level', 'unknown')
            print(f"Complexity level: {complexity}")
            if data[0].get('simple_summary'):
                print(f"Summary: {data[0]['simple_summary'][:100]}...")
    else:
        print("❌ No data collected. Check storylines_scraper.log for issues.")