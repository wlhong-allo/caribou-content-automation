from urllib.parse import urlparse, parse_qs

def convert_link(url: str, tracking_code: str) -> str:
    table_data = [
        {"Platform": "Trip.com", "Type": "Pre-defined", "Key": "Allianceid", "Value": "3883897"},
        {"Platform": "Trip.com", "Type": "Pre-defined", "Key": "SID", "Value": "22890196"},
        {"Platform": "Trip.com", "Type": "Advisor Tracking", "Key": "trip_sub1", "Value": "caribou"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "cityId", "Value": "617"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "hotelId", "Value": "6463598"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "checkIn", "Value": "45208"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "checkOut", "Value": "45215"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "adult", "Value": "2"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "children", "Value": "2"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "crn", "Value": "2"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "curr", "Value": "HKD"},
        {"Platform": "Trip.com", "Type": "Extracted", "Key": "ages", "Value": "5,9"},
        {"Platform": "Booking.com", "Type": "Pre-defined", "Key": "wId", "Value": "68904"},
        {"Platform": "Booking.com", "Type": "Pre-defined", "Key": "pId", "Value": "18920"},
        {"Platform": "Booking.com", "Type": "Advisor Tracking", "Key": "mId", "Value": "advisorName"},
        {"Platform": "Agoda", "Type": "Pre-defined", "Key": "pcs", "Value": "1"},
        {"Platform": "Agoda", "Type": "Pre-defined", "Key": "cid", "Value": "1917804"},
        {"Platform": "Agoda", "Type": "Advisor Tracking", "Key": "tag", "Value": "caribou"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "finalPriceView", "Value": "1"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "locale", "Value": "en-us"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "currency", "Value": "HKD"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "isRealUser", "Value": "true"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "checkIn", "Value": "45208"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "checkOut", "Value": "45215"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "rooms", "Value": "1"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "adults", "Value": "2"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "children", "Value": "0"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "los", "Value": "4"},
        {"Platform": "Agoda", "Type": "Extracted", "Key": "childAges", "Value": "5,10"},
        {"Platform": "KKDay", "Type": "Pre-defined", "Key": "cid", "Value": "16370"},
        {"Platform": "KKDay", "Type": "Advisor Tracking", "Key": "ud1", "Value": "caribou"},
        {"Platform": "Klook", "Type": "Pre-defined", "Key": "aid", "Value": "39112"},
        {"Platform": "Klook", "Type": "Advisor Tracking", "Key": "aff_label1", "Value": "caribou"},
        {"Platform": "Expedia", "Type": "Pre-defined", "Key": "camref", "Value": "1011lBWuC"},
        {"Platform": "Expedia", "Type": "Advisor Tracking", "Key": "pubref", "Value": "caribou"},
        {"Platform": "Expedia", "Type": "Pre-defined", "Key": "p_id", "Value": "1101l502970"},
        {"Platform": "Hotels.com", "Type": "Pre-defined", "Key": "wId", "Value": "68904"},
        {"Platform": "Hotels.com", "Type": "Pre-defined", "Key": "pId", "Value": "11757"},
        {"Platform": "Hotels.com", "Type": "Advisor Tracking", "Key": "mId", "Value": "advisorName"}
    ]

    def is_valid_url(url: str) -> bool:
        try:
            urlparse(url)
            return True
        except:
            return False

    # def is_valid_phone_number(phone_number: str) -> bool:
    #     return phone_number.isdigit() and 10 <= len(phone_number) <= 15

    if not is_valid_url(url):
        return "Invalid URL"

    # if not is_valid_phone_number(tracking_code):
    #     return "Invalid Phone Number"

    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    matching_rows = [row for row in table_data if row["Platform"].lower() in domain.lower()]

    expedia_domain = "expedia" in domain
    hotels_com_domain = "hotels.com" in domain or "hotels.cn" in domain
    klook_domain = "klook.com" in domain
    booking_domain = "booking.com" in domain

    if expedia_domain:
        root_domain = "https://www.chinesean.com/affiliate/clickBanner.do?"
        parameters = ["wId=68904", "pId=22377", f"mId={tracking_code}"]
        parameters_string = "&".join(parameters)
        partnerize_root_domain = "https://prf.hn/click/"
        partnerize_parameters = ["camref:1011ljPRX", "pubref:CHINESEANTXID", "ar:CHINESEANID"]
        partnerize_parameters_string = "/".join(partnerize_parameters)
        return f"{root_domain}{parameters_string}&targetURL={partnerize_root_domain}{partnerize_parameters_string}/destination:{url}"

    elif hotels_com_domain:
        root_domain = "https://www.chinesean.com/affiliate/clickBanner.do?"
        parameters = ["wId=68904", "pId=11757", f"mId={tracking_code}"]
        parameters_string = "&".join(parameters)
        partnerize_root_domain = "https://prf.hn/click/"
        partnerize_parameters = ["camref:1100l8vyR", "pubref:CHINESEANTXID", "ar:CHINESEANID"]
        partnerize_parameters_string = "/".join(partnerize_parameters)
        return f"{root_domain}{parameters_string}&targetURL={partnerize_root_domain}{partnerize_parameters_string}/destination:{url}"

    elif booking_domain:
        root_domain = "https://www.chinesean.com/affiliate/clickBanner.do?"
        parameters = ["wId=68904", "pId=18920", f"mId={tracking_code}"]
        parameters_string = "&".join(parameters)
        return f"{root_domain}{parameters_string}&targetURL={url}?aid=880505&lang=zh-tw&label=affnetca-link-TW-index-1_pub-CHINESEANID_site-CHINESEANID_pname-CHINESEANWEB_clkid-CHINESEANTXID&utm_source=affnetca&utm_medium=link&utm_campaign=TW&utm_term=index-1&utm_content=CHINESEANID"

    elif klook_domain:
        root_domain = "https://affiliate.klook.com/redirect?"
        parameters = ["aid=39112", f"aff_label1={tracking_code}"]
        parameters_string = "&".join(parameters)
        return f"{root_domain}{parameters_string}&k_site={url}"

    elif matching_rows:
        updated_params = []
        
        # Pre-defined parameters
        for row in matching_rows:
            if row["Type"] == "Pre-defined":
                updated_params.append(f"{row['Key']}={row['Value']}")

        # Advisor tracking
        for row in matching_rows:
            if row["Type"] == "Advisor Tracking":
                updated_params.append(f"{row['Key']}={tracking_code}")

        # Extracted parameters
        query_params = parse_qs(parsed_url.query)
        for key, value in query_params.items():
            matching_row = next(
                (row for row in matching_rows 
                if row["Type"] == "Extracted" and row["Key"].lower() == key.lower()),
                None
            )
            if matching_row:
                updated_params.append(f"{key}={value[0]}")

        updated_params_string = "&".join(updated_params)
        return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{updated_params_string}"

    return "The platform is not yet covered"

if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path

    # Get file path from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "articles-data/top10-ubud/step-4.json"
    
    print(f"Processing file: {input_file}")
    
    try:
        # Read JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Process each hotel
        for hotel in data['hotels']:
            if 'ota_urls' in hotel:
                print(f"\nProcessing {hotel['hotel_name']}")
                for ota_key, url_data in hotel['ota_urls'].items():
                    if url_data['url'] != 'no_url':
                        print(f"Converting {ota_key} URL...")
                        aff_url = convert_link(url_data['url'], 'caribou')
                        url_data['aff_url'] = aff_url
                        print(f"Result: {aff_url[:100]}...")
        
        # Write back to file
        output_file = Path(input_file)
        output_file = output_file.parent / f"{output_file.stem}_with_aff{output_file.suffix}"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nProcessing complete. Results saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
