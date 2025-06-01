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

class BatmanOrganizationsScraper:
    def __init__(self, base_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize the organizations scraper with safety features
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        
        # Respectful headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BatmanOrganizationsScraper/1.0; Educational Purpose)',
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
                logging.FileHandler('organizations_scraper.log'),
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
    
    def extract_organization_details(self, soup: BeautifulSoup) -> Dict:
        """Extract detailed organization information from infobox and content"""
        details = {
            'organization_type': '',  # hero team, villain group, crime family, government, corporation
            'alignment': '',  # good, evil, neutral
            'founded': '',
            'leader': '',
            'headquarters': '',
            'members': [],
            'enemies': [],
            'allies': [],
            'activities': [],
            'resources': [],
            'status': 'active'  # active, disbanded, reformed
        }
        
        # Extract from infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            # Common organization fields
            org_fields = {
                'organization_type': ['type', 'organization type', 'classification'],
                'alignment': ['alignment', 'allegiance', 'side'],
                'founded': ['founded', 'established', 'formed', 'created'],
                'leader': ['leader', 'head', 'commander', 'boss', 'chairman'],
                'headquarters': ['headquarters', 'base', 'location', 'hq'],
                'status': ['status', 'state', 'condition']
            }
            
            for data_div in infobox.find_all('div', {'data-source': True}):
                data_source = data_div.get('data-source', '').lower()
                text_content = data_div.get_text(strip=True)
                
                for detail_key, field_names in org_fields.items():
                    if any(field in data_source for field in field_names):
                        details[detail_key] = text_content
                        break
        
        # Extract members, activities, and relationships from content
        content = soup.find('div', class_='mw-parser-output')
        if content:
            text = content.get_text().lower()
            
            # Organization members (focus on major Batman universe characters)
            batman_characters = [
                'batman', 'bruce wayne', 'robin', 'dick grayson', 'tim drake',
                'jason todd', 'damian wayne', 'batgirl', 'barbara gordon', 'nightwing',
                'alfred pennyworth', 'commissioner gordon', 'catwoman', 'huntress',
                'oracle', 'spoiler', 'red hood', 'red robin', 'batwoman'
            ]
            
            villain_characters = [
                'joker', 'two-face', 'penguin', 'riddler', 'bane', 'scarecrow',
                'ra\'s al ghul', 'talia al ghul', 'harley quinn', 'poison ivy',
                'mr. freeze', 'clayface', 'killer croc', 'black mask'
            ]
            
            # Activities/Operations
            activity_keywords = [
                'crime fighting', 'law enforcement', 'vigilante', 'protection',
                'organized crime', 'smuggling', 'extortion', 'assassination',
                'research', 'corporate espionage', 'government operations',
                'training', 'recruitment', 'intelligence gathering'
            ]
            
            # Resources/Assets
            resource_keywords = [
                'advanced technology', 'weapons cache', 'financial resources',
                'international network', 'government backing', 'corporate funding',
                'criminal network', 'underground connections', 'training facilities',
                'surveillance network', 'transportation', 'safe houses'
            ]
            
            # Find members (limit to key characters)
            all_characters = batman_characters + villain_characters
            for character in all_characters:
                if character in text and character not in details['members']:
                    details['members'].append(character)
                    if len(details['members']) >= 8:  # Limit to 8 key members
                        break
            
            # Find activities
            for activity in activity_keywords:
                if activity in text and activity not in details['activities']:
                    details['activities'].append(activity)
                    if len(details['activities']) >= 5:  # Limit to 5 activities
                        break
            
            # Find resources
            for resource in resource_keywords:
                if resource in text and resource not in details['resources']:
                    details['resources'].append(resource)
                    if len(details['resources']) >= 5:  # Limit to 5 resources
                        break
            
            # Auto-detect organization type if not found
            if not details['organization_type']:
                if any(hero in text for hero in ['justice', 'hero', 'protect', 'defend']):
                    if any(team in text for team in ['team', 'league', 'group']):
                        details['organization_type'] = 'hero team'
                elif any(villain in text for villain in ['crime', 'criminal', 'villain', 'evil']):
                    if any(org in text for org in ['family', 'syndicate', 'gang']):
                        details['organization_type'] = 'crime organization'
                    else:
                        details['organization_type'] = 'villain group'
                elif any(corp in text for corp in ['corporation', 'company', 'enterprise']):
                    details['organization_type'] = 'corporation'
                elif any(gov in text for gov in ['government', 'agency', 'department']):
                    details['organization_type'] = 'government agency'
            
            # Auto-detect alignment if not found
            if not details['alignment']:
                hero_indicators = ['protect', 'defend', 'justice', 'help', 'save']
                villain_indicators = ['crime', 'criminal', 'destroy', 'kill', 'steal']
                
                hero_score = sum(1 for word in hero_indicators if word in text)
                villain_score = sum(1 for word in villain_indicators if word in text)
                
                if hero_score > villain_score + 1:
                    details['alignment'] = 'good'
                elif villain_score > hero_score + 1:
                    details['alignment'] = 'evil'
                else:
                    details['alignment'] = 'neutral'
        
        return details
    
    def scrape_batman_organization(self, org_name: str) -> Optional[Dict]:
        """Scrape a Batman organization page with detailed information"""
        base_url = "https://batman.fandom.com"
        url = f"{base_url}/wiki/{org_name.replace(' ', '_')}"
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        org_data = {
            'name': org_name,
            'url': url,
            'category': '',
            'description': '',
            'details': {},
            'aliases': [],
            'notable_operations': [],
            'first_appearance': ''
        }
        
        try:
            # Get organization category
            categories = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
            for cat in categories:
                cat_text = cat.get_text().lower()
                if any(org_type in cat_text for org_type in ['organization', 'team', 'group', 'agency', 'family', 'corporation']):
                    org_data['category'] = cat.get_text()
                    break
            
            # Get aliases from infobox
            infobox = soup.find('aside', class_='portable-infobox')
            if infobox:
                alias_section = infobox.find('div', {'data-source': 'alias'})
                if alias_section:
                    aliases = alias_section.get_text(strip=True).split(',')
                    org_data['aliases'] = [alias.strip() for alias in aliases]
            
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
                        any(word in text.lower() for word in ['organization', 'team', 'group', 'agency', 'family', 'league', 'corporation'])):
                        clean_text = re.sub(r'\s+', ' ', text.strip())
                        org_data['description'] = clean_text[:600] + '...' if len(clean_text) > 600 else clean_text
                        break
            
            # Extract detailed organization information
            org_data['details'] = self.extract_organization_details(soup)
            
            self.logger.info(f"Successfully scraped organization data for {org_name}")
            return org_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {org_name}: {e}")
            return None
    
    def get_batman_organizations_list(self, use_categories: bool = True) -> List[str]:
        """Get comprehensive list of Batman universe organizations"""
        
        discovered_organizations = []
        
        # Start with category discovery if requested
        if use_categories:
            self.logger.info("Discovering organizations from categories...")
            discovered_organizations = self.get_organizations_from_categories()
        
        # Comprehensive manual organizations list
        manual_organizations = [
            # Hero Teams & Organizations
            "Justice_League", "Justice_League_of_America", "Batman_Family", "Bat-Family",
            "Outsiders", "Birds_of_Prey", "Teen_Titans", "Titans", "Justice_Society",
            "Batman_Incorporated", "Batman_Inc", "Wayne_Enterprises", "Wayne_Foundation",
            
            # Government & Law Enforcement
            "GCPD", "Gotham_City_Police_Department", "FBI", "CIA", "DEO", "ARGUS",
            "Checkmate", "Task_Force_X", "Suicide_Squad", "SHIELD", "Department_of_Extranormal_Operations",
            
            # Villain Organizations
            "League_of_Assassins", "League_of_Shadows", "Court_of_Owls", "Injustice_League",
            "Legion_of_Doom", "Secret_Society_of_Super_Villains", "Kobra", "HIVE",
            "H.I.V.E.", "Black_Glove", "The_Religion_of_Crime", "Intergang",
            
            # Crime Families & Syndicates
            "Falcone_Crime_Family", "Maroni_Crime_Family", "Penguin_Organization",
            "Red_Hood_Gang", "Joker_Gang", "Two-Face_Gang", "Riddler_Organization",
            "Black_Mask_Organization", "Ventriloquist_Gang", "Mad_Hatter_Gang",
            
            # Corporations & Businesses
            "Wayne_Enterprises", "LexCorp", "Queen_Industries", "Kord_Industries",
            "Stagg_Enterprises", "Ace_Chemicals", "Ferris_Aircraft", "S.T.A.R._Labs",
            
            # Research & Scientific Organizations
            "S.T.A.R._Labs", "LexCorp_Research", "Wayne_Tech", "Palmer_Technologies",
            "Cadmus_Project", "Project_Cadmus", "Belle_Reve", "Blackgate_Prison",
            
            # International Organizations
            "Interpol", "United_Nations", "NATO", "European_Union", "Russian_Bratva",
            "Yakuza", "Triads", "Mafia", "Cosa_Nostra",
            
            # Arkham & Medical
            "Arkham_Asylum", "Arkham_Asylum_Staff", "Blackgate_Prison", "Iron_Heights",
            "Gotham_General_Hospital", "Gotham_University", "Hudson_University",
            
            # Media & Information
            "Gotham_Gazette", "Daily_Planet", "WGBS", "Galaxy_Communications",
            "Channel_52", "Vicki_Vale_Show", "Gotham_Tonight",
            
            # Specialized Teams
            "Batman_and_Robin", "Dynamic_Duo", "Gotham_Knights", "Shadow_Cabinet",
            "Seven_Soldiers", "Global_Guardians", "Omega_Men", "R.E.B.E.L.S.",
            
            # Mystical/Supernatural Organizations
            "Shadowpact", "Justice_League_Dark", "Trenchcoat_Brigade", "Sentinels_of_Magic",
            "Books_of_Magic", "Constantine_Network", "Zatanna_Associates"
        ]
        
        # Merge discovered and manual organizations
        all_organizations = discovered_organizations.copy()
        for org in manual_organizations:
            if org not in all_organizations:
                all_organizations.append(org)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_organizations = []
        for org in all_organizations:
            if org not in seen:
                seen.add(org)
                unique_organizations.append(org)
        
        self.logger.info(f"Found {len(unique_organizations)} Batman organizations to scrape")
        self.logger.info(f"Category discovered: {len(discovered_organizations)}, Manual backup: {len(manual_organizations)}")
        return unique_organizations
    
    def get_organizations_from_categories(self) -> List[str]:
        """Get organizations from Batman Wiki categories"""
        org_names = []
        
        # Batman organization category pages
        category_urls = [
            "https://batman.fandom.com/wiki/Category:Organizations",
            "https://batman.fandom.com/wiki/Category:Teams",
            "https://batman.fandom.com/wiki/Category:Groups",
            "https://batman.fandom.com/wiki/Category:Agencies",
            "https://batman.fandom.com/wiki/Category:Crime_Families"
        ]
        
        for url in category_urls:
            self.logger.info(f"Getting organization list from: {url}")
            response = self.safe_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find organization links in category
                category_content = soup.find('div', class_='category-page__members')
                if not category_content:
                    category_content = soup.find('div', class_='mw-category')
                
                if category_content:
                    org_links = category_content.find_all('a', href=True)
                    for link in org_links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        # Filter for actual organization pages
                        if ('/wiki/' in href and 
                            ':' not in href and 
                            'Category:' not in href and
                            'Template:' not in href and
                            'File:' not in href and
                            title and len(title) > 1):
                            org_name = href.replace('/wiki/', '')
                            if org_name and org_name not in org_names:
                                org_names.append(org_name)
        
        return org_names
    
    def scrape_batman_organizations_comprehensive(self, limit: int = None) -> List[Dict]:
        """Scrape comprehensive Batman organizations database - runs until complete"""
        
        org_names = self.get_batman_organizations_list(use_categories=True)
        organizations_data = []
        
        # If no limit specified, scrape ALL discovered organizations
        if limit is None:
            total_orgs = len(org_names)
            self.logger.info(f"Starting COMPLETE scrape of ALL {total_orgs} Batman organizations...")
        else:
            total_orgs = min(limit, len(org_names))
            self.logger.info(f"Starting to scrape {total_orgs} Batman organizations...")
        
        orgs_to_scrape = org_names if limit is None else org_names[:limit]
        successful_scrapes = 0
        failed_scrapes = 0
        
        for i, org in enumerate(orgs_to_scrape):
            self.logger.info(f"Scraping organization {i+1}/{total_orgs}: {org}")
            data = self.scrape_batman_organization(org)
            
            if data:
                organizations_data.append(data)
                successful_scrapes += 1
                self.logger.info(f"✅ Successfully scraped {org}")
            else:
                failed_scrapes += 1
                self.logger.warning(f"❌ Failed to scrape {org}")
            
            # Save periodically (every 10 organizations)
            if (i + 1) % 10 == 0:
                self.save_to_json(organizations_data, f'batman_organizations_partial_{i+1}.json')
                self.logger.info(f"💾 Saved partial organization data: {successful_scrapes} organizations")
                self.logger.info(f"📊 Progress: {successful_scrapes} success, {failed_scrapes} failed")
            
            # Politeness break every 25 organizations
            if (i + 1) % 25 == 0:
                self.logger.info("😴 Taking a 2-minute politeness break...")
                time.sleep(120)
        
        # Final summary
        self.logger.info(f"🏁 ORGANIZATIONS SCRAPING COMPLETE!")
        self.logger.info(f"📊 Final Results: {successful_scrapes} successful, {failed_scrapes} failed")
        self.logger.info(f"📈 Success Rate: {(successful_scrapes/total_orgs)*100:.1f}%")
        
        return organizations_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'batman_organizations.json'):
        """Save scraped organization data to JSON file"""
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Organization data saved to {filepath}")

if __name__ == "__main__":
    import sys
    
    print("Batman Organizations Scraper")
    print("=" * 40)
    print("1. Quick test (3 organizations, ~30 seconds)")
    print("2. COMPLETE scrape (ALL organizations until none remain, 2-3 hours)")
    print("3. Custom amount")
    
    mode = input("\nChoose mode (1/2/3): ").strip()
    
    scraper = BatmanOrganizationsScraper(base_delay=2.0, max_delay=4.0)
    
    if mode == "1":
        print("\nStarting quick organization test...")
        # Test with diverse organization types
        test_organizations = ["Justice_League", "League_of_Assassins", "GCPD"]
        organizations_data = []
        for org in test_organizations:
            data = scraper.scrape_batman_organization(org)
            if data:
                organizations_data.append(data)
        scraper.save_to_json(organizations_data, 'test_batman_organizations.json')
        filename = 'test_batman_organizations.json'
        
    elif mode == "2":
        print("\nStarting COMPLETE organizations scrape...")
        print("This will scrape ALL discovered organizations until NONE remain!")
        print("Expected: 80-120+ organizations, 2-3 hours runtime")
        print("Progress saved every 10 organizations, breaks every 25")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        organizations = scraper.scrape_batman_organizations_comprehensive(limit=None)  # No limit = ALL organizations
        scraper.save_to_json(organizations, 'batman_organizations_COMPLETE.json')
        filename = 'batman_organizations_COMPLETE.json'
        
    elif mode == "3":
        try:
            limit = int(input("How many organizations? "))
            organizations = scraper.scrape_batman_organizations_comprehensive(limit=limit)
            scraper.save_to_json(organizations, f'batman_organizations_{limit}.json')
            filename = f'batman_organizations_{limit}.json'
        except ValueError:
            print("Invalid number")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if 'organizations' in locals() or 'organizations_data' in locals():
        data = organizations if 'organizations' in locals() else organizations_data
        print(f"\n✅ Successfully scraped {len(data)} organizations!")
        print(f"📁 Saved to: data/{filename}")
        print(f"📋 Log file: organizations_scraper.log")
        
        if data:
            print(f"\nSample organization: {data[0]['name']}")
            details = data[0].get('details', {})
            if details.get('organization_type'):
                print(f"Type: {details['organization_type']}")
            if details.get('alignment'):
                print(f"Alignment: {details['alignment']}")
    else:
        print("❌ No data collected. Check organizations_scraper.log for issues.")