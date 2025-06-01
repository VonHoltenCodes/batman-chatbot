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

class BatmanLocationsScraper:
    def __init__(self, base_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize the locations scraper with safety features
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        
        # Respectful headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BatmanLocationsScraper/1.0; Educational Purpose)',
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
                logging.FileHandler('locations_scraper.log'),
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
    
    def extract_location_details(self, soup: BeautifulSoup) -> Dict:
        """Extract detailed location information from infobox and content"""
        details = {
            'type': '',
            'district': '',
            'address': '',
            'owner': '',
            'security_level': '',
            'notable_features': [],
            'residents': [],
            'security_systems': [],
            'first_appearance': '',
            'status': 'active'
        }
        
        # Extract from infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            # Common location fields
            location_fields = {
                'type': ['type', 'category', 'classification'],
                'district': ['district', 'neighborhood', 'area', 'location'],
                'address': ['address', 'location', 'coordinates'],
                'owner': ['owner', 'owned by', 'proprietor', 'controlled by'],
                'security_level': ['security', 'security level', 'protection'],
                'first_appearance': ['first appearance', 'debut'],
                'status': ['status', 'condition', 'state']
            }
            
            for data_div in infobox.find_all('div', {'data-source': True}):
                data_source = data_div.get('data-source', '').lower()
                text_content = data_div.get_text(strip=True)
                
                # Match field names
                for detail_key, field_names in location_fields.items():
                    if any(field in data_source for field in field_names):
                        details[detail_key] = text_content
                        break
        
        # Extract features and characteristics from content
        content = soup.find('div', class_='mw-parser-output')
        if content:
            text = content.get_text().lower()
            
            # Notable features keywords
            feature_keywords = [
                'secret entrance', 'hidden passage', 'underground', 'rooftop access',
                'computer system', 'training area', 'laboratory', 'garage', 'hangar',
                'medical bay', 'trophy room', 'prison cells', 'containment', 'vault',
                'elevator', 'waterfall entrance', 'cave system', 'subway access',
                'helicopter pad', 'boat dock', 'weapons cache', 'surveillance system'
            ]
            
            # Security systems
            security_keywords = [
                'laser grid', 'motion sensors', 'pressure plates', 'guard patrol',
                'camera system', 'alarm system', 'biometric scanner', 'keycard access',
                'facial recognition', 'retinal scanner', 'voice recognition',
                'titanium doors', 'reinforced walls', 'bulletproof glass',
                'electromagnetic locks', 'security checkpoint', 'guard tower'
            ]
            
            # Notable residents/occupants
            resident_keywords = [
                'batman', 'bruce wayne', 'alfred', 'robin', 'batgirl', 'nightwing',
                'joker', 'penguin', 'riddler', 'two-face', 'catwoman', 'bane',
                'commissioner gordon', 'harvey bullock', 'prisoners', 'inmates',
                'staff', 'employees', 'workers', 'guards', 'doctors'
            ]
            
            # Find notable features
            for feature in feature_keywords:
                if feature in text and feature not in details['notable_features']:
                    details['notable_features'].append(feature)
            
            # Find security systems
            for security in security_keywords:
                if security in text and security not in details['security_systems']:
                    details['security_systems'].append(security)
            
            # Find residents (limited to avoid too much noise)
            for resident in resident_keywords:
                if resident in text and resident not in details['residents']:
                    details['residents'].append(resident)
                    if len(details['residents']) >= 10:  # Limit to top 10
                        break
        
        return details
    
    def scrape_batman_location(self, location_name: str) -> Optional[Dict]:
        """Scrape a Batman location page with detailed information"""
        base_url = "https://batman.fandom.com"
        url = f"{base_url}/wiki/{location_name.replace(' ', '_')}"
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        location_data = {
            'name': location_name,
            'url': url,
            'category': '',
            'description': '',
            'details': {},
            'aliases': [],
            'connected_locations': [],
            'notable_events': []
        }
        
        try:
            # Get location category from page categories
            categories = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
            for cat in categories:
                cat_text = cat.get_text().lower()
                if any(loc_type in cat_text for loc_type in ['location', 'building', 'district', 'neighborhood', 'facility']):
                    location_data['category'] = cat.get_text()
                    break
            
            # Get aliases from infobox
            infobox = soup.find('aside', class_='portable-infobox')
            if infobox:
                alias_section = infobox.find('div', {'data-source': 'alias'})
                if alias_section:
                    aliases = alias_section.get_text(strip=True).split(',')
                    location_data['aliases'] = [alias.strip() for alias in aliases]
            
            # Get description from article content
            content = soup.find('div', class_='mw-parser-output')
            if content:
                # Remove infobox and unwanted elements
                for unwanted in content.find_all(['aside', 'table'], class_=['portable-infobox', 'infobox']):
                    unwanted.decompose()
                
                paragraphs = content.find_all('p')
                for para in paragraphs:
                    text = para.get_text(strip=True)
                    
                    if (len(text) > 50 and 
                        not text.startswith('For ') and 
                        any(word in text.lower() for word in ['located', 'building', 'facility', 'district', 'area', 'gotham', 'wayne'])):
                        clean_text = re.sub(r'\s+', ' ', text.strip())
                        location_data['description'] = clean_text[:600] + '...' if len(clean_text) > 600 else clean_text
                        break
            
            # Extract detailed location information
            location_data['details'] = self.extract_location_details(soup)
            
            self.logger.info(f"Successfully scraped location data for {location_name}")
            return location_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {location_name}: {e}")
            return None
    
    def get_gotham_locations_list(self, use_categories: bool = True) -> List[str]:
        """Get comprehensive list of Gotham/Batman locations"""
        
        discovered_locations = []
        
        # Start with category discovery if requested
        if use_categories:
            self.logger.info("Discovering locations from categories...")
            discovered_locations = self.get_locations_from_categories()
        
        # Comprehensive manual locations list
        manual_locations = [
            # Core Batman Locations
            "Batcave", "Wayne_Manor", "Wayne_Enterprises", "Wayne_Tower", "Wayne_Foundation",
            "Ace_Chemicals", "Arkham_Asylum", "Blackgate_Penitentiary", "Blackgate_Prison",
            
            # GCPD & Government
            "GCPD_Headquarters", "Gotham_City_Police_Department", "City_Hall", "Gotham_City_Hall",
            "Mayor's_Office", "District_Attorney's_Office", "Gotham_Courthouse", "Gotham_General_Hospital",
            
            # Gotham Districts/Neighborhoods
            "Crime_Alley", "Park_Row", "The_Narrows", "East_End", "Old_Gotham", "New_Gotham",
            "Downtown_Gotham", "Midtown_Gotham", "Uptown_Gotham", "Financial_District",
            "Gotham_University_District", "Bristol_County", "Robinson_Park", "Amusement_Mile",
            
            # Landmarks & Infrastructure
            "Gotham_Bridge", "ACE_Chemical_Building", "Gotham_Cathedral", "Gotham_Opera_House",
            "Gotham_Museum", "Gotham_Natural_History_Museum", "Clock_Tower", "Gotham_Clock_Tower",
            "Gotham_Harbor", "Gotham_Port", "Gotham_Docks", "Gotham_Airport", "Gotham_Subway",
            
            # Villain Lairs & Hideouts
            "Iceberg_Lounge", "Ace_Chemical_Plant", "Joker's_Funhouse", "Penguin's_Lair",
            "Riddler's_Hideout", "Two-Face_Hideout", "Mad_Hatter's_Lair", "Scarecrow's_Lab",
            "Mr._Freeze_Laboratory", "Poison_Ivy's_Greenhouse", "Bane's_Hideout",
            
            # Underground/Hidden Locations
            "Gotham_Underground", "Gotham_Sewers", "Gotham_Catacombs", "Wonder_Tower",
            "League_of_Assassins_Headquarters", "Court_of_Owls_Nest", "Talon_Training_Facility",
            
            # Entertainment & Business
            "Gotham_Casino", "Flamingo_Club", "Stacked_Deck", "My_Alibi", "Gotham_Mall",
            "Gotham_Stock_Exchange", "Gotham_First_National_Bank", "Gotham_Mercy_Hospital",
            
            # Media Specific Locations
            "Titans_Tower_(Gotham)", "Birds_of_Prey_Headquarters", "Oracle's_Clocktower",
            "GCPD_Rooftop", "Gotham_Gazette", "Vicki_Vale_Apartment", "Selina_Kyle_Apartment",
            
            # Surrounding Areas
            "Gotham_Bay", "Gotham_River", "Gotham_Woods", "Gotham_Cemetery", "Gotham_Pier",
            "Gotham_Shipyard", "Gotham_Industrial_District", "Gotham_Rail_Yard",
            
            # Historical/Destroyed Locations
            "Original_Wayne_Manor", "Old_Gotham_Cathedral", "Earthquake_Damaged_Areas",
            "No_Man's_Land_Territories", "Cataclysm_Ruins"
        ]
        
        # Merge discovered and manual locations
        all_locations = discovered_locations.copy()
        for location in manual_locations:
            if location not in all_locations:
                all_locations.append(location)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_locations = []
        for location in all_locations:
            if location not in seen:
                seen.add(location)
                unique_locations.append(location)
        
        self.logger.info(f"Found {len(unique_locations)} Gotham locations to scrape")
        self.logger.info(f"Category discovered: {len(discovered_locations)}, Manual backup: {len(manual_locations)}")
        return unique_locations
    
    def get_locations_from_categories(self) -> List[str]:
        """Get locations from Batman Wiki categories"""
        location_names = []
        
        # Batman location category pages
        category_urls = [
            "https://batman.fandom.com/wiki/Category:Locations",
            "https://batman.fandom.com/wiki/Category:Gotham_City_Locations",
            "https://batman.fandom.com/wiki/Category:Buildings",
            "https://batman.fandom.com/wiki/Category:Districts",
            "https://batman.fandom.com/wiki/Category:Neighborhoods"
        ]
        
        for url in category_urls:
            self.logger.info(f"Getting location list from: {url}")
            response = self.safe_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find location links in category
                category_content = soup.find('div', class_='category-page__members')
                if not category_content:
                    category_content = soup.find('div', class_='mw-category')
                
                if category_content:
                    location_links = category_content.find_all('a', href=True)
                    for link in location_links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        # Filter for actual location pages
                        if ('/wiki/' in href and 
                            ':' not in href and 
                            'Category:' not in href and
                            'Template:' not in href and
                            'File:' not in href and
                            title and len(title) > 1):
                            location_name = href.replace('/wiki/', '')
                            if location_name and location_name not in location_names:
                                location_names.append(location_name)
        
        return location_names
    
    def scrape_batman_locations_comprehensive(self, limit: int = None) -> List[Dict]:
        """Scrape comprehensive Batman locations database - runs until complete"""
        
        location_names = self.get_gotham_locations_list(use_categories=True)
        locations_data = []
        
        # If no limit specified, scrape ALL discovered locations
        if limit is None:
            total_locations = len(location_names)
            self.logger.info(f"Starting COMPLETE scrape of ALL {total_locations} Batman locations...")
        else:
            total_locations = min(limit, len(location_names))
            self.logger.info(f"Starting to scrape {total_locations} Batman locations...")
        
        locations_to_scrape = location_names if limit is None else location_names[:limit]
        successful_scrapes = 0
        failed_scrapes = 0
        
        for i, location in enumerate(locations_to_scrape):
            self.logger.info(f"Scraping location {i+1}/{total_locations}: {location}")
            data = self.scrape_batman_location(location)
            
            if data:
                locations_data.append(data)
                successful_scrapes += 1
                self.logger.info(f"✅ Successfully scraped {location}")
            else:
                failed_scrapes += 1
                self.logger.warning(f"❌ Failed to scrape {location}")
            
            # Save periodically (every 10 locations)
            if (i + 1) % 10 == 0:
                self.save_to_json(locations_data, f'batman_locations_partial_{i+1}.json')
                self.logger.info(f"💾 Saved partial location data: {successful_scrapes} locations")
                self.logger.info(f"📊 Progress: {successful_scrapes} success, {failed_scrapes} failed")
            
            # Politeness break every 25 locations
            if (i + 1) % 25 == 0:
                self.logger.info("😴 Taking a 2-minute politeness break...")
                time.sleep(120)
        
        # Final summary
        self.logger.info(f"🏁 SCRAPING COMPLETE!")
        self.logger.info(f"📊 Final Results: {successful_scrapes} successful, {failed_scrapes} failed")
        self.logger.info(f"📈 Success Rate: {(successful_scrapes/total_locations)*100:.1f}%")
        
        return locations_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'batman_locations.json'):
        """Save scraped location data to JSON file"""
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Location data saved to {filepath}")

if __name__ == "__main__":
    import sys
    
    print("Batman Locations Scraper")
    print("=" * 40)
    print("1. Quick test (3 locations, ~30 seconds)")
    print("2. COMPLETE scrape (ALL locations until none remain, 2-4 hours)")
    print("3. Custom amount")
    
    mode = input("\nChoose mode (1/2/3): ").strip()
    
    scraper = BatmanLocationsScraper(base_delay=2.0, max_delay=4.0)
    
    if mode == "1":
        print("\nStarting quick location test...")
        # Test with core locations
        test_locations = ["Batcave", "Wayne_Manor", "Arkham_Asylum"]
        locations_data = []
        for location in test_locations:
            data = scraper.scrape_batman_location(location)
            if data:
                locations_data.append(data)
        scraper.save_to_json(locations_data, 'test_batman_locations.json')
        filename = 'test_batman_locations.json'
        
    elif mode == "2":
        print("\nStarting COMPLETE locations scrape...")
        print("This will scrape ALL discovered locations until NONE remain!")
        print("Expected: 100-200+ locations, 2-4 hours runtime")
        print("Progress saved every 10 locations, breaks every 25")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        locations = scraper.scrape_batman_locations_comprehensive(limit=None)  # No limit = ALL locations
        scraper.save_to_json(locations, 'batman_locations_COMPLETE.json')
        filename = 'batman_locations_COMPLETE.json'
        
    elif mode == "3":
        try:
            limit = int(input("How many locations? "))
            locations = scraper.scrape_batman_locations_comprehensive(limit=limit)
            scraper.save_to_json(locations, f'batman_locations_{limit}.json')
            filename = f'batman_locations_{limit}.json'
        except ValueError:
            print("Invalid number")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if 'locations' in locals() or 'locations_data' in locals():
        data = locations if 'locations' in locals() else locations_data
        print(f"\n✅ Successfully scraped {len(data)} locations!")
        print(f"📁 Saved to: data/{filename}")
        print(f"📋 Log file: locations_scraper.log")
        
        if data:
            print(f"\nSample location: {data[0]['name']}")
            details = data[0].get('details', {})
            if details.get('notable_features'):
                print(f"Features: {', '.join(details['notable_features'][:3])}...")
    else:
        print("❌ No data collected. Check locations_scraper.log for issues.")