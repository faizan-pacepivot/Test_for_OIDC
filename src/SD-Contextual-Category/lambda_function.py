import requests
# from datetime import datetime, timedelta
import os
# import time
import json
from dotenv import load_dotenv
# ------------------ ACCESS TOKEN ------------------
load_dotenv()


def get_access_token():
    url = "https://api.amazon.co.uk/auth/o2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": os.environ['client_id'],
        "client_secret": os.environ['client_secret'],
        "refresh_token": os.environ['refresh_token'],
        "scope": "profile",
        "profile_id": os.environ['profile_id']
    }

    r = requests.post(url, data=data)
    print("Token Status:", r.status_code)

    if r.status_code != 200:
        raise Exception("Failed to get token")

    return r.json()["access_token"]


# ------------------ CAMPAIGN ------------------
def build_Campaign_Payload_SD_Contextual_Category(name, budgetType, budget, startDate, state, tactic):
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


def create_campaign(access_token, name, budgetType, budget, startDate, state, tactic):
    url = "https://advertising-api-eu.amazon.com/sd/campaigns"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": os.environ['client_id'],
        "Amazon-Advertising-API-Scope": os.environ['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/json",
        # "x-amzn-advertising-api-version": "v3"
    }

    payload = build_Campaign_Payload_SD_Contextual_Category(
        name, budgetType, budget, startDate, state, tactic)
    print("✅ Payload:", json.dumps(payload, indent=2))

    response = requests.post(url, headers=headers, json=payload)

    print("Status:", response.status_code)
    print("RAW Response:", response.text)

    if response.status_code not in [200, 207]:
        raise Exception(response.text)

    data = response.json()
    print("Parsed JSON:", json.dumps(data, indent=2))

    # ✅ SD response handling (NEW FORMAT)
    if isinstance(data, list) and len(data) > 0:
        if data[0].get("code") == "SUCCESS":
            campaign_id = data[0]["campaignId"]
            print(f"✅ Campaign created: {campaign_id}")
            return campaign_id

    raise Exception("Campaign created but campaignId not found")


# ------------------ AD GROUP ------------------
def create_ad_group(access_token, name, cid, defaultBid, bidOptimization, state):
    url = "https://advertising-api-eu.amazon.com/sd/adGroups"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": os.environ['client_id'],
        "Amazon-Advertising-API-Scope": os.environ['profile_id'],
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
def create_product_ad(cid, agid, sku, access_token, state):
    url = "https://advertising-api-eu.amazon.com/sd/productAds"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": os.environ['client_id'],
        "Amazon-Advertising-API-Scope": os.environ['profile_id'],
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


# ------------------ GET CATEGORY ID FROM ASIN ------------------
def discover_toys_category(access_token):
    """Find Toys audience IDs automatically"""
    url = "https://advertising-api-eu.amazon.com/audiences/list"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": os.environ['client_id'],
        "Amazon-Advertising-API-Scope": os.environ['profile_id'],
        "Content-Type": "application/json"
    }
    
    payload = {
        "adType": "SD",
        "filters": [
            {"field": "category", "values": ["In-market"]},
            {"field": "audienceName", "values": ["toy", "toys", "doll", "action figure"]}
        ]
    }
    
    r = requests.post(url, headers=headers, json=payload)
    print("🔍 CATEGORY DISCOVERY:", r.status_code)

    audiences = r.json().get("audiences", [])
    category_ids = []

    for a in audiences:
        print(f"🎯 FOUND: {a['audienceId']} | {a['audienceName']}")
        category_ids.append(a["audienceId"])

    return category_ids[:3]



# -------------------- Category Targeting -----------------------------
def create_category_targeting(access_token, agid, category_id, bid, state):
    url = "https://advertising-api-eu.amazon.com/sd/targets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": os.environ['client_id'],
        "Amazon-Advertising-API-Scope": os.environ['profile_id'],
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = [{
        "adGroupId": agid,
        "expression": [{
            "type": "audience",
            "value": [{
                "type": "audienceSameAs",
                "value": category_id
            }]
        }],
        "bid": float(bid),
        "state": state,
        "expressionType": "manual"
    }]
    
    print("🎯 TOYS AUDIENCE Payload:", json.dumps(payload, indent=2))
    r = requests.post(url, headers=headers, json=payload)
    print("✅ TOYS AUDIENCE Response:", r.status_code, r.text)
    return r.json()



# ------------------ LAMBDA HANDLER ------------------
def lambda_handler(event, context):

    budget = "200.00"
    budgetType = "daily"
    startDate = "20260108"
    tactic = "T00030"
    state = "paused"
    defaultBid = 1
    bidOptimization = "clicks"
    asin = "B009GCTZWC"
    sku = "BI-CGOZ-MFIV"
    endDate = "20270108"
    portfolioId = "null"
    costType = "cpc"
    bid = 2.0
    bid_retarget = "2.0"
    bid_audience = "1.5"
    access_token = get_access_token()
    # audience_id = get_sd_audience_id(access_token)
    # if not audience_id:
    #     return {"error": "No SD audience found"}

    cid = create_campaign(access_token, "Faizan_SD_Contextual_Category2y",
                          budgetType, budget, startDate,  state, tactic)
    # print("Payload:", payload)

    agid = create_ad_group(access_token, "Lambda Ad Group 2",
                           cid, defaultBid, bidOptimization, state)
    pid = create_product_ad(cid, agid, sku, access_token, state)
    
    category_ids  = discover_toys_category(access_token)
    category_results = []    
    for catid in category_ids:
        res = create_category_targeting(access_token, agid, catid, bid, state)
        category_results.append(res)

    return {
        "campaignId": cid,
        "adGroupId": agid,
        "ProductAd": pid,
        "toysCategoryId": category_ids,
        "toysCategoryResult": category_results
    }


# ------------------ LOCAL TEST  ------------------
if __name__ == "__main__":
    print("DEBUG STARTED")
    result = lambda_handler({}, {})
    print("FINAL RESULT:", result)
# 