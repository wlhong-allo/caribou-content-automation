import json
import os
from lib.affiliate_link import convert_link

def process_file(input_file):
    print(f"Processing file: {input_file}")
    
    try:
        # Read JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        changes_made = False
        # Process each hotel
        for hotel in data['hotels']:
            if 'ota_urls' in hotel:
                print(f"\nChecking {hotel['hotel_name']}")
                for ota_key, url_data in hotel['ota_urls'].items():
                    if url_data.get('url', 'no_url') != 'no_url' and 'aff_url' not in url_data:
                        print(f"Converting {ota_key} URL...")
                        aff_url = convert_link(url_data['url'], 'caribou')
                        url_data['aff_url'] = aff_url if aff_url != "Invalid URL" else url_data['url']
                        changes_made = True
                        print(f"Added affiliate URL for {ota_key}")
        
        if changes_made:
            # Write back to same file
            with open(input_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nUpdates saved to: {input_file}")
        else:
            print("\nNo missing affiliate URLs found")
        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    # Get file path from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "articles-data/top10-ubud/step-4.json"
    process_file(input_file)
