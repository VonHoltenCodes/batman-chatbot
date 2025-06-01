#!/usr/bin/env python3
"""
Batman Database Consolidator
Merges all scraped data into unified master datasets
"""
import json
import os
import glob
from typing import List, Dict, Set
from collections import defaultdict

class BatmanDataMerger:
    def __init__(self, data_dir: str = '../scraper/data'):
        self.data_dir = data_dir
        self.master_data = {
            'characters': [],
            'vehicles': [],
            'locations': [],
            'storylines': [],
            'organizations': []
        }
        self.stats = defaultdict(int)
        
    def merge_characters(self) -> List[Dict]:
        """Merge all character data files"""
        print("🦇 Merging character data...")
        
        # Find all character files
        character_files = [
            'batman_characters_MERGED.json',
            'batman_characters_comprehensive.json',
            'test_batman_characters.json'
        ]
        
        characters = []
        seen_names = set()
        
        for filename in character_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                print(f"  📁 Processing {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for char in data:
                    char_name = char.get('name', '')
                    if char_name and char_name not in seen_names:
                        # Standardize character data structure
                        standardized_char = {
                            'id': f"char_{len(characters) + 1}",
                            'name': char_name,
                            'type': 'character',
                            'url': char.get('url', ''),
                            'description': char.get('description', ''),
                            'aliases': char.get('aliases', []),
                            'first_appearance': char.get('first_appearance', ''),
                            'relationships': char.get('relationships', []),
                            'powers_abilities': char.get('powers_abilities', []),
                            'source_file': filename
                        }
                        characters.append(standardized_char)
                        seen_names.add(char_name)
                        self.stats['characters_added'] += 1
                    else:
                        self.stats['characters_duplicates'] += 1
        
        print(f"  ✅ Merged {len(characters)} unique characters")
        return characters
    
    def merge_vehicles(self) -> List[Dict]:
        """Merge all vehicle data files"""
        print("🚗 Merging vehicle data...")
        
        # Find all vehicle files
        vehicle_files = [
            'batman_vehicles_COMPLETE.json',
            'test_batman_vehicles.json'
        ]
        
        vehicles = []
        seen_names = set()
        
        for filename in vehicle_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                print(f"  📁 Processing {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for vehicle in data:
                    vehicle_name = vehicle.get('name', '')
                    if vehicle_name and vehicle_name not in seen_names:
                        # Standardize vehicle data structure
                        standardized_vehicle = {
                            'id': f"vehicle_{len(vehicles) + 1}",
                            'name': vehicle_name,
                            'type': 'vehicle',
                            'url': vehicle.get('url', ''),
                            'description': vehicle.get('description', ''),
                            'vehicle_type': vehicle.get('type', ''),
                            'specifications': vehicle.get('specifications', {}),
                            'aliases': vehicle.get('aliases', []),
                            'users': vehicle.get('users', []),
                            'source_file': filename
                        }
                        vehicles.append(standardized_vehicle)
                        seen_names.add(vehicle_name)
                        self.stats['vehicles_added'] += 1
                    else:
                        self.stats['vehicles_duplicates'] += 1
        
        print(f"  ✅ Merged {len(vehicles)} unique vehicles")
        return vehicles
    
    def merge_locations(self) -> List[Dict]:
        """Merge all location data files"""
        print("🏙️ Merging location data...")
        
        # Find all location files
        location_files = [
            'batman_locations_COMPLETE.json',
            'test_batman_locations.json'
        ]
        
        locations = []
        seen_names = set()
        
        for filename in location_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                print(f"  📁 Processing {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for location in data:
                    location_name = location.get('name', '')
                    if location_name and location_name not in seen_names:
                        # Standardize location data structure
                        standardized_location = {
                            'id': f"location_{len(locations) + 1}",
                            'name': location_name,
                            'type': 'location',
                            'url': location.get('url', ''),
                            'description': location.get('description', ''),
                            'category': location.get('category', ''),
                            'details': location.get('details', {}),
                            'aliases': location.get('aliases', []),
                            'connected_locations': location.get('connected_locations', []),
                            'source_file': filename
                        }
                        locations.append(standardized_location)
                        seen_names.add(location_name)
                        self.stats['locations_added'] += 1
                    else:
                        self.stats['locations_duplicates'] += 1
        
        print(f"  ✅ Merged {len(locations)} unique locations")
        return locations
    
    def merge_storylines(self) -> List[Dict]:
        """Merge all storyline data files"""
        print("📚 Merging storyline data...")
        
        # Find all storyline files
        storyline_files = [
            'batman_storylines_COMPLETE.json',
            'batman_storylines_SIMPLE.json',
            'test_batman_storylines.json'
        ]
        
        storylines = []
        seen_names = set()
        
        for filename in storyline_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                print(f"  📁 Processing {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for storyline in data:
                    storyline_name = storyline.get('name', '')
                    if storyline_name and storyline_name not in seen_names:
                        # Standardize storyline data structure
                        standardized_storyline = {
                            'id': f"storyline_{len(storylines) + 1}",
                            'name': storyline_name,
                            'type': 'storyline',
                            'url': storyline.get('url', ''),
                            'description': storyline.get('description', ''),
                            'simple_summary': storyline.get('simple_summary', ''),
                            'category': storyline.get('category', ''),
                            'details': storyline.get('details', {}),
                            'related_stories': storyline.get('related_stories', []),
                            'source_file': filename
                        }
                        storylines.append(standardized_storyline)
                        seen_names.add(storyline_name)
                        self.stats['storylines_added'] += 1
                    else:
                        self.stats['storylines_duplicates'] += 1
        
        print(f"  ✅ Merged {len(storylines)} unique storylines")
        return storylines
    
    def merge_organizations(self) -> List[Dict]:
        """Merge all organization data files"""
        print("🏛️ Merging organization data...")
        
        # Find all organization files
        organization_files = [
            'batman_organizations_COMPLETE.json',
            'test_batman_organizations.json'
        ]
        
        organizations = []
        seen_names = set()
        
        for filename in organization_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                print(f"  📁 Processing {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for org in data:
                    org_name = org.get('name', '')
                    if org_name and org_name not in seen_names:
                        # Standardize organization data structure
                        standardized_org = {
                            'id': f"organization_{len(organizations) + 1}",
                            'name': org_name,
                            'type': 'organization',
                            'url': org.get('url', ''),
                            'description': org.get('description', ''),
                            'category': org.get('category', ''),
                            'details': org.get('details', {}),
                            'aliases': org.get('aliases', []),
                            'notable_operations': org.get('notable_operations', []),
                            'source_file': filename
                        }
                        organizations.append(standardized_org)
                        seen_names.add(org_name)
                        self.stats['organizations_added'] += 1
                    else:
                        self.stats['organizations_duplicates'] += 1
        
        print(f"  ✅ Merged {len(organizations)} unique organizations")
        return organizations
    
    def create_cross_references(self) -> Dict:
        """Create cross-reference mappings between entities"""
        print("🔗 Creating cross-references...")
        
        cross_refs = {
            'character_to_locations': defaultdict(list),
            'character_to_vehicles': defaultdict(list),
            'character_to_organizations': defaultdict(list),
            'location_to_characters': defaultdict(list),
            'vehicle_to_characters': defaultdict(list),
            'organization_to_characters': defaultdict(list)
        }
        
        # Create character name lookup for fuzzy matching
        character_names = {char['name'].lower(): char['id'] for char in self.master_data['characters']}
        location_names = {loc['name'].lower(): loc['id'] for loc in self.master_data['locations']}
        vehicle_names = {veh['name'].lower(): veh['id'] for veh in self.master_data['vehicles']}
        org_names = {org['name'].lower(): org['id'] for org in self.master_data['organizations']}
        
        # Cross-reference characters mentioned in other entities
        for location in self.master_data['locations']:
            location_id = location['id']
            residents = location.get('details', {}).get('residents', [])
            for resident in residents:
                if resident.lower() in character_names:
                    char_id = character_names[resident.lower()]
                    cross_refs['location_to_characters'][location_id].append(char_id)
                    cross_refs['character_to_locations'][char_id].append(location_id)
        
        for vehicle in self.master_data['vehicles']:
            vehicle_id = vehicle['id']
            users = vehicle.get('users', [])
            for user in users:
                if user.lower() in character_names:
                    char_id = character_names[user.lower()]
                    cross_refs['vehicle_to_characters'][vehicle_id].append(char_id)
                    cross_refs['character_to_vehicles'][char_id].append(vehicle_id)
        
        for org in self.master_data['organizations']:
            org_id = org['id']
            members = org.get('details', {}).get('members', [])
            for member in members:
                if member.lower() in character_names:
                    char_id = character_names[member.lower()]
                    cross_refs['organization_to_characters'][org_id].append(char_id)
                    cross_refs['character_to_organizations'][char_id].append(org_id)
        
        # Convert defaultdicts to regular dicts
        cross_refs = {k: dict(v) for k, v in cross_refs.items()}
        
        print(f"  ✅ Created cross-references")
        return cross_refs
    
    def merge_all_data(self) -> Dict:
        """Merge all Batman data into unified structure"""
        print("🦇 BATMAN DATABASE CONSOLIDATION STARTED")
        print("=" * 50)
        
        # Merge each category
        self.master_data['characters'] = self.merge_characters()
        self.master_data['vehicles'] = self.merge_vehicles()
        self.master_data['locations'] = self.merge_locations()
        self.master_data['storylines'] = self.merge_storylines()
        self.master_data['organizations'] = self.merge_organizations()
        
        # Create cross-references
        cross_references = self.create_cross_references()
        
        # Build final database structure
        final_database = {
            'metadata': {
                'total_entities': sum(len(entities) for entities in self.master_data.values()),
                'categories': {
                    'characters': len(self.master_data['characters']),
                    'vehicles': len(self.master_data['vehicles']),
                    'locations': len(self.master_data['locations']),
                    'storylines': len(self.master_data['storylines']),
                    'organizations': len(self.master_data['organizations'])
                },
                'created_at': '2025-06-01',
                'version': '1.0',
                'description': 'Comprehensive Batman Universe Database'
            },
            'data': self.master_data,
            'cross_references': cross_references,
            'statistics': dict(self.stats)
        }
        
        return final_database
    
    def save_master_database(self, database: Dict) -> None:
        """Save the master database to files"""
        print("\n💾 Saving master database...")
        
        # Create output directory
        os.makedirs('master_database', exist_ok=True)
        
        # Save complete database
        with open('master_database/batman_master_database.json', 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        # Save individual category files for easier access
        for category, data in database['data'].items():
            with open(f'master_database/batman_{category}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save cross-references
        with open('master_database/batman_cross_references.json', 'w', encoding='utf-8') as f:
            json.dump(database['cross_references'], f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Saved complete database to master_database/")
    
    def print_final_stats(self, database: Dict) -> None:
        """Print final consolidation statistics"""
        print("\n🎉 CONSOLIDATION COMPLETE!")
        print("=" * 50)
        
        metadata = database['metadata']
        print(f"📊 FINAL BATMAN DATABASE STATISTICS:")
        print(f"  🦇 Characters: {metadata['categories']['characters']}")
        print(f"  🚗 Vehicles: {metadata['categories']['vehicles']}")
        print(f"  🏙️ Locations: {metadata['categories']['locations']}")
        print(f"  📚 Storylines: {metadata['categories']['storylines']}")
        print(f"  🏛️ Organizations: {metadata['categories']['organizations']}")
        print(f"  📈 TOTAL ENTITIES: {metadata['total_entities']}")
        
        print(f"\n🔧 PROCESSING STATISTICS:")
        stats = database['statistics']
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n📁 OUTPUT FILES:")
        print(f"  batman_master_database.json (complete database)")
        print(f"  batman_characters.json ({metadata['categories']['characters']} characters)")
        print(f"  batman_vehicles.json ({metadata['categories']['vehicles']} vehicles)")
        print(f"  batman_locations.json ({metadata['categories']['locations']} locations)")
        print(f"  batman_storylines.json ({metadata['categories']['storylines']} storylines)")
        print(f"  batman_organizations.json ({metadata['categories']['organizations']} organizations)")
        print(f"  batman_cross_references.json (entity relationships)")
        
        print(f"\n🚀 READY FOR CHATBOT DEVELOPMENT!")

def main():
    """Main execution function"""
    merger = BatmanDataMerger()
    
    # Merge all data
    database = merger.merge_all_data()
    
    # Save master database
    merger.save_master_database(database)
    
    # Print final statistics
    merger.print_final_stats(database)

if __name__ == "__main__":
    main()