from datetime import datetime, timedelta
import requests
import os
import time
import json
import boto3
# Faizan
# Get access token from s3
def load_credentials_from_s3(client_code):
    bucket_name = "ads-credentials-bucket-prod"
    key = f"clients/{client_code}/credentials.json"

    s3 = boto3.client("s3")

    try:
        response = s3.get_object(
            Bucket=bucket_name,
            Key=key
        )
        creds = json.loads(
            response["Body"].read().decode("utf-8")
        )

        return creds

    except s3.exceptions.NoSuchKey:
        raise Exception(f"Credentials file not found for client: {client_code}")

    except Exception as e:
        raise Exception(f"S3 credential load failed: {str(e)}")

# ------------------ ACCESS TOKEN -----------------
def get_access_token(creds):
    """Get access token from Amazon Advertising API."""
    url = "https://api.amazon.co.uk/auth/o2/token"
    form_data = {
        "grant_type": "refresh_token",
        "client_id": creds['client_id'],
        "client_secret": creds['client_secret'],
        "refresh_token": creds['refresh_token'],
        "scope": "profile",
        "profile_id": creds['profile_id']
    }
    
    try:
        response = requests.post(url, data=form_data)
        print(f"Token request status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Token error response: {response.text}")
            raise Exception(f"Failed to get access token: {response.text}")
        
        response_data = response.json()
        # Return clean token without any whitespace
        return response_data['access_token'].strip()
    except Exception as e:
        print(f"Failed to get access token: {str(e)}")
        raise

if __name__ == "__main__":
    print(get_access_token())


# -------------------- Branch Id and Entity Id ----------------------------
# _BRAND_ENTITY_CACHE = None


# def get_brand_entity_id(access_token, max_retries=5):
#     global _BRAND_ENTITY_CACHE

#     # ✅ agar pehle hi aa chuka hai to dobara API call nahi
#     if _BRAND_ENTITY_CACHE:
#         return _BRAND_ENTITY_CACHE

#     url = "https://advertising-api-eu.amazon.com/brands"
#     access_token = access_token.strip()

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Amazon-Advertising-API-ClientId": creds["client_id"],
#         "Amazon-Advertising-API-Scope": creds["profile_id"]
#     }

#     for attempt in range(1, max_retries + 1):
#         response = requests.get(url, headers=headers)

#         print(f"Brand API attempt {attempt}, status: {response.status_code}")

#         # ✅ SUCCESS
#         if response.status_code == 200:
#             data = response.json()

#             if not isinstance(data, list) or len(data) == 0:
#                 raise Exception("No brands found for this seller")

#             brand_entity_id = data[0]["brandEntityId"]

#             # ✅ cache store
#             _BRAND_ENTITY_CACHE = brand_entity_id
#             return brand_entity_id

#         # ⛔ RATE LIMIT
#         elif response.status_code == 429:
#             wait_time = attempt * 3  # exponential style
#             print(f"Rate limit hit. Waiting {wait_time} seconds...")
#             time.sleep(wait_time)
#             continue

#         # ❌ OTHER ERRORS
#         else:
#             raise Exception(
#                 f"Failed to fetch brands: {response.status_code} - {response.text}"
#             )

#     raise Exception("Brand API failed after maximum retries")

# ------------------ Brand Info (Name + Entity ID) ------------------

# _BRAND_ENTITY_CACHE = None


# def get_brand_entity_id(access_token, max_retries=5):
#     global _BRAND_ENTITY_CACHE

#     # ✅ agar pehle hi aa chuka hai to dobara API call nahi
#     if _BRAND_ENTITY_CACHE:
#         return _BRAND_ENTITY_CACHE

#     url = "https://advertising-api-eu.amazon.com/brands"
#     access_token = access_token.strip()

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Amazon-Advertising-API-ClientId": creds["client_id"],
#         "Amazon-Advertising-API-Scope": creds["profile_id"]
#     }

#     for attempt in range(1, max_retries + 1):
#         response = requests.get(url, headers=headers)

#         print(f"Brand API attempt {attempt}, status: {response.status_code}")

#         # ✅ SUCCESS
#         if response.status_code == 200:
#             data = response.json()

#             if not isinstance(data, list) or len(data) == 0:
#                 raise Exception("No brands found for this seller")

#             brand_entity_id = data[0]["brandEntityId"]
#             brand_name = data[0]["brandRegistryName"]

#             # ✅ cache store
#             _BRAND_ENTITY_CACHE = (brand_entity_id, brand_name)
#             return brand_entity_id, brand_name

#         # ⛔ RATE LIMIT
#         elif response.status_code == 429:
#             wait_time = attempt * 3  # exponential style
#             print(f"Rate limit hit. Waiting {wait_time} seconds...")
#             time.sleep(wait_time)
#             continue

#         # ❌ OTHER ERRORS
#         else:
#             raise Exception(
#                 f"Failed to fetch brands: {response.status_code} - {response.text}"
#             )

#     raise Exception("Brand API failed after maximum retries")

# --------------------- Payload Function --------------------------
def payload_sponsored_brand_product_collection(name, start_date, budget, brand_entity_id, goal, cost_type):
    return {
        "campaigns": [{
            "name": name,
            "startDate": start_date,
            "budget": budget,
            "budgetType": "DAILY",
            "brandEntityId": brand_entity_id,
            "goal": goal,
            "costType": cost_type,
            "state": "ENABLED"
        }]
    }



def create_campaign_sb_product_collection(creds, access_token, name, start_date, budget, brand_entity_id, goal, cost_type):
    url = "https://advertising-api-eu.amazon.com/sb/v4/campaigns"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.sbcampaignresource.v4+json",
        "Accept": "application/vnd.sbcampaignresource.v4+json"
    }
    
    # Detect landing type: PDP (ASIN), Store, or Custom URL
    # landing_type = detect_landing_type(landing_input)

    # if landing_type == "PDP":
        # Use payload for ASINs
    payload = payload_sponsored_brand_product_collection(
            name=name,
            start_date=start_date,
            budget=budget,
            brand_entity_id=brand_entity_id,  # ASIN list
            goal=goal,
            cost_type=cost_type
        )
    print("Payload:", payload)

    response = requests.post(url, headers=headers, json=payload)

    print(f"Campaign creation status: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code >= 400:
        raise Exception(f"Campaign creation failed: {response.text}")

    data = response.json()

    # ✅ Correct SB v4 response handling
    if "campaigns" in data and "success" in data["campaigns"]:
        success = data["campaigns"]["success"]
        if len(success) > 0:
            campaign_id = success[0]["campaignId"]
            print(f"✅ Campaign created with ID: {campaign_id}")
            return campaign_id

    raise Exception("Campaign created but campaignId not found in response")

# ---------------------- Create Ad Group --------------------------
def create_ad_group(creds, access_token, ad_group_name, campaign_id, state):
    url = "https://advertising-api-eu.amazon.com/sb/v4/adGroups"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.sbadgroupresource.v4+json",
        "Accept": "application/vnd.sbadgroupresource.v4+json"
    }

    payload = {"adGroups": [{"name": ad_group_name, "campaignId": campaign_id, "state": state}]}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code not in [200, 207]:
        raise Exception(f"Ad group creation failed: {response.text}")

    return response.json()["adGroups"]["success"][0]["adGroupId"]


# ---------------------- Create Product Collection Ad --------------------------
def create_sb_product_collection_ad(
    creds, access_token, ad_group_id, ad_name, asin_list, brand_logo_asset_id, custom_image_asset_id):
    """
    Creates Sponsored Brands Product Collection Ad targeting multiple products.
    """
    url = "https://advertising-api-eu.amazon.com/sb/v4/ads/productCollection"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.sbadresource.v4+json",
        "Accept": "application/vnd.sbadresource.v4+json"
    }

    payload = {
        "ads": [
            {
            "adGroupId": ad_group_id,
            "name": ad_name,
            "state": "ENABLED",

            "landingPage": {
                "pageType": "PRODUCT_LIST",
                "asins": asin_list
            },

            "creative": {
                "headline": "Check out our latest products",

                "brandName": "Skillofun",

                "asins": asin_list,

                "brandLogoAssetID": brand_logo_asset_id,

                # "brandLogoCrop": {
                # "top": 0,
                # "left": 0,
                # "width": 1200,
                # "height": 628
                # },

                "customImageAssetId": custom_image_asset_id
                # "customImageCrop": {
                # "top": 0,
                # "left": 0,
                # "width":245,
                # "height": 250
                # }
            }
            }
        ]
        }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code >= 400:
        raise Exception(f"Product Collection Ad creation failed: {response.text}")

    data = response.json()
    print("DEBUG RESPONSE:", json.dumps(data, indent=2))
    if "ads" in data and "success" in data["ads"]:
        return data["ads"]["success"][0]["adId"]
    raise Exception("Product Collection Ad created but adId not found")



# ------------------- keyword ---------------------
def create_sb_keyword(creds, access_token, campaign_id, ad_group_id, keyword_text, match_type, bid):
    url = "https://advertising-api-eu.amazon.com/sb/keywords"
    payload = [{
        "campaignId": campaign_id,
        "adGroupId": ad_group_id,
        "keywordText": keyword_text,
        "matchType": match_type,
        # "state": "ENABLED",
        "bid": bid
    }]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/vnd.sbkeywordresponse.v3+json"
    }
    response = requests.post(url, headers=headers, json=payload)
    # ✅ Accept 200, 201, 207 as valid
    if response.status_code not in [200, 201, 207]:
        raise Exception(f"Keyword creation failed: {response.text}")

    data = response.json()
    # Check each keyword for success
    for item in data:
        if item.get("code") != "SUCCESS":
            print(f"⚠️ Keyword issue: {item}")
    return data

# Get Auto keywords 
def list_sb_themes(access_token, creds, campaign_id, ad_group_id):
    url = "https://advertising-api-eu.amazon.com/sb/themes/list"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"],
        "Content-Type": "application/json",
        "Accept": "application/vnd.sbthemeslistresponse.v3+json"
    }

    payload = {
        "campaignIdFilter": {
            "include": [campaign_id]
        },
        "adGroupIdFilter": {
            "include": [ad_group_id]
        },
        "stateFilter": {
            "include": ["enabled"]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Theme list failed: {response.text}")

    data = response.json()
    return data.get("themes", [])



def pause_sb_themes(access_token, creds, themes, pause_type="paused"):
    url = "https://advertising-api-eu.amazon.com/sb/themes"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"],
        "Content-Type": "application/json",
        "Accept": "application/vnd.sbthemesupdateresponse.v3+json"
    }

    payload = {
        "themes": []
    }

    for theme in themes:
        payload["themes"].append({
            "themeId": theme["themeId"],
            "campaignId": theme["campaignId"],
            "adGroupId": theme["adGroupId"],
            "state": pause_type   # paused OR archived
        })

    response = requests.put(url, headers=headers, json=payload)
    if response.status_code not in [200, 207]:
        raise Exception(f"Theme pause failed: {response.text}")

    print(f"✅ {len(payload['themes'])} auto keyword themes {pause_type.upper()} successfully")


# ------------------ LAMBDA HANDLER ------------------
def lambda_handler(event, context):
    name = event.get("campaignName")
    video_ad_name = event.get("videoAdName")
    start_date = event.get("startDate")
    budget = event.get("budget")
    headline = event.get("headline")
    ad_group_name = event.get("adGroupName")
    ad_group_video_name = event.get("adGroupVideoName")
    video_asset_id = event.get("videoAssetIds")
    keyword_text = event.get("keywordText")
    match_type = event.get("matchType")
    bid = event.get("bid")
    goal = event.get("goal")
    cost_type = event.get("costType")
    asin_list = event.get("asins")
    state = event.get("state")
    store_url = event.get("storeUrl")
    brand_name = event.get("brandRegistryName")
    brand_logo_asset_id = event.get("brandLogoAssetId")
    custom_image_asset_id = event.get("customImageAssetId")
    brand_entity_id = event.get("brandEntityId")
    ad_name = event.get("productName")
    client_code = event.get("client_code")
    if not client_code:
        raise Exception("client_code missing in event")
    creds = load_credentials_from_s3(client_code)

    # access_token = get_access_token()
    # brand_entity_id = get_brand_entity_id(access_token)
    # print("Brand Entity ID:", brand_entity_id)
    
    # ---------- Access Token ----------
    access_token = get_access_token(creds)
    # brand_entity_id = get_brand_entity_id(access_token)
    # print("✅ Brand Entity ID:", brand_entity_id)

    # brand_entity_id, brand_name = get_brand_entity_id(access_token)
    # print("✅ Brand Entity ID:", brand_entity_id)
    # print("✅ Brand Name:", brand_name)

    # ---------- Create Campaign ----------
    campaign_id = create_campaign_sb_product_collection(creds, access_token, name, start_date, budget, brand_entity_id, goal, cost_type)    
    print(f" Campaign created: {campaign_id}")

    # ---------- Create Ad Group ----------
    ad_group_id = create_ad_group(creds, access_token, ad_group_name, campaign_id, state)
    print(f"✅ Ad group created: {ad_group_id}")

    # ---------- Create Product Collection Ad ----------
    ad_id = create_sb_product_collection_ad(creds, access_token, ad_group_id, ad_name, asin_list, brand_logo_asset_id, custom_image_asset_id)
    print(f"✅ Product Collection Ad created with ID: {ad_id}")

    # Create keyword targeting
    keyword_response = create_sb_keyword(creds, access_token, campaign_id, ad_group_id, keyword_text, match_type, bid)
    print(f" Keyword targeting response: {keyword_response}")

    import time
    time.sleep(10) 

    # 🔴 AUTO KEYWORDS BAND KARNE KA STEP
    print("🔍 Checking auto keyword themes...")
    themes = list_sb_themes(access_token, creds, campaign_id, ad_group_id)

    if themes:
        print(f"⚠️ Found {len(themes)} auto keyword theme(s). Pausing them...")
        pause_sb_themes(access_token, creds, themes, pause_type="paused")
    else:
        print("✅ No auto keyword themes found")

    return {
        "campaignId": campaign_id,
        "adGroupId": ad_group_id,
        "productCollectionId": ad_id,
        "keywordId": keyword_response,
    }
