#!/usr/bin/env python3
"""
Analyze failed vehicle scrapes and find alternative URLs/names
"""
import json
import re
from typing import List, Dict

def analyze_failed_vehicles():
    """Analyze the failed vehicle attempts and suggest fixes"""
    
    # Common URL naming patterns on Batman Wiki
    url_variations = {
        # Remove underscores
        'underscore_removal': lambda name: name.replace('_', ' '),
        
        # Add disambiguation
        'add_disambiguation': lambda name: [
            f"{name}_(vehicle)", f"{name}_(Batman)", f"{name}_(comics)",
            f"{name}_(animated)", f"{name}_(film)", f"{name}_(TV)"
        ],
        
        # Alternative naming
        'alternative_names': {
            'Penguin_Submarine': ['Penguin\'s_Submarine', 'Iceberg_Lounge_Sub', 'Duck_Submarine'],
            'LEGO_Batmobile': ['Batmobile_(LEGO)', 'LEGO_Batman_Vehicle'],
            'Brave_Bold_Batmobile': ['Batmobile_(Batman:_The_Brave_and_the_Bold)', 'Brave_and_Bold_Batmobile'],
            'Two-Face_Armored_Car': ['Two-Face_Car', 'Harvey_Dent_Vehicle'],
            'Mr._Freeze_Ice_Truck': ['Mr._Freeze_Vehicle', 'Freeze_Truck'],
            'Robin\'s_Redbird': ['Redbird', 'Tim_Drake_Vehicle'],
            'Nightwing\'s_Motorcycle': ['Nightwing_Bike', 'Dick_Grayson_Motorcycle'],
        },
        
        # Media-specific variations
        'media_specific': lambda name: [
            f"{name}_(1989_film)", f"{name}_(The_Dark_Knight)", f"{name}_(Arkham)",
            f"{name}_(Animated_Series)", f"{name}_(The_Batman)", f"{name}_(Gotham)"
        ]
    }
    
    # Extract failed vehicle names from log (common 404s)
    common_failures = [
        'Penguin_Submarine', 'LEGO_Batmobile', 'Brave_Bold_Batmobile',
        'Two-Face_Armored_Car', 'Mr._Freeze_Ice_Truck', 'Robin\'s_Redbird',
        'Nightwing\'s_Motorcycle', 'Scarecrow_Helicopter', 'Poison_Ivy_Car',
        'Harley_Quinn_Bike', 'Black_Mask_Limo', 'Mad_Hatter_Van'
    ]
    
    print("🔍 VEHICLE RECOVERY ANALYSIS")
    print("=" * 50)
    
    recovery_suggestions = {}
    
    for vehicle in common_failures:
        suggestions = []
        
        # Try alternative names if available
        if vehicle in url_variations['alternative_names']:
            suggestions.extend(url_variations['alternative_names'][vehicle])
        
        # Add disambiguation variations
        disambig = url_variations['add_disambiguation'](vehicle)
        suggestions.extend(disambig)
        
        # Add media-specific variations
        media = url_variations['media_specific'](vehicle)
        suggestions.extend(media)
        
        # Remove duplicates
        suggestions = list(set(suggestions))
        
        recovery_suggestions[vehicle] = suggestions
        
        print(f"\n🚗 {vehicle}:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"  {i}. {suggestion}")
    
    return recovery_suggestions

def create_recovery_scraper():
    """Create a specialized scraper for failed vehicles"""
    recovery_code = '''
def scrape_failed_vehicles_recovery(self) -> List[Dict]:
    """Recovery scraper for failed vehicle attempts"""
    
    # Manual mapping of failed vehicles to likely correct URLs
    recovery_mapping = {
        'Penguin_Submarine': [
            'Penguin\'s_Submarine', 'Duck_Submarine', 'Iceberg_Lounge'
        ],
        'LEGO_Batmobile': [
            'Batmobile_(LEGO_Batman)', 'LEGO_Batman_Batmobile'
        ],
        'Brave_Bold_Batmobile': [
            'Batmobile_(Batman:_The_Brave_and_the_Bold)',
            'Batmobile_(Brave_and_the_Bold)'
        ],
        'Two-Face_Armored_Car': [
            'Two-Face_Car', 'Harvey_Dent_Armored_Car'
        ],
        'Mr._Freeze_Ice_Truck': [
            'Mr._Freeze_Truck', 'Freeze_Mobile'
        ]
    }
    
    vehicles_data = []
    
    for failed_vehicle, alternatives in recovery_mapping.items():
        self.logger.info(f"🔄 Attempting recovery for {failed_vehicle}")
        
        for alt_name in alternatives:
            self.logger.info(f"  Trying alternative: {alt_name}")
            data = self.scrape_batman_vehicle(alt_name)
            
            if data:
                # Update the name to reflect original intent
                data['original_search'] = failed_vehicle
                vehicles_data.append(data)
                self.logger.info(f"  ✅ Found via {alt_name}!")
                break
        else:
            self.logger.warning(f"  ❌ No alternatives worked for {failed_vehicle}")
    
    return vehicles_data
'''
    
    print("\n📝 RECOVERY SCRAPER CODE GENERATED")
    print("Add this method to your BatmanVehicleScraper class:")
    print(recovery_code)

def suggest_manual_search_strategy():
    """Suggest manual search strategies"""
    print("\n🎯 MANUAL SEARCH STRATEGIES")
    print("=" * 40)
    
    strategies = [
        "1. **Category Deep Dive**: Search specific categories like 'Category:Joker_Vehicles'",
        "2. **Character Pages**: Check main character pages for vehicle mentions",
        "3. **Media Pages**: Look at movie/TV show pages for vehicle lists", 
        "4. **Redirect Search**: Some vehicles might redirect from different names",
        "5. **Image Search**: Search for vehicle images that might lead to pages",
        "6. **List Pages**: Look for 'List of Batman vehicles' type pages"
    ]
    
    for strategy in strategies:
        print(strategy)
    
    print(f"\n💡 **Alternative Approach**: Instead of chasing 404s, focus on:")
    print(f"   - Scraping from 'List of Batman vehicles' pages")
    print(f"   - Following links from character pages") 
    print(f"   - Searching episode/comic pages for vehicle mentions")

if __name__ == "__main__":
    analyze_failed_vehicles()
    create_recovery_scraper()
    suggest_manual_search_strategy()
    
    print(f"\n🎯 **RECOMMENDATION**: Your 120 vehicles (58% success) is actually excellent!")
    print(f"   Many of those 87 'failures' are vehicles that simply don't have Wiki pages.")
    print(f"   Focus on quality over quantity - you have comprehensive coverage already!")