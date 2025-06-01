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

class SafeBatmanScraper:
    def __init__(self, base_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize the scraper with safety features
        
        Args:
            base_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        
        # Respectful headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BatmanChatbotScraper/1.0; Educational Purpose)',
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
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track requests for politeness
        self.request_count = 0
        self.last_request_time = 0
        
    def check_robots_txt(self, base_url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            rp.read()
            return rp.can_fetch(self.session.headers['User-Agent'], base_url)
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt: {e}")
            return True  # Assume allowed if can't check
    
    def respectful_delay(self):
        """Add random delay between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay
        delay = random.uniform(self.base_delay, self.max_delay)
        
        # If we're going too fast, add extra delay
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
                
                # Check for rate limiting
                if response.status_code == 429:
                    wait_time = 60 * (attempt + 1)  # Exponential backoff
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
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def scrape_batman_character(self, character_name: str) -> Optional[Dict]:
        """Scrape a Batman character page from the wiki"""
        base_url = "https://batman.fandom.com"
        url = f"{base_url}/wiki/{character_name.replace(' ', '_')}"
        
        # Check robots.txt first
        if not self.check_robots_txt(base_url):
            self.logger.error("Scraping not allowed by robots.txt")
            return None
        
        response = self.safe_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        character_data = {
            'name': character_name,
            'url': url,
            'aliases': [],
            'first_appearance': '',
            'description': '',
            'relationships': [],
            'powers_abilities': []
        }
        
        try:
            # Extract basic info from infobox
            infobox = soup.find('aside', class_='portable-infobox')
            if infobox:
                # Get aliases
                alias_section = infobox.find('div', {'data-source': 'alias'})
                if alias_section:
                    aliases = alias_section.get_text(strip=True).split(',')
                    character_data['aliases'] = [alias.strip() for alias in aliases]
                
                # Get first appearance
                first_app = infobox.find('div', {'data-source': 'first'})
                if first_app:
                    character_data['first_appearance'] = first_app.get_text(strip=True)
            
            # Get description from article content (skip infobox)
            content = soup.find('div', class_='mw-parser-output')
            if content:
                # Remove infobox and other unwanted elements
                for unwanted in content.find_all(['aside', 'table', 'div'], class_=['portable-infobox', 'infobox', 'navbox']):
                    unwanted.decompose()
                
                # Look for paragraphs that contain actual descriptive content
                paragraphs = content.find_all('p')
                for para in paragraphs:
                    text = para.get_text(strip=True)
                    
                    # Skip unwanted content patterns
                    skip_patterns = [
                        'For other', 'This article', 'may refer to:', 'General Information',
                        'Real name:', 'First Appearance:', 'Created by:', 'Affiliations:',
                        'Abilities:', 'Portrayed by:', lambda t: len(t) < 50
                    ]
                    
                    should_skip = False
                    for pattern in skip_patterns:
                        if callable(pattern):
                            if pattern(text):
                                should_skip = True
                                break
                        elif isinstance(pattern, str) and pattern in text:
                            should_skip = True
                            break
                    
                    if not should_skip and len(text) > 50:
                        # Clean up the text
                        import re
                        clean_text = re.sub(r'\s+', ' ', text.strip())
                        # Look for actual character description sentences
                        if any(word in clean_text.lower() for word in ['is a', 'was a', 'known as', 'vigilante', 'villain', 'character', 'member']):
                            character_data['description'] = clean_text[:500] + '...' if len(clean_text) > 500 else clean_text
                            break
            
            self.logger.info(f"Successfully scraped data for {character_name}")
            return character_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {character_name}: {e}")
            return None
    
    def get_character_list_from_category(self) -> List[str]:
        """Get comprehensive list of Batman characters from category pages"""
        character_names = []
        
        # Batman character category pages (corrected URLs)
        category_urls = [
            "https://batman.fandom.com/wiki/Category:Characters",
            "https://batman.fandom.com/wiki/Category:Villains", 
            "https://batman.fandom.com/wiki/Category:Batman_Family",
            "https://batman.fandom.com/wiki/Category:Allies",
            "https://batman.fandom.com/wiki/Category:Supporting_Characters",
            "https://batman.fandom.com/wiki/Category:Anti-Heroes",
            "https://batman.fandom.com/wiki/Category:Anti-Batmen",
            "https://batman.fandom.com/wiki/Category:Blackgate_Prisoners"
        ]
        
        for url in category_urls:
            self.logger.info(f"Getting character list from: {url}")
            response = self.safe_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find character links in category (look for the category member list)
                category_content = soup.find('div', class_='category-page__members')
                if not category_content:
                    category_content = soup.find('div', class_='mw-category')
                
                if category_content:
                    character_links = category_content.find_all('a', href=True)
                    for link in character_links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        # Filter for actual character pages
                        if ('/wiki/' in href and 
                            ':' not in href and 
                            'Category:' not in href and
                            'Template:' not in href and
                            'File:' not in href and
                            title and len(title) > 1):
                            char_name = href.replace('/wiki/', '')
                            if char_name and char_name not in character_names:
                                character_names.append(char_name)
        
        # Comprehensive manual backup list - major Batman universe characters
        comprehensive_characters = [
            # Batman Family
            "Batman", "Bruce_Wayne", "Nightwing", "Dick_Grayson", "Robin_(Dick_Grayson)",
            "Robin_(Jason_Todd)", "Robin_(Tim_Drake)", "Robin_(Damian_Wayne)", "Red_Hood",
            "Red_Robin", "Batgirl_(Barbara_Gordon)", "Batgirl_(Cassandra_Cain)", 
            "Batgirl_(Stephanie_Brown)", "Barbara_Gordon", "Cassandra_Cain", "Stephanie_Brown",
            "Batwoman", "Kate_Kane", "Alfred_Pennyworth", "Lucius_Fox", "Azrael",
            "Jean-Paul_Valley", "Huntress", "Helena_Bertinelli", "Oracle", "Spoiler",
            
            # Major Villains
            "Joker", "Harley_Quinn", "Two-Face", "Harvey_Dent", "Penguin", "Oswald_Cobblepot",
            "Riddler", "Edward_Nygma", "Catwoman", "Selina_Kyle", "Bane", "Scarecrow",
            "Jonathan_Crane", "Ra's_al_Ghul", "Talia_al_Ghul", "League_of_Assassins",
            "Mr._Freeze", "Victor_Fries", "Poison_Ivy", "Pamela_Isley", "Clayface",
            "Killer_Croc", "Waylon_Jones", "Man-Bat", "Kirk_Langstrom", "Deadshot",
            "Floyd_Lawton", "Deathstroke", "Slade_Wilson", "Black_Mask", "Roman_Sionis",
            
            # Secondary Villains
            "Mad_Hatter", "Jervis_Tetch", "Calendar_Man", "Julian_Day", "Victor_Zsasz",
            "Firefly", "Garfield_Lynns", "Ventriloquist", "Arnold_Wesker", "Cluemaster",
            "Arthur_Brown", "Electrocutioner", "Lester_Buchinsky", "KGBeast", "Anatoli_Knyazev",
            "Professor_Pyg", "Lazlo_Valentin", "Anarky", "Lonnie_Machin", "Hush",
            "Thomas_Elliot", "Holiday_Killer", "Alberto_Falcone", "Carmine_Falcone",
            "Sal_Maroni", "Rupert_Thorne", "Tony_Zucco", "Black_Spider", "Eric_Needham",
            
            # Allies & Supporting
            "Commissioner_Gordon", "James_Gordon", "Sarah_Essen", "Harvey_Bullock",
            "Renee_Montoya", "Crispus_Allen", "Detective_Chimp", "Slam_Bradley",
            "Vicki_Vale", "Lois_Lane", "Clark_Kent", "Superman", "Wonder_Woman",
            "The_Flash", "Green_Lantern", "Zatanna", "John_Constantine", "Swamp_Thing",
            
            # Arkham & Blackgate
            "Hugo_Strange", "Jeremiah_Arkham", "Amadeus_Arkham", "Aaron_Cash",
            "Quincy_Sharp", "Warden_Sharp", "Calendar_Man", "Maxie_Zeus",
            "Great_White_Shark", "Warren_White", "Humpty_Dumpty", "Humphry_Dumpler",
            
            # Gotham Characters  
            "Mayor_Hill", "Mayor_Garcia", "Carmine_Falcone", "Sofia_Falcone",
            "Sal_Maroni", "Fish_Mooney", "Penguin's_Mother", "Martha_Wayne",
            "Thomas_Wayne", "Joe_Chill", "Leslie_Thompkins", "Father_Gabriel",
            
            # Teams & Organizations
            "Birds_of_Prey", "Outsiders", "Justice_League", "Teen_Titans", "Titans",
            "Suicide_Squad", "Task_Force_X", "Checkmate", "Secret_Six", "Rogues_Gallery",
            
            # Other Universes/Versions
            "Batman_Beyond", "Terry_McGinnis", "Old_Bruce_Wayne", "Batmite", "Bat-Mite",
            "Earth-2_Batman", "Thomas_Wayne_Batman", "Owlman", "Court_of_Owls", "Talon",
            
            # TV Show Characters (Gotham, Batman TAS, etc.)
            "Fish_Mooney", "Victor_Zsasz", "Theo_Galavan", "Tabitha_Galavan", "Butch_Gilzean",
            "Ed_Nygma", "Kristen_Kringle", "Lee_Thompkins", "Ivy_Pepper", "Silver_St._Cloud",
            "Jerome_Valeska", "Jeremiah_Valeska", "Sofia_Falcone", "Pyg", "Professor_Pyg",
            
            # Arkham Game Characters
            "Warden_Sharp", "Dr._Young", "Frank_Boles", "Aaron_Cash", "Quincy_Sharp",
            "Calendar_Man", "Zsasz", "Amadeus_Arkham", "Jack_Ryder", "Creeper",
            
            # Minor Comics Characters
            "Killer_Moth", "Drury_Walker", "Firefly_(Lynns)", "Garfield_Lynns", "Lock-Up",
            "Lyle_Bolton", "Film_Freak", "Burt_Weston", "Cavalier", "Mortimer_Drake",
            "Cloak", "Dagger", "Monk", "Dala", "Dr._Death", "Karl_Hellfern",
            
            # Supporting Cast
            "Vicki_Vale", "Knox", "Alexander_Knox", "Summer_Gleeson", "Arturo_Rodriguez",
            "Mayor_Krol", "Mayor_Garcia", "Dr._Meridian", "Chase_Meridian", "Max_Shreck",
            "Chip_Shreck", "Selina_Kyle", "Jack_Napier", "Bob_the_Goon", "Lawrence",
            
            # More Villains
            "Magpie", "Margaret_Pye", "Bookworm", "Roddy_McDowall", "King_Tut",
            "Victor_Buono", "Egghead", "Vincent_Price", "Louie_the_Lilac", "Milton_Berle",
            "Ma_Parker", "Shelley_Winters", "Shame", "Cliff_Robertson", "False_Face",
            
            # Animated Series
            "Andrea_Beaumont", "Phantasm", "Ferris_Boyle", "Mary_Dahl", "Baby_Doll",
            "Lloyd_Ventrix", "Feat_of_Clay", "Red_Claw", "Tygrus", "Emile_Dorian",
            
            # More Supporting Characters
            "Matches_Malone", "Stephanie_Brown", "Tim_Drake", "Cassandra_Cain", "Harper_Row",
            "Cullen_Row", "Duke_Thomas", "Signal", "Bluebird", "Spoiler", "Orphan"
        ]
        
        # Merge discovered characters with comprehensive list
        for char in comprehensive_characters:
            if char not in character_names:
                character_names.append(char)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_characters = []
        for char in character_names:
            if char not in seen:
                seen.add(char)
                unique_characters.append(char)
        
        self.logger.info(f"Found {len(unique_characters)} potential characters")
        return unique_characters[:800]  # TRULY MASSIVE - every Batman character possible!
    
    def load_existing_characters(self, filename: str = 'batman_characters_MERGED.json') -> List[str]:
        """Load already scraped character names to avoid duplicates"""
        import os
        filepath = os.path.join('data', filename)
        existing_names = []
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_names = [char['name'] for char in existing_data if 'name' in char]
                    self.logger.info(f"Found {len(existing_names)} already scraped characters")
            except Exception as e:
                self.logger.warning(f"Could not load existing data: {e}")
        
        return existing_names
    
    def scrape_batman_characters_list(self, limit: int = 10, use_comprehensive_list: bool = False, skip_existing: bool = True) -> List[Dict]:
        """Scrape Batman characters - can use comprehensive list or test list"""
        
        if use_comprehensive_list:
            self.logger.info("Getting comprehensive character list...")
            character_names = self.get_character_list_from_category()
        else:
            # Test list for quick testing
            character_names = [
                "Batman", "Robin_(Dick_Grayson)", "Joker", "Catwoman", 
                "Alfred_Pennyworth", "Commissioner_Gordon", "Two-Face",
                "Penguin", "Riddler", "Harley_Quinn"
            ]
        
        # Skip already scraped characters if requested
        if skip_existing:
            existing_names = self.load_existing_characters()
            character_names = [name for name in character_names if name not in existing_names]
            self.logger.info(f"After removing duplicates: {len(character_names)} characters to scrape")
        
        characters_data = []
        total_chars = min(limit, len(character_names))
        
        self.logger.info(f"Starting to scrape {total_chars} NEW characters...")
        
        for i, character in enumerate(character_names[:limit]):
            self.logger.info(f"Scraping character {i+1}/{total_chars}: {character}")
            data = self.scrape_batman_character(character)
            
            if data:
                characters_data.append(data)
                # Save periodically in case of interruption
                if i > 0 and i % 10 == 0:
                    self.save_to_json(characters_data, f'batman_characters_partial_{i}.json')
                    self.logger.info(f"Saved partial data: {len(characters_data)} characters")
            
            # Long break every 25 characters to be extra polite
            if i > 0 and i % 25 == 0:
                self.logger.info("Taking a 2-minute politeness break...")
                time.sleep(120)
        
        return characters_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'batman_characters.json'):
        """Save scraped data to JSON file"""
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data saved to {filepath}")

if __name__ == "__main__":
    import sys
    
    print("Batman Character Scraper")
    print("=" * 40)
    print("1. Quick test (3 characters, ~30 seconds)")
    print("2. Long-running mode (100+ characters, ~2-3 hours)")
    print("3. Custom amount")
    
    mode = input("\nChoose mode (1/2/3): ").strip()
    
    scraper = SafeBatmanScraper(base_delay=2.0, max_delay=4.0)
    
    if mode == "1":
        print("\nStarting quick test with improved description parsing...")
        characters = scraper.scrape_batman_characters_list(limit=3)
        filename = 'test_batman_data.json'
        
    elif mode == "2":
        print("\nStarting long-running comprehensive scrape...")
        print("This will take 6-8 hours and collect 400+ characters - MASSIVE DATASET!")
        print("Progress will be saved every 10 characters")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit("Cancelled")
        characters = scraper.scrape_batman_characters_list(limit=500, use_comprehensive_list=True)
        filename = 'batman_characters_comprehensive.json'
        
    elif mode == "3":
        try:
            limit = int(input("How many characters? "))
            use_comprehensive = input("Use comprehensive list? (y/n): ").strip().lower() == 'y'
            characters = scraper.scrape_batman_characters_list(limit=limit, use_comprehensive_list=use_comprehensive)
            filename = f'batman_characters_{limit}.json'
        except ValueError:
            print("Invalid number")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if characters:
        scraper.save_to_json(characters, filename)
        print(f"\n✅ Successfully scraped {len(characters)} characters!")
        print(f"📁 Saved to: data/{filename}")
        print(f"📋 Log file: scraper.log")
        
        # Show sample data
        if characters:
            print(f"\nSample character: {characters[0]['name']}")
            print(f"Description: {characters[0]['description'][:100]}...")
    else:
        print("❌ No data collected. Check scraper.log for issues.")