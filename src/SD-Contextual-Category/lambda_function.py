import requests
# from datetime import datetime, timedelta
import os
# import time
import json
import boto3
# Faizan
# from dotenv import load_dotenv
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
        raise Exception(
            f"Credentials file not found for client: {client_code}")

    except Exception as e:
        raise Exception(f"S3 credential load failed: {str(e)}")
# ------------------ ACCESS TOKEN ------------------
# load_dotenv()


def get_access_token(creds):
    url = "https://api.amazon.co.uk/auth/o2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": creds['client_id'],
        "client_secret": creds['client_secret'],
        "refresh_token": creds['refresh_token'],
        "scope": "profile",
        "profile_id": creds['profile_id']
    }

    r = requests.post(url, data=data)
    print("Token Status:", r.status_code)

    if r.status_code != 200:
        raise Exception("Failed to get token")

    return r.json()["access_token"]


# --------------------- Get Category Id ---------------------------
def get_category_ids_from_asin(access_token, creds, asin):
    url = "https://advertising-api-eu.amazon.com/sd/targets/recommendations"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Accept": "application/vnd.sdtargetingrecommendations.v3.1+json",
        "Content-Type": "application/vnd.sdtargetingrecommendations.v3.1+json"
    }

    payload = {
        "tactic": "T00020",
        "products": [
            {"asin": asin}
        ],
        "typeFilter": ["CATEGORY"]
    }

    response = requests.post(url, headers=headers, json=payload)
    print("STATUS:", response.status_code)
    print("RAW RESPONSE:", response.text)

    if response.status_code not in (200, 207):
        raise Exception("Failed to get category recommendations")

    data = response.json()

    # ✅ Correct extraction of category IDs
    category_ids = []
    categories = data.get("recommendations", {}).get("categories", [])
    for rec in categories:
        if "category" in rec:
            category_ids.append(rec["category"])

    print("Extracted category IDs:", category_ids)

    if not category_ids:
        raise Exception("No category found")

    return category_ids


# # --------------------- Get Camapign Id ----------------------------

def get_campaign_id_by_name(access_token, creds, campaign_name):
    url = "https://advertising-api-eu.amazon.com/sd/campaigns"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"],
        "Accept": "application/json"
    }

    params = {
        "stateFilter": "enabled,paused"
    }

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch campaigns: {r.text}")

    campaigns = r.json()

    for camp in campaigns:
        if camp.get("name") == campaign_name:
            return camp.get("campaignId")

    return None


# ------------------ CAMPAIGN ------------------
def build_Campaign_Payload_SD_Category(name, budgetType, budget, startDate, state, tactic):
    return [{
        "name": name,
        "budgetType": budgetType,
        "budget": budget,
        "startDate": startDate,
        # "endDate": endDate,
        # "portfolioId": portfolioId,
        "costType": "cpc",
        "state": state,
        "tactic": tactic,
        # "costType": costType,
        # "tactic": "T00030"

    }]


def create_campaign(access_token, creds, name, budgetType, budget, startDate, state, tactic):
    url = "https://advertising-api-eu.amazon.com/sd/campaigns"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/json",
        # "x-amzn-advertising-api-version": "v3"
    }

    payload = build_Campaign_Payload_SD_Category(
        name, budgetType, budget, startDate, state, tactic)
    print("✅ Payload:", json.dumps(payload, indent=2))

    r = requests.post(url, headers=headers, json=payload)
    print("Create Campaign Response:", r.text)

    if r.status_code not in [200, 207]:
        raise Exception(r.text)

    # 🔥 IMPORTANT FIX
    campaign_id = get_campaign_id_by_name(access_token, creds, name)

    if not campaign_id:
        raise Exception("Campaign created but campaignId not retrievable")

    print(f"✅ Campaign ID fetched via GET: {campaign_id}")
    return campaign_id


# ------------------ AD GROUP ------------------
def create_ad_group(access_token, creds, name, cid, defaultBid, bidOptimization, state):
    url = "https://advertising-api-eu.amazon.com/sd/adGroups"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = [
        {
            "name": name,
            "campaignId": cid,
            "defaultBid": defaultBid,
            "bidOptimization": bidOptimization,
            "state": state,
        }
    ]

    r = requests.post(url, headers=headers, json=payload)

    print("Ad Group Status:", r.status_code)
    print("Ad Group Response:", r.text)

    if r.status_code >= 400:
        raise Exception(f"Ad group creation failed: {r.text}")

    data = r.json()

    # ✅ SD API RETURNS LIST
    if isinstance(data, list) and data[0].get("code") == "SUCCESS":
        ad_group_id = data[0]["adGroupId"]
        print(f"✅ Ad Group created: {ad_group_id}")
        return ad_group_id

    raise Exception("Ad Group created but adGroupId not found")


# ---------------------- Product ad ----------------------
def create_product_ad(cid, agid, sku, access_token, creds, state):
    url = "https://advertising-api-eu.amazon.com/sd/productAds"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = [
        {
            "campaignId": cid,
            "adGroupId": agid,
            # "asin": asin,
            "sku": sku,
            "state": state
        }
    ]

    r = requests.post(url, headers=headers, json=payload)

    print("Product Ad Status:", r.status_code)
    print("Product Ad Response:", r.text)

    if r.status_code >= 400:
        raise Exception(f"Product Ad failed: {r.text}")

    data = r.json()
    print("Product Ad Parsed:", json.dumps(data, indent=2))

    # ✅ SAME PATTERN jaise campaign/adgroup mein use kiya
    if isinstance(data, list) and len(data) > 0:
        if data[0].get("code") == "SUCCESS":
            product_ad_id = data[0]["adId"]
            print(f"✅ Product Ad created: {product_ad_id}")
            return product_ad_id
        else:
            raise Exception(
                f"Product Ad failed: {data[0].get('description', 'Unknown error')}")

    raise Exception("Product Ad created but adId not found")

# ---------------------Category Targeting -----------------------------


def create_sd_category_targeting(access_token, creds, ad_group_id, bid, state, category_id):
    url = "https://advertising-api-eu.amazon.com/sd/targets"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"],
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = [
        {
            "adGroupId": ad_group_id,
            "state": state,
            "bid": bid,
            "expressionType": "manual",
            "expression": [
                {
                    "type": "asinCategorySameAs",
                    "value": category_id
                }
            ]
        }
    ]

    print("🎯 SD CATEGORY TARGET PAYLOAD:", json.dumps(payload, indent=2))

    r = requests.post(url, headers=headers, json=payload)
    print("✅ SD CATEGORY TARGET RESPONSE:", r.status_code, r.text)

    return r.json()


# ------------------ LAMBDA HANDLER ------------------
def lambda_handler(event, context):
    budget = event.get("budget")
    budgetType = event.get("budgetType")
    startDate = event.get("startDate")
    tactic = event.get("tactic")
    state = event.get("state")
    defaultBid = event.get("defaultBid")
    bidOptimization = event.get("bidOptimization")
    asin = event.get("asin")
    sku = event.get("sku")
    endDate = event.get("endDate")
    portfolioId = event.get("portfolioId")
    costType = event.get("costType")
    bid = event.get("bid")
    bid_retarget = event.get("bid_retarget")
    bid_category = event.get("bid_category")
    campaign_name = event.get("campaignName")
    ad_group_name = event.get("adGroupName")
    ad_group_id = event.get("adGroupId")
    category_id = event.get("categoryId")
    category_name = event.get("categoryName")
    client_code = event.get("client_code")
    if not client_code:
        raise Exception("client_code missing in event")
    creds = load_credentials_from_s3(client_code)
    # min_price = event.get("min_price")
    # max_price = event.get("max_price")

    # budget = "200.00"
    # budgetType = "daily"
    # startDate = "20260108"
    # tactic = "T00030"
    # state = "paused"
    # defaultBid = 1
    # bidOptimization = "clicks"
    # asin = "B009GCTZWC"
    # sku = "BI-CGOZ-MFIV"
    # endDate = "20270108"
    # portfolioId = "null"
    # costType = "cpc"
    # bid = 2.0
    # bid_retarget = "2.0"
    # bid_audience = "1.5"
    access_token = get_access_token(creds)
    # audience_id = get_sd_audience_id(access_token)
    # if not audience_id:
    #     return {"error": "No SD audience found"}

    cid = create_campaign(access_token, creds, campaign_name,
                          budgetType, budget, startDate,  state, tactic)

    agid = create_ad_group(access_token, creds, campaign_name,
                           cid, defaultBid, bidOptimization, state)
    pid = create_product_ad(cid, agid, sku, access_token, creds, state)

    category_ids = get_category_ids_from_asin(access_token, creds, asin)

    if not category_ids:
        raise Exception("No category found")

    category_id = str(category_ids[0])
    print("FINAL CATEGORY ID:", category_id)

    results = create_sd_category_targeting(
        access_token, creds, agid, bid_category, state, category_id,)

    return {
        "campaignId": cid,
        "adGroupId": agid,
        "ProductAd": pid,
        "categoryIdsUsed": category_id,
        "toysCategoryResult": results
    }

# ------------------ LOCAL TEST ------------------
# if __name__ == "__main__":
#     print("DEBUG STARTED")
#     result = lambda_handler({}, {})
#     print("FINAL RESULT:", result)
