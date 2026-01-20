import requests
from datetime import datetime, timedelta
import os
import boto3
import json
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
        raise Exception(f"Credentials file not found for client: {client_code}")

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


# ------------------ CAMPAIGN ------------------
def build_manual_campaign_payload(name, budget, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding, targetingType, state):
    return {
        "campaigns": [
            {
                "name": name,
                "campaignType": "SPONSORED_PRODUCTS",
                "targetingType": targetingType,
                "state": state,
                "startDate": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),

                # 🔹 Dynamic Bidding
                "dynamicBidding": {
                    "placementBidding": [
                    {
                        "percentage": TOS_bidding,
                        "placement": "PLACEMENT_TOP"
                    },
                    {
                        "percentage": ROS_bidding,
                        "placement": "PLACEMENT_REST_OF_SEARCH"
                    },
                    {
                        "percentage": PP_bidding,
                        "placement": "PLACEMENT_PRODUCT_PAGE"
                    },
                    {
                        "percentage": AB_bidding,
                        "placement": "SITE_AMAZON_BUSINESS"
                    },

                    ],
                    "strategy": dynamic_bidding
                },              
                "budget": {
                    "budgetType": "DAILY",
                    "budget": budget
                }
            }
        ]
    }


def create_campaign(name, budget, access_token, creds, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding, targetingType, state):
    url = "https://advertising-api-eu.amazon.com/sp/campaigns"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.spCampaign.v3+json",
        "Accept": "application/vnd.spCampaign.v3+json"
    }

    payload = build_manual_campaign_payload(name, budget, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding, targetingType, state)
    # print("Payload:", payload)
    r = requests.post(url, headers=headers, json=payload)
    print("Campaign Status:", r.status_code)
    print("Response:", r.text)

    data = r.json()
    return data["campaigns"]["success"][0]["campaignId"]


# ------------------ AD GROUP ------------------
def create_ad_group(campaign_id, name, default_bid, access_token, creds, state):
    url = "https://advertising-api-eu.amazon.com/sp/adGroups"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.spAdGroup.v3+json",
        "Accept": "application/vnd.spAdGroup.v3+json"
    }

    payload = {
        "adGroups": [
            {
                "name": name,
                "campaignId": campaign_id,
                "defaultBid": default_bid,
                "state": state
            }
        ]
    }

    r = requests.post(url, headers=headers, json=payload)
    data = r.json()
    return data["adGroups"]["success"][0]["adGroupId"]


# ------------------ PRODUCT AD (SAFE) ------------------
def create_product_ad(campaign_id, ad_group_id, asin, sku, access_token, creds):
    url = "https://advertising-api-eu.amazon.com/sp/productAds"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"],
        "Content-Type": "application/vnd.spProductAd.v3+json",
        "Accept": "application/vnd.spProductAd.v3+json"
    }

    payload = {
        "productAds": [{
            "campaignId": campaign_id,
            "adGroupId": ad_group_id,
            "asin": asin,
            "sku": sku,
            "state": "ENABLED"
        }]
    }

    r = requests.post(url, headers=headers, json=payload)
    data = r.json()

    print(f"ProductAd Response for SKU {sku}:", data)

    if data.get("productAds", {}).get("success"):
        return data["productAds"]["success"][0]["adId"]

    print(f"❌ ProductAd failed / duplicate SKU: {sku}")
    return None


# ------------------ PRODUCT TARGET ------------------
def create_product_target(access_token, creds, campaign_id, ad_group_id, target_asin, bid):
    url = "https://advertising-api-eu.amazon.com/sp/targets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds["client_id"],
        "Amazon-Advertising-API-Scope": creds["profile_id"],
        "Content-Type": "application/vnd.spTargetingClause.v3+json",
        "Accept": "application/vnd.spTargetingClause.v3+json"
    }

    payload = {
        "targetingClauses": [{
            "campaignId": campaign_id,
            "adGroupId": ad_group_id,
            "state": "ENABLED",
            "bid": bid,
            "expressionType": "MANUAL",
            "expression": [{"type": "ASIN_SAME_AS", "value": target_asin}]
        }]
    }

    r = requests.post(url, headers=headers, json=payload)
    data = r.json()

    if data.get("targetingClauses", {}).get("success"):
        return data["targetingClauses"]["success"][0]["targetId"]

    print("❌ Product Target failed")
    return None


# ------------------ MAIN HANDLER ------------------
def lambda_handler(event, context):

    budget = event.get("budget")
    TOS_bidding = event.get("TOS_bidding")
    ROS_bidding = event.get("ROS_bidding")
    PP_bidding = event.get("PP_bidding")
    AB_bidding = event.get("AB_bidding")
    dynamic_bidding = event.get("dynamic_bidding")
    default_bid = event.get("default_bid")
    # keyword_text = event.get("keyword_text")
    # match_type = event.get("match_type")
    bid = event.get("bid")
    SKUS = event.get("SKUS")
    asin = event.get("asin")
    targetingType = event.get("targetingType")
    state = event.get("state")
    campaign_name = event.get("campaignName")
    ad_group_name = event.get("adGroupName")
    products = event.get("products")
    client_code = event.get("client_code")
    if not client_code:
        raise Exception("client_code missing in event")
    creds = load_credentials_from_s3(client_code)

    access_token = get_access_token(creds)

    cid = create_campaign(campaign_name, budget, access_token, creds, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding, targetingType, state)
    # print("Payload:", payload)
    # print("TOS_bidding:", TOS_bidding)
    agid = create_ad_group(cid, ad_group_name, default_bid, access_token, creds, state)

    # asin = "B009GCTZWC"

    # products = [
    #     {"asin": "B009GCTZWC", "sku": "BI-CGOZ-MFIV"},
    #     {"asin": "B0089IOXMG", "sku": "BL-DWN2-3SEL"},
    #     {"asin": "B009GCSI8Y", "sku": "BV-0DRT-HJYX"},
    #     {"asin": "B00DZL9MUU", "sku": "BX-85TD-A52M"},
    #     {"asin": "B009GCTHOI", "sku": "C2-4C1O-T3YJ"},
    #     {"asin": "B009GCR1PA", "sku": "C9-MLGL-2MUL"},
    #     {"asin": "B007OU5Y5K", "sku": "CA-HF92-DQ5O"},
    #     {"asin": "B009GCRSGC", "sku": "DF-MYL1-AB0Z"},
    #     {"asin": "B009GCRMGI", "sku": "DR-XM4F-S8J6"},
    #     {"asin": "B007OU62LU", "sku": "DV-WZTZ-LC74"}
    # ]

    product_ads = []
    product_targets = []

    for p in products:
        pid = create_product_ad(cid, agid, p["asin"], p["sku"], access_token, creds)
        if pid:
            product_ads.append(pid)
        # Create a product target for each ASIN
        tid = create_product_target(access_token, creds, cid, agid, p["asin"], 2.0)
        if tid:
            product_targets.append(tid)

    return {
        "campaignId": cid,
        "adGroupId": agid,
        "productAdsCreated": product_ads,
        "productTargetId": product_targets
    }


# ------------------ LOCAL TEST ------------------
# if __name__ == "__main__":
#     print("DEBUG STARTED")
#     result = lambda_handler({}, {})
#     print("FINAL RESULT:", result)
