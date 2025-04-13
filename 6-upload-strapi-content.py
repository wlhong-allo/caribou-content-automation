import requests
import os
from dotenv import load_dotenv
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Strapi credentials from environment variables
STRAPI_URL = os.getenv('STRAPI_URL')
STRAPI_TOKEN = os.getenv('STRAPI_TOKEN')

def print_json(title, data, max_length=1000):
    """Print JSON data in a nice format, truncating if needed"""
    try:
        if isinstance(data, str):
            json_str = data
        else:
            json_str = json.dumps(data, indent=2)
        
        if len(json_str) > max_length:
            print(f"{title}: {json_str[:max_length]}... (truncated)")
        else:
            print(f"{title}: {json_str}")
    except Exception as e:
        print(f"Error printing JSON {title}: {e}")
        print(f"Original data: {data}")

def test_api_access():
    """Test the API access to Strapi CMS with the provided token"""
    headers = {
        'Authorization': f'Bearer {STRAPI_TOKEN}',
    }
    
    endpoint = f"{STRAPI_URL.rstrip('/')}/api/theme-pages"
    print(f"Testing access to: {endpoint}")
    print(f"Using token: {STRAPI_TOKEN[:10]}...")
    
    response = requests.get(endpoint, headers=headers)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    return response

def upload_image(file_path, alt_text=None):
    """Upload an image to Strapi"""
    article_folder = os.getenv('ARTICLE_FOLDER')
    full_path = os.path.join('articles-data', article_folder, file_path)
    
    headers = {
        'Authorization': f'Bearer {STRAPI_TOKEN}'
    }
    
    files = {
        'files': (os.path.basename(full_path), open(full_path, 'rb'), f'image/{os.path.splitext(full_path)[1][1:]}')
    }
    
    data = {}
    if alt_text:
        data['fileInfo'] = json.dumps({'alternativeText': alt_text})
    
    try:
        endpoint = f"{STRAPI_URL.rstrip('/')}/api/upload"
        print(f"Uploading image: {full_path}")
        response = requests.post(endpoint, headers=headers, files=files, data=data)
        response.raise_for_status()
        
        image_data = response.json()[0]
        print(f"Image uploaded successfully with ID: {image_data.get('id')}")
        
        return {
            "id": image_data.get("id"),
            "url": image_data.get("url"),
            "mime": image_data.get("mime"),
            "name": image_data.get("name")
        }
    except Exception as e:
        print(f"Error uploading image {file_path}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")
        raise e

def create_theme_page(title, description, description_html=None, cover_image_id=None, locale="zh-Hans-HK"):
    """Create a new theme-page entry in Strapi CMS"""
    headers = {
        'Authorization': f'Bearer {STRAPI_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "data": {
            "mainTitle": title,
            "mainDescription": description,
            "mainDescriptionInHtml": description_html or description.replace("\n", "<br>"),
            "coverImageAlt": title,
            "locale": locale
        }
    }
    
    if cover_image_id:
        data["data"]["coverImage"] = {"id": cover_image_id}
    
    endpoint = f"{STRAPI_URL.rstrip('/')}/api/theme-pages"
    
    try:
        print(f"\nAttempting to create theme page at: {endpoint}")
        print(f"Data: {data}")
        response = requests.post(endpoint, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404 or response.status_code == 403:
            endpoint_singular = f"{STRAPI_URL.rstrip('/')}/api/theme-page"
            print(f"First attempt failed. Trying singular endpoint: {endpoint_singular}")
            response = requests.post(endpoint_singular, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        else:
            raise e

def upload_hotel_images(hotels):
    """Upload all images for all hotels first and return a mapping"""
    hotel_images_mapping = {}
    
    for hotel in hotels:
        if not hotel.get("images"):
            continue
            
        print(f"\nUploading images for hotel: {hotel['hotel_name']}")
        hotel_gallery_images = []
        
        for img in hotel["images"]:
            try:
                uploaded_image = upload_image(img["path"], img["alt"])
                hotel_gallery_images.append({
                    "url": {
                        "id": uploaded_image["id"]
                    },
                    "caption": img.get("caption", ""),
                    "alt": img.get("alt", "")
                })
                print(f"Successfully uploaded image: {img['path']}")
            except Exception as e:
                print(f"Error uploading image {img['path']}: {e}")
                continue
        
        if hotel_gallery_images:
            hotel_images_mapping[hotel['hotel_name']] = hotel_gallery_images
            print(f"Uploaded {len(hotel_gallery_images)} images for {hotel['hotel_name']}")
        
        time.sleep(1)  # Small delay between hotels
    
    return hotel_images_mapping

def transform_content_to_blocks(content_data, hotel_images_mapping):
    """Transform content data into blocks structure for Strapi"""
    blocks = []
    
    for index, hotel in enumerate(content_data["hotels"], 1):
        blocks.append({
            "__component": "theme-page-block.heading",
            "text": f"{index}. {hotel['hotel_name']}"
        })
        
        if hotel.get("images"):
            blocks.append({
                "__component": "theme-page-block.gallery",
                "images": hotel_images_mapping.get(hotel['hotel_name'], [])
            })
        
        blocks.append({
            "__component": "theme-page-block.hotel-widget",
            "hotelName": hotel["hotel_name"],
            "ctaPriority": "Caribou"
        })
        
        blocks.append({
            "__component": "theme-page-block.paragraph",
            "text": hotel["hotel_paragraph"],
            "html": f"<div>{hotel['hotel_paragraph']}</div>"
        })
    
    if content_data.get("final_paragraph"):
        blocks.append({
            "__component": "theme-page-block.paragraph",
            "text": content_data["final_paragraph"],
            "html": f"<div>{content_data['final_paragraph']}</div>"
        })
    
    return blocks

def update_theme_page_blocks(page_id, blocks):
    """Update theme page with all blocks at once"""
    headers = {
        'Authorization': f'Bearer {STRAPI_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    update_data = {
        "data": {
            "blocks": blocks
        }
    }
    
    endpoint = f"{STRAPI_URL.rstrip('/')}/api/theme-pages/{page_id}"
    response = requests.put(endpoint, json=update_data, headers=headers)
    response.raise_for_status()
    return response.json()

def get_theme_page_blocks(page_id):
    """Get theme page blocks with their IDs and nested data"""
    headers = {
        'Authorization': f'Bearer {STRAPI_TOKEN}',
    }
    
    params = {
        'populate[blocks][populate]': '*',
        'populate[blocks][on][theme-page-block.gallery][populate][images][populate]': '*',
        'populate[blocks][on][theme-page-block.hotel-widget][populate][hotelLinks]': '*',
        'populate[blocks][on][theme-page-block.hotel-widget][populate][image]': '*'
    }
    
    endpoint = f"{STRAPI_URL.rstrip('/')}/api/theme-pages/{page_id}"
    response = requests.get(endpoint, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def update_hotel_widget_links(page_id, blocks, hotel):
    """Update hotel widget with OTA links"""
    logger.info(f"Updating hotel widget for {hotel['hotel_name']}")
    headers = {
        'Authorization': f'Bearer {STRAPI_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    widget_id = None
    for block in blocks:
        if (block.get("__component") == "theme-page-block.hotel-widget" and 
            block.get("hotelName") == hotel["hotel_name"]):
            widget_id = block.get("id")
            break
    
    if not widget_id:
        logger.warning(f"Could not find widget for hotel {hotel['hotel_name']}")
        return
        
    logger.info(f"Found widget ID {widget_id} for hotel {hotel['hotel_name']}")
    
    # Platform name mapping to match Strapi's expected values
    platform_mapping = {
        "agoda": "Agoda",
        "expedia": "Expedia", 
        "trip_com": "Trip.com",
        "hotels_com": "Hotels.com",
        "booking_com": "Booking.com",
        "klook": "Klook",
        "kkday": "kkday"
    }
    
    hotel_links = []
    for platform, url_data in hotel["ota_urls"].items():
        # Skip if url_data is None or not a dict
        if not isinstance(url_data, dict):
            logger.warning(f"Invalid URL data for platform {platform}, skipping")
            continue
            
        # Skip if aff_url is not set or is "no_url"
        aff_url = url_data.get("aff_url")
        if not aff_url or aff_url == "no_url":
            logger.info(f"Skipping {platform} - no affiliate URL available")
            continue
            
        # Convert platform name to proper format
        proper_platform = platform_mapping.get(platform.lower().replace(".", "_"))
        if proper_platform:
            hotel_links.append({
                "link": aff_url,
                "platform": proper_platform
            })
        else:
            logger.warning(f"Unknown platform {platform}, skipping link")
    
    endpoint = f"{STRAPI_URL.rstrip('/')}/api/theme-pages/{page_id}"
    
    response = requests.get(
        endpoint, 
        headers=headers,
        params={'populate[blocks]': '*'}
    )
    response.raise_for_status()
    
    blocks = response.json().get("data", {}).get("attributes", {}).get("blocks", [])
    
    updated = False
    for i, block in enumerate(blocks):
        if block.get("id") == widget_id:
            blocks[i]["hotelLinks"] = hotel_links
            updated = True
            break
    
    if not updated:
        logger.warning(f"Could not find widget with ID {widget_id} in the retrieved blocks")
        return
    
    update_data = {
        "data": {
            "blocks": blocks
        }
    }
    
    for block in blocks:
        if block.get("id") == widget_id:
            logger.info(f"Ready to update hotel widget: ID={block.get('id')}, Links count={len(block.get('hotelLinks', []))}")
            if logger.level <= logging.DEBUG:
                print_json("Hotel widget to update", block)
    
    try:
        logger.info(f"Updating hotel widget with {len(hotel_links)} links...")
        update_response = requests.put(endpoint, json=update_data, headers=headers)
        update_response.raise_for_status()
        logger.info("Hotel widget updated successfully.")
        return update_response.json()
    except Exception as e:
        logger.error(f"Error updating hotel widget: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            if e.response.headers.get('content-type') == 'application/json':
                error_json = e.response.json()
                print_json("Error response", error_json)
            else:
                logger.error(f"Response text: {e.response.text[:1000]}")
        return None

# Main execution
if __name__ == "__main__":
    try:
        # Test API connection
        test_response = test_api_access()
        if test_response.status_code != 200:
            print("API connection failed")
            exit(1)

        # Load the content data
        input_file = "articles-data/top10-ubud/step-6-content-for-upload.json"
        with open(input_file, 'r') as f:
            content_data = json.load(f)
            
        # Upload cover image first if exists
        cover_image_id = None
        if content_data.get("cover_image_path"):
            print("\nUploading cover image...")
            try:
                uploaded_cover = upload_image(
                    content_data["cover_image_path"], 
                    content_data.get("title")
                )
                cover_image_id = uploaded_cover["id"]
                print(f"Cover image uploaded with ID: {cover_image_id}")
            except Exception as e:
                print(f"Warning: Failed to upload cover image: {e}")

        print("\nUploading all hotel images first...")
        hotel_images_mapping = upload_hotel_images(content_data["hotels"])
        
        print("\nCreating theme page...")
        theme_page = create_theme_page(
            title=content_data["title"],
            description=content_data["main_description"],
            cover_image_id=cover_image_id,
            locale=content_data.get("locale", "zh-Hans-HK")  # Default to zh-Hant if not specified
        )
        
        if not theme_page or "data" not in theme_page:
            print("Failed to create theme page")
            exit(1)

        page_id = theme_page["data"]["id"]
        print(f"Created theme page with ID: {page_id}")

        print("\nTransforming content into blocks with pre-uploaded images...")
        blocks = transform_content_to_blocks(content_data, hotel_images_mapping)
        
        print("\nUpdating theme page with blocks...")
        update_theme_page_blocks(page_id, blocks)
        
        print("\nFetching updated blocks with detailed population...")
        updated_page = get_theme_page_blocks(page_id)
        blocks_with_ids = updated_page["data"]["attributes"]["blocks"]
        
        print("\nProcessing hotel widgets...")
        
        hotel_results = []
        
        for hotel in content_data["hotels"]:
            hotel_result = {
                "name": hotel["hotel_name"],
                "widget_updated": False,
                "gallery_updated": hotel["hotel_name"] in hotel_images_mapping
            }
            
            print(f"\nProcessing hotel: {hotel['hotel_name']}")
            
            try:
                print("Updating hotel widget...")
                update_hotel_widget_links(page_id, blocks_with_ids, hotel)
                hotel_result["widget_updated"] = True
            except Exception as e:
                print(f"Failed to update hotel widget for {hotel['hotel_name']}: {e}")
            
            hotel_results.append(hotel_result)
            time.sleep(1)
        
        print("\n--- Upload Summary ---")
        for result in hotel_results:
            print(f"{result['name']}: Widget: {'✓' if result['widget_updated'] else '✗'}, Gallery: {'✓' if result['gallery_updated'] else '✗'}")
            
        successful = all(result["widget_updated"] and result["gallery_updated"] for result in hotel_results)
        if successful:
            print("\nContent upload completed successfully!")
        else:
            print("\nContent upload completed with some errors. Check the summary above.")

    except Exception as e:
        print(f"Error in main process: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")
