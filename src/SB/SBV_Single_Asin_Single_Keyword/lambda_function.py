import requests
from datetime import datetime, timedelta
import os
import json
import boto3
import time

# Get Credentials from s3 from client_1
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

# if __name__ == "__main__":
#     print(get_access_token(creds))


# -------------------- Branch Id and Entity Id ----------------------------
_BRAND_ENTITY_CACHE = None


def get_brand_entity_id(access_token, creds, max_retries=5):
    global _BRAND_ENTITY_CACHE

    # ✅ agar pehle hi aa chuka hai to dobara API call nahi
    if _BRAND_ENTITY_CACHE:
        return _BRAND_ENTITY_CACHE

    url = "https://advertising-api-eu.amazon.com/brands"
    access_token = access_token.strip()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"]
    }

    for attempt in range(1, max_retries + 1):
        response = requests.get(url, headers=headers)

        print(f"Brand API attempt {attempt}, status: {response.status_code}")

        # ✅ SUCCESS
        if response.status_code == 200:
            data = response.json()

            if not isinstance(data, list) or len(data) == 0:
                raise Exception("No brands found for this seller")

            brand_entity_id = data[0]["brandEntityId"]

            # ✅ cache store
            _BRAND_ENTITY_CACHE = brand_entity_id
            return brand_entity_id

        # ⛔ RATE LIMIT
        elif response.status_code == 429:
            wait_time = attempt * 3  # exponential style
            print(f"Rate limit hit. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            continue

        # ❌ OTHER ERRORS
        else:
            raise Exception(
                f"Failed to fetch brands: {response.status_code} - {response.text}"
            )

    raise Exception("Brand API failed after maximum retries")


# --------------------- Create Campaing --------------------------------

def payload_sponsored_brands_campaign_video(name, start_date, budget, brand_entity_id, goal, cost_type):
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



def create_campaign_sb_video(access_token, creds, name, start_date, budget, brand_entity_id, goal, cost_type):
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
    payload = payload_sponsored_brands_campaign_video(
            name=name,
            start_date=start_date,
            budget=budget,
            brand_entity_id=brand_entity_id,
            # headline=headline,
            # brand_logo_asset_id=brand_logo_asset_id,
            # asin=asin,  # ASIN list
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
 
    
    # ---------------------- Create Ad_Group --------------------------
def create_ad_group(access_token, creds, ad_group_name, campaign_id, state):
    url = "https://advertising-api-eu.amazon.com/sb/v4/adGroups"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.sbadgroupresource.v4+json",
        "Accept": "application/vnd.sbadgroupresource.v4+json"
    }
        
    payload = {
        "adGroups": [
            {
                "name": ad_group_name,
                "campaignId": campaign_id,
                "state": state
            }
        ]
    }

    print("📦 Ad Group Payload:", payload)

    response = requests.post(url, headers=headers, json=payload)

    print("Ad group creation status code:", response.status_code)
    print("Response content:", response.text)

    if response.status_code not in [200, 207]:
        raise Exception(f"Ad group creation failed: {response.text}")

    data = response.json()
    ad_group_id = data["adGroups"]["success"][0]["adGroupId"]

    print("✅ Ad group created:", ad_group_id)
    return ad_group_id


    # --------------- Create sb Video -----------------
def create_sb_video_ad_asin(access_token, creds, ad_group_id, asin, video_asset_id):
    url = "https://advertising-api-eu.amazon.com/sb/v4/ads/video"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/vnd.sbadresource.v4+json"
    }

    payload = {
        "ads": [
        {
            "name": "Product Ads for Video",
            "state": "ENABLED",
            "adGroupId": ad_group_id,
            "creative": {
                # "assetType": "VIDEO",
                "asins": asin,
                # "consentToTranslate": false,
                # "videoAssetIds": ["amzn1.assetlibrary.asset1.c7cd133d2427f7434aec834bc9e91a61:version_v1"] 
                "videoAssetIds": video_asset_id
            }
        }]
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    data = response.json()

    ads_data = data.get("ads", {})
    if ads_data.get("success") and len(ads_data["success"]) > 0:
        video_ad_id = ads_data["success"][0].get("adId")
        print(f"✅ Video ad created successfully: {video_ad_id}")
        return video_ad_id
    elif ads_data.get("error") and len(ads_data["error"]) > 0:
        print("❌ Video ad creation failed with error:", ads_data["error"])
        return None
    else:
        print("❌ Video ad creation failed, unexpected response:", data)
        return None



    
# ------------------- keyword ---------------------
def create_sb_keyword(access_token, creds, campaign_id, ad_group_id, keyword_text, match_type, bid):
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
    asin = event.get("asins")
    state = event.get("state")
    store_url = event.get("storeUrl")
    brand_name = event.get("brandName")
    client_code = event.get("client_code")
    if not client_code:
        raise Exception("client_code missing in event")
    creds = load_credentials_from_s3(client_code)

    access_token = get_access_token(creds)
    brand_entity_id = get_brand_entity_id(access_token, creds)
    print("Brand Entity ID:", brand_entity_id)

    # Create Campaign
    campaign_id = create_campaign_sb_video(
            access_token, creds, name, start_date, budget,
            brand_entity_id, goal, cost_type  # Only pass ASIN for PDP
        )
    print(f" Campaign created: {campaign_id}")

    print("📦 Creating ad group...")
        # Create the ad group
    ad_group_id = create_ad_group(access_token, creds, ad_group_name, campaign_id, state)
    print(f" Ad group created: {ad_group_id}")

    # video_asset_id = get_brand_video_asset_id(access_token, brand_entity_id)

    video_ad_id = create_sb_video_ad_asin(access_token, creds, ad_group_id, asin, video_asset_id)
    print(f" Video Ad ID: {video_ad_id}")

    keyword_id = create_sb_keyword(access_token, creds, campaign_id, ad_group_id, keyword_text, match_type, bid)
    print(f" Keyword ID: {keyword_id}")

          # ⏳ Amazon ko time do keywords generate karne ka
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


    # Create keyword targeting
    # keyword_response = create_sb_keyword(access_token, campaign_id, ad_group_id, keyword_text, match_type, bid)
    # print(f" Keyword targeting response: {keyword_response}")


    return {
        "campaignId": campaign_id,
        "adGroupId": ad_group_id,
        "videoId": video_ad_id,
        "keywordId": keyword_id,
        "themesId": themes
    }
