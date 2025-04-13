import os
import json
import asyncio
import aiohttp
import re
import time
from PIL import Image
from io import BytesIO
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
from pydantic import BaseModel, Field
from typing import ClassVar, Dict, List, Any, Optional
from bs4 import BeautifulSoup
import random
from dotenv import load_dotenv

load_dotenv()
# Environment variables
ARTICLE_FOLDER = os.getenv("ARTICLE_FOLDER", "top10-ubud")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "").strip()
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

class HotelImageUrls(BaseModel):
    image_url: str = Field(..., description="Image URL.")
    image_caption: str = Field(..., description="Caption for the image.")
    description_id: int = Field(..., description="ID of the description.")
    description: str = Field(..., description="Description text.")
    
    # Fixed prompt template with proper placeholders
    PROMPT: ClassVar[str] = """From the crawled content, Look for MediaGalleryCarousel from the <h3> tag, and from there find the best matched image URLs and their captions corresponding to the below list of descriptions:

{descriptions}

Please find the high resolution image URLs from the photo album view. One extracted image JSON format should look like this: 
{{"image_url": "https://example.com/image.jpg", "image_caption": "Caption for the image.", "description_id": 1, "description": "DESCRIPTION_TEXT"}}."""

    @classmethod
    def schema(cls):
        return cls.model_json_schema()

async def download_and_resize_image(session, url, filepath, max_size=1000):
    """
    Download image from URL, resize to max_size while maintaining aspect ratio, and save to filepath as JPG
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Clean up URL - remove any parameters after .jpg, .jpeg, etc.
        cleaned_url = url
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        for ext in image_extensions:
            if ext in url.lower():
                base_url = url.lower().split(ext)[0] + ext
                cleaned_url = base_url
                break
                
        print(f"Downloading image from: {cleaned_url}")
        
        async with session.get(cleaned_url, headers=headers) as response:
            if response.status == 200:
                # Get image data
                image_data = await response.read()
                
                # Check if content is valid
                if len(image_data) < 1000:  # Less than 1KB is probably not a valid image
                    print(f"Warning: Image from {cleaned_url} is too small ({len(image_data)} bytes)")
                    return False
                
                try:
                    # Open image from bytes
                    img = Image.open(BytesIO(image_data))
                    
                    # Calculate new dimensions to maintain aspect ratio
                    width, height = img.size
                    if width > height:
                        # Landscape mode
                        new_width = max_size
                        new_height = int(height * (max_size / width))
                    else:
                        # Portrait mode
                        new_height = max_size
                        new_width = int(width * (max_size / height))
                    
                    # Resize image
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Convert to RGB if needed (to handle PNG transparency)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    # Save as JPG
                    img.save(filepath, 'JPEG', quality=90)
                    
                    print(f"Successfully downloaded, resized and saved image to {filepath}")
                    return True
                except Exception as e:
                    print(f"Error processing image with PIL: {e}")
                    return False
            else:
                print(f"Failed to download {cleaned_url}, status code: {response.status}")
                return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

async def crawl_with_retry(crawler: AsyncWebCrawler, url: str, run_config: CrawlerRunConfig, max_retries: int = 3):
    """Retry crawler.arun with exponential backoff using the provided crawler instance"""
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
                print(f"Attempt {retry_count+1}/{max_retries} for URL: {url}")
                result = await crawler.arun(url=url, config=run_config)
                return result
                
        except Exception as e:
            last_error = e
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Error during crawl attempt {retry_count}: {e}. Waiting {wait_time} seconds before retry.")
            await asyncio.sleep(wait_time)
    
    # All retries failed
    print(f"All retries failed for URL: {url}. Last error: {last_error}")
    return None  # Return None instead of raising an exception

async def crawl_hotel_images(crawler: AsyncWebCrawler, hotel_name: str, url: str):
    """
    Crawl images from the Expedia photo gallery URL and collect all image URLs.
    Using CSS-based content selection for targeting specific elements.
    """
    print(f"Crawling images for hotel: {hotel_name} using URL: {url}")
    
    # Step 1: Initial page load with button click to open gallery
    js_code = """
    (function() {
      try {
        var btn = document.querySelector("#Overview button");
        if (btn) {
          btn.click();
          return true;
        }
        return false;
      } catch(e) {
        console.error(e);
        return false;
      }
    })();
    """
    
    # Wait for the thumbnail gallery to appear
    wait_for_thumbnail = "css:#app-layer-thumbnail-gallery"
    
    # Create first step config to open the thumbnail gallery
    thumbnail_config = CrawlerRunConfig(
        word_count_threshold=1,
        js_code=js_code,
        wait_for=wait_for_thumbnail,
        cache_mode=CacheMode.BYPASS,
        session_id=f"hotel_{hotel_name.replace(' ', '_')}"
    )
    
    # Execute first step
    try:
        result = await crawl_with_retry(crawler, url, thumbnail_config)
        if result is None:
            print(f"Failed to open thumbnail gallery for {hotel_name}")
            return []
        
        print(f"Thumbnail gallery opened for {hotel_name}")
        
        # Step 2: Click on the first thumbnail to open the media gallery
        media_js = """
        (function() {
          try {
            var btn = document.querySelector("#app-layer-thumbnail-gallery li button");
            if (btn) {
              btn.click();
              return true;
            }
            return false;
          } catch(e) {
            console.error(e);
            return false;
          }
        })();
        """
        
        # Wait for media gallery to appear
        wait_for_media = "css:#app-layer-media-gallery"
        
        # Create second step config to open the media gallery
        media_config = CrawlerRunConfig(
            word_count_threshold=1,
            js_code=media_js,
            wait_for=wait_for_media,
            js_only=True,  # Continue in the same session
            session_id=f"hotel_{hotel_name.replace(' ', '_')}",
            cache_mode=CacheMode.BYPASS
        )
        
        # Execute second step
        media_result = await crawl_with_retry(crawler, url, media_config)
        if media_result is None:
            print(f"Failed to open media gallery for {hotel_name}")
            return []
        
        print(f"Media gallery opened for {hotel_name}")
        
        # Step 3: Extract images using JsonCssExtractionStrategy
        print(f"Extracting images for {hotel_name} using JsonCssExtractionStrategy")
        
        # Define the image extraction schema
        image_schema = {
            "name": "GalleryImages",
            "baseSelector": "div.uitk-image-placeholder",
            "fields": [
                {
                    "name": "image_url", 
                    "selector": "img.uitk-image-media", 
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "image_caption", 
                    "selector": "img.uitk-image-media", 
                    "type": "attribute",
                    "attribute": "alt"
                }
            ]
        }
        
        # Create extraction strategy
        image_extraction_strategy = JsonCssExtractionStrategy(image_schema)
        
        # Create extraction config with the strategy and CSS selector targeting only the gallery
        extract_config = CrawlerRunConfig(
            # Target only the gallery container
            css_selector="#app-layer-media-gallery",
            # Extract with our defined schema
            extraction_strategy=image_extraction_strategy,
            #extraction_strategy=None,  # Extract raw HTML for debugging
            js_only=True,
            session_id=f"hotel_{hotel_name.replace(' ', '_')}",
            cache_mode=CacheMode.BYPASS
        )
        
        # Execute extraction
        extract_result = await crawl_with_retry(crawler, url, extract_config)
        if extract_result is None:
            print(f"Failed to extract images for {hotel_name}")
            return []
        

        print("Partial HTML :", extract_result.cleaned_html)

        print(f"Extracted content for {hotel_name}: {extract_result.extracted_content}")
        # Process the extracted content from JSON
        image_urls = []
        try:
            # Parse the extracted content
            if isinstance(extract_result.extracted_content, str):
                extracted_data = json.loads(extract_result.extracted_content)
            else:
                extracted_data = extract_result.extracted_content
            
            # Handle the case where extracted_data is None
            if extracted_data is None:
                print(f"No image data extracted for {hotel_name}")
                return []
                
            # Ensure we have a list
            if not isinstance(extracted_data, list):
                extracted_data = [extracted_data]
            
            print(f"Extracted {extracted_data} from {hotel_name}")
            # Process each image item
            for i, img in enumerate(extracted_data):
                # Skip entries without URLs or with invalid URLs
                if not img.get('image_url') or 'http' not in img.get('image_url', ''):
                    continue
                
                image_urls.append({
                    'image_url': img.get('image_url', ''),
                    'image_caption': img.get('image_caption', f'Hotel image {i+1}'),
                    'description_id': i+1,
                    'description': img.get('image_caption', f'Hotel image {i+1}')
                })
            
            print(f"Extracted {len(image_urls)} images for {hotel_name}")
            # Ensure images are unique
            seen_urls = set()
            unique_images = []
            for img in image_urls:
                if img['image_url'] not in seen_urls:
                    seen_urls.add(img['image_url'])
                    unique_images.append(img)
            
            if unique_images:
                print(f"Successfully extracted {len(unique_images)} unique images for {hotel_name}")
                # Print the first few images
                for i, img in enumerate(unique_images[:3]):
                    print(f"Image {i+1}: {img['image_url']}")
                if len(unique_images) > 3:
                    print(f"... and {len(unique_images) - 3} more images")
                return unique_images
            else:
                print(f"No valid images found for {hotel_name}")
                return []
        except Exception as e:
            print(f"Error processing image data for {hotel_name}: {e}")
            return []
    
    except Exception as e:
        print(f"Error during crawl process for {hotel_name}: {e}")
        return []

async def fallback_to_original_images(hotel):
    """Use original image URLs if crawling fails"""
    print(f"Using original images for {hotel['hotel_name']}")
    return hotel

async def rewrite_caption_with_perplexity(caption: str, hotel_paragraph: str) -> str:
    """Use Perplexity API to rewrite the image caption based on hotel context"""
    if not PERPLEXITY_API_KEY:
        print("No Perplexity API key found, using original caption")
        return caption
        
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Given this hotel description:
{hotel_paragraph}

Please rewrite this image caption to enhance SEO, make it more descriptive and engaging, while maintaining accuracy:
{caption}

Keep it concise (max 100 characters) and focus on the visual elements."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json={
                    "model": "pplx-7b-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    new_caption = result["choices"][0]["message"]["content"].strip()
                    return new_caption
                else:
                    print(f"Error from Perplexity API: {response.status}")
                    return caption
    except Exception as e:
        print(f"Error using Perplexity API: {e}")
        return caption

async def process_hotel(crawler: AsyncWebCrawler, hotel: dict, base_images_dir: str):
    """Process a single hotel to download images and update paths using the provided crawler instance"""
    hotel_name = hotel["hotel_name"]
    
    # Create a folder number prefix based on hotel index
    hotel_index = 1 # Default
    if data and 'hotels' in data:
        for i, h in enumerate(data["hotels"], 1):
            if h["hotel_name"] == hotel_name:
                hotel_index = i
                break
        
    # Create hotel folder name from the hotel name with index prefix using only first two words of the hotel name
    hotel_name_parts = hotel_name.split()[:2]
    hotel_folder_name = f"{hotel_index}-{'-'.join(hotel_name_parts).lower()}"
    hotel_image_dir = os.path.join(base_images_dir, hotel_folder_name)
    os.makedirs(hotel_image_dir, exist_ok=True)
    
    # Initialize images array if not exists
    if "images" not in hotel:
        hotel["images"] = []
    
    # CHANGE 1: Only use Expedia URL for image extraction
    gallery_url = None
    if "ota_urls" in hotel and "expedia" in hotel["ota_urls"] and hotel["ota_urls"]["expedia"].get("url"):
        gallery_url = hotel["ota_urls"]["expedia"]["url"]
        if gallery_url == "no_url":
            gallery_url = None
    
    # If no Expedia URL found, skip crawling
    crawled_images = []
    if not gallery_url:
        print(f"No valid Expedia gallery URL found for {hotel_name}. Skipping crawl.")
    else:
        # Use the provided crawler instance to get images
        try:
            crawled_images = await crawl_hotel_images(crawler, hotel_name, gallery_url)
            # Limit to 8 images and randomize order
            if len(crawled_images) > 8:
                crawled_images = random.sample(crawled_images, 8)
            else:
                random.shuffle(crawled_images)
        except Exception as e:
            print(f"Error during crawl_hotel_images call for {hotel_name}: {e}")
            # crawled_images remains empty

    # If we have crawled images, download, resize and update the hotel's image paths
    if crawled_images:
        print(f"Preparing to download and process {len(crawled_images)} images for {hotel_name}")
        
        # Download, resize, and save images
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
            download_tasks = []
            image_mappings = []  # Track which image goes to which hotel image
            
            # Prepare download tasks
            for crawled_image in crawled_images:
                # Create a descriptive filename from caption
                caption = crawled_image.get("image_caption", "image")
                
                # Rewrite caption using Perplexity API
                new_caption = await rewrite_caption_with_perplexity(caption, hotel["hotel_paragraph"])
                
                # Remove commas and other special characters from filename
                sanitized_desc = re.sub(r'[\\/*?:"<>|,]', "", caption).lower().replace(' ', '-')[:50]
                
                # Create filename without index prefix
                filename = f"{sanitized_desc}.jpg"
                filepath = os.path.join(hotel_image_dir, filename)
                
                # Add to download tasks
                download_tasks.append(download_and_resize_image(session, crawled_image["image_url"], filepath))
                
                # Track which hotel image this corresponds to
                image_mappings.append({
                    "filepath": filepath,
                    "relative_path": f"hotels-data/{hotel_folder_name}/{filename}",
                    "caption": new_caption,
                    "alt": f"{hotel_name} - {new_caption}"
                })
            
            # Process downloads concurrently
            if download_tasks:
                results = await asyncio.gather(*download_tasks, return_exceptions=True)
                
                # Update hotel image paths based on download results
                successful_images = []
                for i, result in enumerate(results):
                    # If download was successful, add to successful images
                    if result is True:
                        mapping = image_mappings[i]
                        successful_images.append({
                            "path": mapping["relative_path"],
                            "caption": mapping["caption"],
                            "alt": mapping["alt"]
                        })
                    else:
                        print(f"Failed to download image {i+1}: {result}")
                
                # Randomize final order and update hotel images
                random.shuffle(successful_images)
                hotel["images"] = successful_images
                
                print(f"Successfully downloaded and processed {len(successful_images)} images for {hotel_name}")
    else:
        print(f"No images crawled for {hotel_name}, keeping original image URLs.")
    
    return hotel

async def process_hotel_with_error_handling(crawler: AsyncWebCrawler, hotel: dict, base_images_dir: str):
    """Wrapper around process_hotel with error handling, accepting the crawler instance"""
    try:
        return await process_hotel(crawler, hotel, base_images_dir)
    except Exception as e:
        print(f"Critical error processing hotel {hotel.get('hotel_name', 'unknown')}: {e}")
        # Return the original hotel data in case of critical failure during processing
        return hotel

# Global data variable to help with hotel indexing
data = None

async def main():
    global data
    
    # Create base images directory
    base_dir = "articles-data"
    article_dir = os.path.join(base_dir, ARTICLE_FOLDER)
    hotels_data_dir = os.path.join(article_dir, "hotels-data")
    os.makedirs(hotels_data_dir, exist_ok=True)
    
    # Read step-4.json
    input_file = os.path.join(article_dir, "step-4.json")
    output_file = os.path.join(article_dir, "step-5.json")
    
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
        print(f"Successfully loaded {input_file} with {len(data['hotels'])} hotels")
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return
    
    # Initialize the crawler ONCE
    browser_config = BrowserConfig(
        verbose=True,
        headless=False  # Set to False to watch the browser actions for debugging
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Process hotels one by one using the single crawler instance
        for i, hotel in enumerate(data["hotels"]):
            try:
                print(f"Processing hotel {i+1}/{len(data['hotels'])}: {hotel['hotel_name']}")
                # Pass the crawler instance to the processing function
                processed_hotel = await process_hotel_with_error_handling(crawler, hotel, hotels_data_dir)
                data["hotels"][i] = processed_hotel
                
                # Save after each successful hotel processing to preserve progress
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
                
                # Wait between hotels to avoid overwhelming the browser and API
                if i < len(data["hotels"]) - 1:
                    wait_time = 5
                    print(f"Waiting {wait_time} seconds before processing next hotel...")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                print(f"Unhandled error in main loop for hotel {hotel.get('hotel_name', 'unknown')} at index {i}: {e}")
                # Optionally decide whether to continue or break
                # continue
    
    # Final save (outside the crawler context)
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Processing complete. Results saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main()) 