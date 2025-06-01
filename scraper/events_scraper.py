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

class BatmanEventsScraper:
    def __init__(self, base_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize the events scraper with timeline management
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        
        # Respectful headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BatmanEventsScraper/1.0; Educational Purpose)',
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
                logging.FileHandler('events_scraper.log'),
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
    
    def extract_event_timeline_info(self, soup: BeautifulSoup) -> Dict:
        """Extract timeline and event information"""
        details = {
            'event_type': '',  # origin, crisis, death, major event, character development
            'timeline_position': '',  # early career, middle career, late career, etc.
            'duration': '',  # single issue, arc, ongoing
            'scale': '',  # personal, city-wide, global, cosmic
            'key_participants': [],
            'locations_affected': [],
            'consequences': [],
            'timeline_era': '',  # Golden Age, Silver Age, Bronze Age, Modern Age
            'continuity_impact': 'low'  # low, medium, high (complexity indicator)
        }
        
        # Extract from infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            # Common event fields
            event_fields = {
                'event_type': ['type', 'event type', 'classification', 'category'],
                'duration': ['duration', 'length', 'timeline', 'span'],
                'scale': ['scale', 'scope', 'impact level'],
                'timeline_era': ['era', 'age', 'period', 'continuity'],
                'timeline_position': ['position', 'when', 'timing']
            }
            
            for data_div in infobox.find_all('div', {'data-source': True}):
                data_source = data_div.get('data-source', '').lower()
                text_content = data_div.get_text(strip=True)
                
                for detail_key, field_names in event_fields.items():
                    if any(field in data_source for field in field_names):
                        details[detail_key] = text_content
                        break
        
        # Extract event details from content
        content = soup.find('div', class_='mw-parser-output')
        if content:
            text = content.get_text().lower()
            
            # Key Batman characters involved
            key_characters = [
                'batman', 'bruce wayne', 'robin', 'dick grayson', 'tim drake',
                'jason todd', 'damian wayne', 'batgirl', 'barbara gordon', 'nightwing',
                'alfred pennyworth', 'commissioner gordon', 'joker', 'catwoman'
            ]
            
            # Locations that might be affected
            key_locations = [
                'gotham city', 'gotham', 'batcave', 'wayne manor', 'arkham asylum',
                'blackgate', 'gcpd', 'wayne enterprises', 'crime alley'
            ]
            
            # Types of consequences
            consequence_types = [
                'death', 'resurrection', 'identity revealed', 'retirement', 'injury',
                'new character introduced', 'character development', 'relationship change',
                'location destroyed', 'organization formed', 'villain defeated'
            ]
            
            # Event type classification
            if not details['event_type']:
                if any(word in text for word in ['origin', 'beginning', 'first time', 'how he became']):
                    details['event_type'] = 'origin event'
                elif any(word in text for word in ['death', 'died', 'killed', 'murder']):
                    details['event_type'] = 'death event'
                elif any(word in text for word in ['crisis', 'disaster', 'catastrophe', 'emergency']):
                    details['event_type'] = 'crisis event'
                elif any(word in text for word in ['revealed', 'exposed', 'discovered', 'unmasked']):
                    details['event_type'] = 'revelation event'
                elif any(word in text for word in ['battle', 'fight', 'war', 'conflict']):
                    details['event_type'] = 'conflict event'
                else:
                    details['event_type'] = 'major event'
            
            # Scale detection
            if not details['scale']:
                if any(word in text for word in ['world', 'global', 'earth', 'planet']):
                    details['scale'] = 'global'
                elif any(word in text for word in ['gotham', 'city', 'citywide']):
                    details['scale'] = 'city-wide'
                elif any(word in text for word in ['personal', 'private', 'individual']):
                    details['scale'] = 'personal'
                else:
                    details['scale'] = 'regional'
            
            # Find key participants (limit to avoid noise)
            for character in key_characters:
                if character in text and character not in details['key_participants']:
                    details['key_participants'].append(character)
                    if len(details['key_participants']) >= 6:  # Limit to 6 key participants
                        break
            
            # Find affected locations
            for location in key_locations:
                if location in text and location not in details['locations_affected']:
                    details['locations_affected'].append(location)
                    if len(details['locations_affected']) >= 4:  # Limit to 4 locations
                        break
            
            # Find consequences
            for consequence in consequence_types:
                if consequence in text and consequence not in details['consequences']:
                    details['consequences'].append(consequence)
                    if len(details['consequences']) >= 3:  # Limit to 3 main consequences
                        break
            
            # Assess continuity impact (complexity)
            complexity_indicators = [
                'multiverse', 'alternate timeline', 'retcon', 'continuity change',
                'reboot', 'crisis', 'reality alteration', 'dimension'
            ]
            
            complexity_count = sum(1 for indicator in complexity_indicators if indicator in text)
            
            if complexity_count == 0:
                details['continuity_impact'] = 'low'
            elif complexity_count <= 2:
                details['continuity_impact'] = 'medium'
            else:
                details['continuity_impact'] = 'high'
        
        return details
    
    def scrape_batman_event(self, event_name: str) -> Optional[Dict]:
        """Scrape a Batman event/timeline entry with detailed information"""
        base_url = "https://batman.fandom.com"
        url = f"{base_url}/wiki/{event_name.replace(' ', '_')}"
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        event_data = {
            'name': event_name,
            'url': url,
            'category': '',
            'description': '',
            'simple_summary': '',  # Simplified for timeline clarity
            'details': {},
            'related_events': [],
            'chronological_order': ''
        }
        
        try:
            # Get event category
            categories = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
            for cat in categories:
                cat_text = cat.get_text().lower()
                if any(event_type in cat_text for event_type in ['event', 'crisis', 'storyline', 'timeline', 'history']):
                    event_data['category'] = cat.get_text()
                    break
            
            # Get description from article content
            content = soup.find('div', class_='mw-parser-output')
            if content:
                # Remove infobox and unwanted elements
                for unwanted in content.find_all(['aside', 'table'], class_=['portable-infobox', 'infobox']):
                    unwanted.decompose()
                
                paragraphs = content.find_all('p')
                for para in paragraphs:
                    text = para.get_text(strip=True)
                    
                    if (len(text) > 80 and 
                        not text.startswith('For ') and 
                        any(word in text.lower() for word in ['event', 'happened', 'occurred', 'batman', 'gotham', 'crisis'])):
                        clean_text = re.sub(r'\s+', ' ', text.strip())
                        event_data['description'] = clean_text[:700] + '...' if len(clean_text) > 700 else clean_text
                        
                        # Create simple summary (remove complex timeline references)
                        simple_text = clean_text
                        complexity_terms = [
                            'however', 'but later', 'this was retconned', 'in an alternate',
                            'pre-crisis', 'post-crisis', 'earth-1', 'earth-2', 'multiverse'
                        ]
                        
                        for term in complexity_terms:
                            if term in simple_text.lower():
                                # Cut off at the complex part
                                simple_text = simple_text[:simple_text.lower().find(term)].strip()
                        
                        event_data['simple_summary'] = simple_text[:400] + '...' if len(simple_text) > 400 else simple_text
                        break
            
            # Extract detailed event information
            event_data['details'] = self.extract_event_timeline_info(soup)
            
            # Mark high-complexity events
            if event_data['details']['continuity_impact'] == 'high':
                self.logger.warning(f"⚠️ {event_name} marked as high complexity event")
            
            self.logger.info(f"Successfully scraped event data for {event_name}")
            return event_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {event_name}: {e}")
            return None
    
    def get_batman_events_list(self, use_categories: bool = True, focus_on_clear: bool = True) -> List[str]:
        """Get curated list of Batman events and timeline moments"""
        
        discovered_events = []
        
        # Start with category discovery if requested
        if use_categories:
            self.logger.info("Discovering events from categories...")
            discovered_events = self.get_events_from_categories()
        
        # Curated events list - focusing on clear, major events
        if focus_on_clear:
            # Clear, impactful Batman events
            curated_events = [
                # Origin & Early Career
                "Death_of_Thomas_and_Martha_Wayne", "Batman's_First_Case", "Meeting_Robin", 
                "Formation_of_Dynamic_Duo", "Dick_Grayson_Becomes_Robin", "Batman_Year_One_Events",
                
                # Major Character Deaths/Changes
                "Death_of_Jason_Todd", "Barbara_Gordon_Paralyzed", "Tim_Drake_Becomes_Robin",
                "Dick_Grayson_Becomes_Nightwing", "Damian_Wayne_Introduced", "Death_of_Alfred",
                
                # Major Villain Events
                "Joker's_First_Crime", "Two-Face_Origin", "Penguin_First_Appearance",
                "Bane_Breaks_Batman's_Back", "Ra's_al_Ghul_Revealed", "Court_of_Owls_Revealed",
                
                # Gotham City Events
                "Gotham_Earthquake", "No_Man's_Land_Period", "Arkham_Asylum_Breakout",
                "Wayne_Manor_Destroyed", "Batcave_Discovered", "GCPD_Corruption_Exposed",
                
                # Identity & Relationship Events
                "Batman_Identity_Crisis", "Bruce_Wayne_Presumed_Dead", "Return_of_Bruce_Wayne",
                "Batman_and_Catwoman_Romance", "Commissioner_Gordon_Retires", "Oracle_Revealed",
                
                # Team Formation Events
                "Justice_League_Formation", "Outsiders_Created", "Birds_of_Prey_Founded",
                "Batman_Inc_Established", "Teen_Titans_Formed", "Dynamic_Duo_Ended",
                
                # Major Conflicts
                "War_Against_Crime_Families", "Arkham_War", "Gang_War", "Mob_War",
                "League_of_Assassins_Conflict", "Court_of_Owls_War", "Joker_War",
                
                # Technology & Resources
                "Batcave_Construction", "First_Batmobile", "Wayne_Enterprises_Founded",
                "Oracle_Computer_Network", "Batman_Beyond_Future", "Watchtower_Built",
                
                # Personal Milestones
                "Bruce_Wayne_Inherits_Fortune", "Alfred_Joins_Wayne_Family", "First_Love_Interest",
                "Retirement_Attempts", "Training_Completion", "First_Teamup"
            ]
        else:
            # Include complex crossover events
            curated_events = [
                "Crisis_on_Infinite_Earths_Impact", "Zero_Hour_Changes", "Final_Crisis_Events",
                "Flashpoint_Alterations", "New_52_Reboot", "Rebirth_Restoration", "Dark_Nights_Metal",
                "Convergence_Events", "Infinite_Crisis_Changes", "Identity_Crisis_Revelations"
            ]
        
        # Merge discovered and curated events
        all_events = discovered_events.copy()
        for event in curated_events:
            if event not in all_events:
                all_events.append(event)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_events = []
        for event in all_events:
            if event not in seen:
                seen.add(event)
                unique_events.append(event)
        
        self.logger.info(f"Found {len(unique_events)} Batman events to scrape")
        self.logger.info(f"Focus mode: {'Clear/Major Events' if focus_on_clear else 'Including Complex'}")
        return unique_events
    
    def get_events_from_categories(self) -> List[str]:
        """Get events from Batman Wiki categories"""
        event_names = []
        
        # Batman event category pages
        category_urls = [
            "https://batman.fandom.com/wiki/Category:Events",
            "https://batman.fandom.com/wiki/Category:Timeline",
            "https://batman.fandom.com/wiki/Category:History",
            "https://batman.fandom.com/wiki/Category:Major_Events"
        ]
        
        for url in category_urls:
            self.logger.info(f"Getting event list from: {url}")
            response = self.safe_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find event links in category
                category_content = soup.find('div', class_='category-page__members')
                if not category_content:
                    category_content = soup.find('div', class_='mw-category')
                
                if category_content:
                    event_links = category_content.find_all('a', href=True)
                    for link in event_links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        # Filter for actual event pages
                        if ('/wiki/' in href and 
                            ':' not in href and 
                            'Category:' not in href and
                            'Template:' not in href and
                            'File:' not in href and
                            title and len(title) > 1):
                            event_name = href.replace('/wiki/', '')
                            if event_name and event_name not in event_names:
                                event_names.append(event_name)
        
        return event_names
    
    def scrape_batman_events_comprehensive(self, limit: int = None, clear_mode: bool = True) -> List[Dict]:
        """Scrape comprehensive Batman events database with timeline management"""
        
        event_names = self.get_batman_events_list(use_categories=True, focus_on_clear=clear_mode)
        events_data = []
        
        # If no limit specified, scrape ALL discovered events
        if limit is None:
            total_events = len(event_names)
            mode_text = "CLEAR" if clear_mode else "COMPLEX"
            self.logger.info(f"Starting COMPLETE {mode_text} scrape of ALL {total_events} Batman events...")
        else:
            total_events = min(limit, len(event_names))
            self.logger.info(f"Starting to scrape {total_events} Batman events...")
        
        events_to_scrape = event_names if limit is None else event_names[:limit]
        successful_scrapes = 0
        failed_scrapes = 0
        complex_events = 0
        
        for i, event in enumerate(events_to_scrape):
            self.logger.info(f"Scraping event {i+1}/{total_events}: {event}")
            data = self.scrape_batman_event(event)
            
            if data:
                events_data.append(data)
                successful_scrapes += 1
                
                # Track complexity
                if data['details'].get('continuity_impact') == 'high':
                    complex_events += 1
                
                self.logger.info(f"✅ Successfully scraped {event}")
            else:
                failed_scrapes += 1
                self.logger.warning(f"❌ Failed to scrape {event}")
            
            # Save periodically (every 5 events - smaller batches for timeline data)
            if (i + 1) % 5 == 0:
                self.save_to_json(events_data, f'batman_events_partial_{i+1}.json')
                self.logger.info(f"💾 Saved partial event data: {successful_scrapes} events")
                self.logger.info(f"📊 Progress: {successful_scrapes} success, {failed_scrapes} failed, {complex_events} complex")
            
            # Politeness break every 20 events
            if (i + 1) % 20 == 0:
                self.logger.info("😴 Taking a 3-minute politeness break...")
                time.sleep(180)
        
        # Final summary
        self.logger.info(f"🏁 EVENTS SCRAPING COMPLETE!")
        self.logger.info(f"📊 Final Results: {successful_scrapes} successful, {failed_scrapes} failed")
        self.logger.info(f"📈 Success Rate: {(successful_scrapes/total_events)*100:.1f}%")
        self.logger.info(f"⚠️ Complex Events: {complex_events} ({(complex_events/successful_scrapes)*100:.1f}% of successful)")
        
        return events_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'batman_events.json'):
        """Save scraped event data to JSON file"""
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Event data saved to {filepath}")

if __name__ == "__main__":
    import sys
    
    print("Batman Events & Timeline Scraper")
    print("=" * 40)
    print("1. Quick test (3 major events, ~45 seconds)")
    print("2. CLEAR mode (major events only, 1-2 hours)")
    print("3. COMPLETE mode (all events including complex, 3-4 hours)")
    print("4. Custom amount")
    
    mode = input("\nChoose mode (1/2/3/4): ").strip()
    
    scraper = BatmanEventsScraper(base_delay=2.0, max_delay=4.0)
    
    if mode == "1":
        print("\nStarting quick events test...")
        # Test with clear, major Batman events
        test_events = ["Death_of_Jason_Todd", "Bane_Breaks_Batman's_Back", "Dick_Grayson_Becomes_Nightwing"]
        events_data = []
        for event in test_events:
            data = scraper.scrape_batman_event(event)
            if data:
                events_data.append(data)
        scraper.save_to_json(events_data, 'test_batman_events.json')
        filename = 'test_batman_events.json'
        
    elif mode == "2":
        print("\nStarting CLEAR events scrape...")
        print("This focuses on major, well-documented Batman timeline events")
        print("Avoids complex multiverse/continuity events")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        events = scraper.scrape_batman_events_comprehensive(limit=None, clear_mode=True)
        scraper.save_to_json(events, 'batman_events_CLEAR.json')
        filename = 'batman_events_CLEAR.json'
        
    elif mode == "3":
        print("\nStarting COMPLETE events scrape...")
        print("This includes ALL events, including complex crossover events")
        print("Warning: Some events may have confusing timeline implications")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        events = scraper.scrape_batman_events_comprehensive(limit=None, clear_mode=False)
        scraper.save_to_json(events, 'batman_events_COMPLETE.json')
        filename = 'batman_events_COMPLETE.json'
        
    elif mode == "4":
        try:
            limit = int(input("How many events? "))
            clear_mode = input("Clear mode only? (y/n): ").strip().lower() == 'y'
            events = scraper.scrape_batman_events_comprehensive(limit=limit, clear_mode=clear_mode)
            mode_suffix = "_CLEAR" if clear_mode else "_COMPLEX"
            scraper.save_to_json(events, f'batman_events_{limit}{mode_suffix}.json')
            filename = f'batman_events_{limit}{mode_suffix}.json'
        except ValueError:
            print("Invalid number")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if 'events' in locals() or 'events_data' in locals():
        data = events if 'events' in locals() else events_data
        print(f"\n✅ Successfully scraped {len(data)} events!")
        print(f"📁 Saved to: data/{filename}")
        print(f"📋 Log file: events_scraper.log")
        
        if data:
            print(f"\nSample event: {data[0]['name']}")
            details = data[0].get('details', {})
            if details.get('event_type'):
                print(f"Type: {details['event_type']}")
            if details.get('scale'):
                print(f"Scale: {details['scale']}")
            if details.get('continuity_impact'):
                print(f"Complexity: {details['continuity_impact']}")
    else:
        print("❌ No data collected. Check events_scraper.log for issues.")