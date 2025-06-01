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

class BatmanVehicleScraper:
    def __init__(self, base_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize the vehicle scraper with safety features
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        
        # Respectful headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BatmanVehicleScraper/1.0; Educational Purpose)',
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
                logging.FileHandler('vehicle_scraper.log'),
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
    
    def extract_vehicle_specifications(self, soup: BeautifulSoup) -> Dict:
        """Extract detailed vehicle specifications from infobox and content"""
        specs = {
            'length': '',
            'width': '',
            'height': '',
            'weight': '',
            'max_speed': '',
            'engine': '',
            'armor': '',
            'crew_capacity': '',
            'weapons': [],
            'defensive_systems': [],
            'special_features': [],
            'manufacturer': '',
            'first_appearance': ''
        }
        
        # Extract from infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            # Look for common specification fields
            spec_fields = {
                'length': ['length', 'len'],
                'width': ['width', 'beam'],
                'height': ['height', 'height'],
                'weight': ['weight', 'mass', 'displacement'],
                'max_speed': ['speed', 'max speed', 'top speed', 'maximum speed'],
                'engine': ['engine', 'propulsion', 'power'],
                'armor': ['armor', 'armour', 'protection'],
                'crew_capacity': ['crew', 'capacity', 'occupancy'],
                'manufacturer': ['manufacturer', 'builder', 'made by'],
                'first_appearance': ['first appearance', 'debut']
            }
            
            for data_div in infobox.find_all('div', {'data-source': True}):
                data_source = data_div.get('data-source', '').lower()
                text_content = data_div.get_text(strip=True)
                
                # Match field names
                for spec_key, field_names in spec_fields.items():
                    if any(field in data_source for field in field_names):
                        specs[spec_key] = text_content
                        break
        
        # Extract weapons and features from content
        content = soup.find('div', class_='mw-parser-output')
        if content:
            text = content.get_text().lower()
            
            # Batman universe vehicle weapons (hero + villain)
            weapon_keywords = [
                # Batman weapons
                'machine gun', 'cannon', 'missile', 'rocket', 'torpedo', 'laser',
                'plasma cannon', 'rail gun', 'minigun', 'gatling gun', 'chain gun',
                'autocannon', 'howitzer', 'mortar', 'grenade launcher', 'flamethrower',
                'emp cannon', 'sonic cannon', 'freeze ray', 'taser', 'net launcher',
                'batarang launcher', 'caltrops', 'smoke dispenser', 'oil slick',
                
                # Villain-specific weapons
                'laughing gas dispenser', 'acid sprayer', 'poison gas', 'tear gas',
                'ice cannon', 'freeze gun', 'thermite cannon', 'explosive charges',
                'drill weapon', 'saw blade', 'harpoon gun', 'grappling hook gun',
                'electrified hull', 'ramming spikes', 'buzz saw', 'flame thrower',
                'umbrella launcher', 'umbrella gun', 'question mark launcher',
                'venom dispenser', 'fear toxin sprayer', 'mind control ray',
                'sonic weapon', 'hypnotic device', 'explosive pellets'
            ]
            
            # Defensive systems
            defensive_keywords = [
                'armor plating', 'bulletproof', 'missile defense', 'countermeasures',
                'stealth mode', 'cloaking device', 'electromagnetic shielding',
                'reactive armor', 'ablative armor', 'force field', 'deflector shield'
            ]
            
            # Special features
            feature_keywords = [
                'autopilot', 'gps', 'sonar', 'radar', 'thermal imaging', 'night vision',
                'ejection seat', 'vtol', 'submarine mode', 'flight capable', 'hover mode',
                'transformer', 'modular', 'self-repair', 'ai system', 'voice control',
                'remote control', 'stealth coating', 'emp hardening', 'self-destruct'
            ]
            
            # Find weapons
            for weapon in weapon_keywords:
                if weapon in text and weapon not in specs['weapons']:
                    specs['weapons'].append(weapon)
            
            # Find defensive systems  
            for defense in defensive_keywords:
                if defense in text and defense not in specs['defensive_systems']:
                    specs['defensive_systems'].append(defense)
            
            # Find special features
            for feature in feature_keywords:
                if feature in text and feature not in specs['special_features']:
                    specs['special_features'].append(feature)
        
        return specs
    
    def scrape_batman_vehicle(self, vehicle_name: str) -> Optional[Dict]:
        """Scrape a Batman vehicle page with detailed specifications"""
        base_url = "https://batman.fandom.com"
        url = f"{base_url}/wiki/{vehicle_name.replace(' ', '_')}"
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        vehicle_data = {
            'name': vehicle_name,
            'url': url,
            'type': '',
            'description': '',
            'specifications': {},
            'aliases': [],
            'users': [],
            'appearances': []
        }
        
        try:
            # Get vehicle type from categories or infobox
            categories = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
            for cat in categories:
                cat_text = cat.get_text().lower()
                if any(vtype in cat_text for vtype in ['vehicle', 'aircraft', 'ship', 'submarine', 'car', 'boat', 'plane']):
                    vehicle_data['type'] = cat.get_text()
                    break
            
            # Get aliases from infobox
            infobox = soup.find('aside', class_='portable-infobox')
            if infobox:
                alias_section = infobox.find('div', {'data-source': 'alias'})
                if alias_section:
                    aliases = alias_section.get_text(strip=True).split(',')
                    vehicle_data['aliases'] = [alias.strip() for alias in aliases]
            
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
                        any(word in text.lower() for word in ['vehicle', 'car', 'aircraft', 'ship', 'boat', 'batmobile', 'batwing', 'batboat'])):
                        clean_text = re.sub(r'\s+', ' ', text.strip())
                        vehicle_data['description'] = clean_text[:600] + '...' if len(clean_text) > 600 else clean_text
                        break
            
            # Extract detailed specifications
            vehicle_data['specifications'] = self.extract_vehicle_specifications(soup)
            
            self.logger.info(f"Successfully scraped vehicle data for {vehicle_name}")
            return vehicle_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {vehicle_name}: {e}")
            return None
    
    def get_vehicles_from_categories(self) -> List[str]:
        """Get vehicles from Batman Wiki categories"""
        vehicle_names = []
        
        # Batman universe vehicle category pages (verified URLs) - includes all vehicles
        category_urls = [
            "https://batman.fandom.com/wiki/Category:Vehicles",
            "https://batman.fandom.com/wiki/Category:Batmobiles",
            "https://batman.fandom.com/wiki/Category:Batplanes", 
            "https://batman.fandom.com/wiki/Category:Aircrafts",
            "https://batman.fandom.com/wiki/Category:Watercrafts",
            "https://batman.fandom.com/wiki/Category:Animated_Batmobiles",
            "https://batman.fandom.com/wiki/Category:Live-Action_Batmobiles",
            "https://batman.fandom.com/wiki/Category:Video_Game_Batmobiles"
        ]
        
        for url in category_urls:
            self.logger.info(f"Getting vehicle list from: {url}")
            response = self.safe_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find vehicle links in category
                category_content = soup.find('div', class_='category-page__members')
                if not category_content:
                    category_content = soup.find('div', class_='mw-category')
                
                if category_content:
                    vehicle_links = category_content.find_all('a', href=True)
                    for link in vehicle_links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        # Filter for actual vehicle pages
                        if ('/wiki/' in href and 
                            ':' not in href and 
                            'Category:' not in href and
                            'Template:' not in href and
                            'File:' not in href and
                            title and len(title) > 1):
                            vehicle_name = href.replace('/wiki/', '')
                            if vehicle_name and vehicle_name not in vehicle_names:
                                vehicle_names.append(vehicle_name)
        
        return vehicle_names
    
    def get_batman_vehicles_list(self, use_categories: bool = True) -> List[str]:
        """Get comprehensive list of Batman vehicles"""
        
        # Start with category discovery if requested
        if use_categories:
            self.logger.info("Discovering vehicles from categories...")
            discovered_vehicles = self.get_vehicles_from_categories()
        else:
            discovered_vehicles = []
        
        # Comprehensive manual backup list
        manual_vehicles = [
            # Primary Vehicles
            "Batmobile", "Batwing", "Batboat", "Batcycle", "Bat-Sub", "Batcopter",
            "Batplane", "Redbird", "Robin's_Redbird", "Nightwing's_Motorcycle",
            
            # Batmobile Variants
            "Batmobile_(1989)", "Batmobile_(Returns)", "Batmobile_(Forever)", 
            "Batmobile_(Batman_&_Robin)", "Batmobile_(Begins)", "Batmobile_(Dark_Knight)",
            "Batmobile_(Arkham)", "Batmobile_(Animated_Series)", "Batmobile_(The_Batman)",
            "Batmobile_(Brave_and_Bold)", "Batmobile_(66_TV)", "Tumbler", "Bat-Tank",
            
            # Aircraft
            "Batwing_(Burton)", "Batwing_(Animated)", "Batwing_(Arkham)", "Bat-Gyro",
            "Flying_Batcave", "Bat-Glider", "Whirly-Bat", "Bat-Rocket", "Batjet",
            
            # Watercraft  
            "Batboat_(Classic)", "Batboat_(Animated)", "Bat-Sub_(Classic)", "Bat-Submarine",
            "Hydrofoil_Batboat", "Batskiboat", "Bat-Submersible",
            
            # Motorcycles & Bikes
            "Batcycle_(Classic)", "Batcycle_(Dark_Knight)", "Batpod", "Robin's_Cycle",
            "Nightwing's_Bike", "Batgirl's_Cycle", "Red_Robin's_Cycle",
            
            # Specialized Vehicles
            "Bat-Train", "Bat-Truck", "Batmobile_Snowplow", "Arctic_Batmobile",
            "Space_Batmobile", "Underwater_Batmobile", "Flying_Batmobile", "Bat-Mech",
            
            # Support Vehicles
            "Mobile_Crime_Lab", "Bat-Ambulance", "Bat-Fire_Truck", "Bat-Tow_Truck",
            "Batcave_Vehicles", "Utility_Batmobile", "Racing_Batmobile",
            
            # Villain Vehicles - EXPANDED
            "Jokermobile", "Penguin_Submarine", "Two-Face_Armored_Car", "Riddler_Car",
            "Joker_Helicopter", "Penguin_Duck_Boat", "Mr._Freeze_Ice_Truck",
            "Scarecrow_Helicopter", "Bane_Truck", "Harley_Quinn_Bike", "Poison_Ivy_Car",
            "Ra's_al_Ghul_Train", "League_of_Assassins_Vehicles", "Deathstroke_Bike",
            "Black_Mask_Limo", "Killer_Croc_Boat", "Mad_Hatter_Van", "Clayface_Vehicle",
            "Firefly_Jetpack", "Calendar_Man_Car", "Victor_Zsasz_Van", "Hugo_Strange_Car",
            "Penguin_Iceberg_Lounge_Boat", "Joker_Steamroller", "Joker_Parade_Float",
            "Two-Face_Truck", "Riddler_Question_Mark_Car", "Catwoman_Motorcycle",
            "Talia_al_Ghul_Helicopter", "Falcone_Crime_Family_Cars", "Maroni_Vehicles",
            "Court_of_Owls_Vehicles", "Talon_Aircraft", "Professor_Pyg_Ambulance",
            "Anarky_Motorcycle", "Hush_Vehicle", "Deadshot_Aircraft", "KGBeast_Tank",
            
            # Other Universe Vehicles
            "Batman_Beyond_Batmobile", "Future_Batwing", "Terry's_Cycle",
            "Justice_League_Batmobile", "Brave_Bold_Batmobile", "LEGO_Batmobile"
        ]
        
        # Merge discovered and manual vehicles
        all_vehicles = discovered_vehicles.copy()
        for vehicle in manual_vehicles:
            if vehicle not in all_vehicles:
                all_vehicles.append(vehicle)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_vehicles = []
        for vehicle in all_vehicles:
            if vehicle not in seen:
                seen.add(vehicle)
                unique_vehicles.append(vehicle)
        
        self.logger.info(f"Found {len(unique_vehicles)} Batman vehicles to scrape")
        self.logger.info(f"Category discovered: {len(discovered_vehicles)}, Manual backup: {len(manual_vehicles)}")
        return unique_vehicles
    
    def scrape_batman_vehicles_comprehensive(self, limit: int = None) -> List[Dict]:
        """Scrape comprehensive Batman vehicle database - runs until complete"""
        
        vehicle_names = self.get_batman_vehicles_list(use_categories=True)
        vehicles_data = []
        
        # If no limit specified, scrape ALL discovered vehicles
        if limit is None:
            total_vehicles = len(vehicle_names)
            self.logger.info(f"Starting COMPLETE scrape of ALL {total_vehicles} Batman vehicles...")
        else:
            total_vehicles = min(limit, len(vehicle_names))
            self.logger.info(f"Starting to scrape {total_vehicles} Batman vehicles...")
        
        vehicles_to_scrape = vehicle_names if limit is None else vehicle_names[:limit]
        successful_scrapes = 0
        failed_scrapes = 0
        
        for i, vehicle in enumerate(vehicles_to_scrape):
            self.logger.info(f"Scraping vehicle {i+1}/{total_vehicles}: {vehicle}")
            data = self.scrape_batman_vehicle(vehicle)
            
            if data:
                vehicles_data.append(data)
                successful_scrapes += 1
                self.logger.info(f"✅ Successfully scraped {vehicle}")
            else:
                failed_scrapes += 1
                self.logger.warning(f"❌ Failed to scrape {vehicle}")
            
            # Save periodically (every 10 vehicles)
            if (i + 1) % 10 == 0:
                self.save_to_json(vehicles_data, f'batman_vehicles_partial_{i+1}.json')
                self.logger.info(f"💾 Saved partial vehicle data: {successful_scrapes} vehicles")
                self.logger.info(f"📊 Progress: {successful_scrapes} success, {failed_scrapes} failed")
            
            # Politeness break every 25 vehicles
            if (i + 1) % 25 == 0:
                self.logger.info("😴 Taking a 2-minute politeness break...")
                time.sleep(120)
            
            # Long break every 50 vehicles for extra politeness
            elif (i + 1) % 50 == 0:
                self.logger.info("😴 Taking a 5-minute extended break...")
                time.sleep(300)
        
        # Final summary
        self.logger.info(f"🏁 SCRAPING COMPLETE!")
        self.logger.info(f"📊 Final Results: {successful_scrapes} successful, {failed_scrapes} failed")
        self.logger.info(f"📈 Success Rate: {(successful_scrapes/total_vehicles)*100:.1f}%")
        
        return vehicles_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'batman_vehicles.json'):
        """Save scraped vehicle data to JSON file"""
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Vehicle data saved to {filepath}")

if __name__ == "__main__":
    import sys
    
    print("Batman Vehicle Scraper")
    print("=" * 40)
    print("1. Quick test (3 vehicles, ~30 seconds)")
    print("2. COMPLETE scrape (ALL vehicles until none remain, 3-6 hours)")
    print("3. Custom amount")
    
    mode = input("\nChoose mode (1/2/3): ").strip()
    
    scraper = BatmanVehicleScraper(base_delay=2.0, max_delay=4.0)
    
    if mode == "1":
        print("\nStarting quick vehicle test...")
        # Test with mix of hero and villain vehicles
        test_vehicles = ["Batmobile", "Jokermobile", "Penguin_Submarine"]
        vehicles_data = []
        for vehicle in test_vehicles:
            data = scraper.scrape_batman_vehicle(vehicle)
            if data:
                vehicles_data.append(data)
        scraper.save_to_json(vehicles_data, 'test_batman_vehicles.json')
        filename = 'test_batman_vehicles.json'
        
    elif mode == "2":
        print("\nStarting COMPLETE vehicle scrape...")
        print("This will scrape ALL discovered vehicles until NONE remain!")
        print("Expected: 80-150+ vehicles, 3-6 hours runtime")
        print("Progress saved every 10 vehicles, breaks every 25")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        vehicles = scraper.scrape_batman_vehicles_comprehensive(limit=None)  # No limit = ALL vehicles
        scraper.save_to_json(vehicles, 'batman_vehicles_COMPLETE.json')
        filename = 'batman_vehicles_COMPLETE.json'
        
    elif mode == "3":
        try:
            limit = int(input("How many vehicles? "))
            vehicles = scraper.scrape_batman_vehicles_comprehensive(limit=limit)
            scraper.save_to_json(vehicles, f'batman_vehicles_{limit}.json')
            filename = f'batman_vehicles_{limit}.json'
        except ValueError:
            print("Invalid number")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if 'vehicles' in locals() or 'vehicles_data' in locals():
        data = vehicles if 'vehicles' in locals() else vehicles_data
        print(f"\n✅ Successfully scraped {len(data)} vehicles!")
        print(f"📁 Saved to: data/{filename}")
        print(f"📋 Log file: vehicle_scraper.log")
        
        if data:
            print(f"\nSample vehicle: {data[0]['name']}")
            specs = data[0].get('specifications', {})
            if specs.get('weapons'):
                print(f"Weapons: {', '.join(specs['weapons'][:3])}...")
    else:
        print("❌ No data collected. Check vehicle_scraper.log for issues.")