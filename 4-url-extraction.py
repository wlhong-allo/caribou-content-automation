import json
import os
import time
import re
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from lib.affiliate_link import convert_link

# Load environment variables from .env file
load_dotenv()

ARTICLE_FOLDER = os.getenv("ARTICLE_FOLDER", "top10-ubud")

# Set your Perplexity API key
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "").strip()
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

print(f"Using Perplexity API key: {PERPLEXITY_API_KEY[:5]}...{PERPLEXITY_API_KEY[-5:]}")

# Define the schema for the URL extraction response
class OtaUrl(BaseModel):
    url: str = Field(..., description="URL to the hotel's landing page on the OTA")
    ota_symbol: str = Field(..., description="Symbol of the OTA (agoda, expedia, trip_com, hotels_com, booking_com)")

# Read the extraction prompt
with open("prompts/4-url-extraction-prompt.txt", "r") as f:
    extraction_prompt_template = f.read()

# Read the step-3.json file
try:
    with open(f"articles-data/{ARTICLE_FOLDER}/step-3.json", "r") as f:
        data = json.load(f)
    print(f"Successfully loaded step-3.json with {len(data['hotels'])} hotels")
except Exception as e:
    print(f"Error loading step-3.json: {e}")
    raise

def extract_json_from_text(text):
    """Extract JSON object from text that might contain other content"""
    try:
        # Look for JSON pattern with regex
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, text)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
    except:
        pass
    return None

def test_api_connection():
    """Test the Perplexity API connection with a simple request"""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello world"}
        ]
    }
    
    try:
        print("Testing API connection...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Test response status: {response.status_code}")
        if response.status_code == 200:
            print("API connection successful!")
            return True
        else:
            print(f"API connection failed: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"API connection test error: {e}")
        return False

def call_perplexity_api(hotel_name, max_retries=3, retry_delay=2):
    """Call Perplexity API to extract URLs for a hotel"""
    prompt = extraction_prompt_template.replace('__HOTEL_NAME__', hotel_name)
    
    # System prompt for better structured output
    system_content = """You are a helpful assistant for extracting URLs. 

    1. Find the direct URLs for the hotel on each OTA
    2. For each OTA, extract both the landing page URL
    3. Return in the exact JSON format requested
    4. Make sure all URLs are valid and complete
    5. If that OTA have country and language in the url, please include the specified country and language in the url
    """
    
    # Setup schema for structured output
    url_schema = {
        "type": "object",
        "properties": {
            "agoda": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "expedia": {
                "type": "object", 
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "trip_com": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "hotels_com": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "booking_com": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            }
        }
    }
    
    # API endpoint
    url = "https://api.perplexity.ai/chat/completions"
    
    # Headers with API key
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Request payload
    payload = {
        "model": "sonar-pro",  # Using sonar model which supports structured outputs
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": url_schema}
        },
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    for attempt in range(max_retries):
        try:
            print(f"Sending request to Perplexity API (attempt {attempt+1}/{max_retries})...")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        extracted = extract_json_from_text(content)
                        if extracted:
                            return extracted
            
            if response.status_code == 401:
                print("Authentication error - check your API key")
                return None
            
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
    
    return None

def retry_missing_urls(hotel_name, missing_otas, max_retries=2):
    """Retry extracting URLs for OTAs that returned no_url"""
    for retry in range(max_retries):
        print(f"\nRetry {retry + 1}/{max_retries} for missing URLs in {hotel_name}")
        prompt = f"Find ONLY the direct URLs for {hotel_name} on these specific OTAs: {', '.join(missing_otas)}."
        url_data = call_perplexity_api(prompt)
        
        if url_data:
            results = {}
            for ota in missing_otas:
                if ota in url_data and "url" in url_data[ota]:
                    results[ota] = {
                        "url": url_data[ota]["url"]
                    }
            if results:
                return results
    return {}

# Test API connection before starting the extraction
if not test_api_connection():
    print("API connection test failed. Please check your API key and try again.")
    exit(1)

# Process each hotel
for i, hotel in enumerate(data["hotels"]):
    print(f"\nProcessing hotel {i+1}/{len(data['hotels'])}: {hotel['hotel_name']}")
    
    url_data = call_perplexity_api(hotel["hotel_name"])
    
    if url_data:
        hotel["ota_urls"] = {}
        for ota in ["agoda", "expedia", "trip_com", "hotels_com", "booking_com"]:
            if ota in url_data:
                hotel["ota_urls"][ota] = {
                    "url": url_data[ota].get("url", "no_url")
                }
            else:
                hotel["ota_urls"][ota] = {"url": "no_url"}
        
        # Check for missing URLs
        missing_otas = [
            ota for ota in ["agoda", "expedia", "trip_com", "hotels_com", "booking_com"]
            if ota not in hotel["ota_urls"] or hotel["ota_urls"][ota]["url"] == "no_url"
        ]
        
        if missing_otas:
            print(f"Missing URLs for OTAs: {missing_otas}")
            retry_results = retry_missing_urls(hotel["hotel_name"], missing_otas)
            for ota_key, url_data in retry_results.items():
                if url_data["url"] != "no_url":
                    hotel["ota_urls"][ota_key] = url_data
    else:
        print(f"No URL data found for {hotel['hotel_name']}")
    
    time.sleep(2)

# Convert URLs to affiliate URLs before output
TRACKING_CODE = os.getenv("TRACKING_CODE", "caribou")
for hotel in data["hotels"]:
    if "ota_urls" in hotel:
        for ota_key, url_data in hotel["ota_urls"].items():
            if url_data["url"] != "no_url":
                aff_url = convert_link(url_data["url"], TRACKING_CODE)
                url_data["aff_url"] = aff_url if aff_url != "Invalid URL" else url_data["url"]

# Write output
output_path = f"articles-data/{ARTICLE_FOLDER}/step-4.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Processing complete. Results saved to {output_path}")
