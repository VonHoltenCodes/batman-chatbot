#!/usr/bin/env python3
"""
Merge all Batman character data files into one comprehensive dataset
"""
import json
import os
import glob
from typing import List, Dict

def merge_batman_data():
    """Merge all partial and complete Batman character files"""
    data_dir = 'data'
    all_characters = []
    seen_names = set()
    
    # Find all Batman character JSON files
    pattern = os.path.join(data_dir, 'batman_characters*.json')
    files = glob.glob(pattern)
    
    print(f"Found {len(files)} data files to merge:")
    for file in sorted(files):
        print(f"  - {os.path.basename(file)}")
    
    # Process each file
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        print(f"\nProcessing {filename}...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            file_chars = 0
            duplicates = 0
            
            for character in data:
                if 'name' in character:
                    char_name = character['name']
                    
                    if char_name not in seen_names:
                        all_characters.append(character)
                        seen_names.add(char_name)
                        file_chars += 1
                    else:
                        duplicates += 1
            
            print(f"  Added {file_chars} new characters, skipped {duplicates} duplicates")
            
        except Exception as e:
            print(f"  ERROR reading {filename}: {e}")
    
    # Sort characters alphabetically by name
    all_characters.sort(key=lambda x: x.get('name', '').lower())
    
    # Save merged dataset
    output_file = os.path.join(data_dir, 'batman_characters_MERGED.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_characters, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 MERGE COMPLETE! 🎉")
    print(f"📊 Total unique characters: {len(all_characters)}")
    print(f"📁 Saved to: {output_file}")
    
    # Show some stats
    print(f"\n📈 Dataset Statistics:")
    
    # Count characters with descriptions
    with_desc = sum(1 for char in all_characters if char.get('description', '').strip())
    print(f"  Characters with descriptions: {with_desc}")
    
    # Sample some character names
    print(f"\n🦇 Sample characters:")
    for i, char in enumerate(all_characters[:10]):
        print(f"  {i+1}. {char.get('name', 'Unknown')}")
    
    if len(all_characters) > 10:
        print(f"  ... and {len(all_characters) - 10} more!")
    
    return len(all_characters)

if __name__ == "__main__":
    total = merge_batman_data()
    print(f"\n🚀 You now have {total} Batman characters! That's MASSIVE! 🚀")