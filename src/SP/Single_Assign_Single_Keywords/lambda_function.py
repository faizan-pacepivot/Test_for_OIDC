import requests
from datetime import datetime, timedelta
# import os
import json
import boto3
# Faizan
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
def build_manual_campaign_payload(name, budget, state, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding):
    return {
        "campaigns": [
            {
                "name": name,
                "campaignType": "SPONSORED_PRODUCTS",
                "targetingType": "MANUAL",
                "state": state,
                "startDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),

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


def create_campaign(name, budget, state, creds, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding):
    url = "https://advertising-api-eu.amazon.com/sp/campaigns"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.spCampaign.v3+json",
        "Accept": "application/vnd.spCampaign.v3+json"
    }

    payload = build_manual_campaign_payload(name, budget, state, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding)
    print("Payload:", payload)
    r = requests.post(url, headers=headers, json=payload)
    print("Campaign Status:", r.status_code)
    print("Response:", r.text)

    data = r.json()
    return data["campaigns"]["success"][0]["campaignId"]


# ------------------ AD GROUP ------------------
def create_ad_group(campaign_id, name, default_bid, creds, state):
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


# ------------------ KEYWORD ------------------
def create_keyword(access_token, creds, campaign_id, ad_group_id, keyword_text, match_type, bid, state):
    url = "https://advertising-api-eu.amazon.com/sp/keywords"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.spKeyword.v3+json",
        "Accept": "application/vnd.spKeyword.v3+json"
    }

    payload = {
        "keywords": [
            {
                "campaignId": campaign_id,
                "adGroupId": ad_group_id,
                "keywordText": keyword_text,
                "matchType": match_type,
                "bid": bid,
                "state": state
            }
        ]
    }

    r = requests.post(url, headers=headers, json=payload)
    return r.json()["keywords"]["success"][0]["keywordId"]


# ------------------ PRODUCT AD ------------------
def create_product_ad(campaign_id, ad_group_id, asin, sku, creds, state):
    url = "https://advertising-api-eu.amazon.com/sp/productAds"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.spProductAd.v3+json",
        "Accept": "application/vnd.spProductAd.v3+json"
    }

    payload = {
        "productAds": [
            {
                "campaignId": campaign_id,
                "adGroupId": ad_group_id,
                "asin": asin,
                "sku": sku,
                "state": state
            }
        ]
    }

    r = requests.post(url, headers=headers, json=payload)

    print("Product Ad Status:", r.status_code)
    print("Product Ad Response:", r.text)

    res = r.json()

    # ✅ SUCCESS CASE
    if (
        res.get("productAds") and
        res["productAds"].get("success") and
        len(res["productAds"]["success"]) > 0
    ):
        return res["productAds"]["success"][0]["adId"]

    # ❌ ERROR CASE
    if res.get("productAds", {}).get("error"):
        raise Exception(f"Product Ad Error: {res['productAds']['error']}")

    raise Exception("Product Ad creation failed: Unknown error")


# ------------------ LAMBDA HANDLER ------------------
def lambda_handler(event, context):

    budget = event.get("budget")
    TOS_bidding = event.get("TOS_bidding")
    ROS_bidding = event.get("ROS_bidding")
    PP_bidding = event.get("PP_bidding")
    AB_bidding = event.get("AB_bidding")
    dynamic_bidding = event.get("dynamic_bidding")
    default_bid = event.get("default_bid")
    keyword_text = event.get("keyword_text")
    match_type = event.get("match_type")
    bid = event.get("bid")
    sku = event.get("sku")
    asin = event.get("asin")
    state = event.get("state")
    campaign_name = event.get("campaignName")
    ad_group_name = event.get("adGroupName")
    client_code = event.get("client_code")
    if not client_code:
        raise Exception("client_code missing in event")

    creds = load_credentials_from_s3(client_code)

    # 🔹 Placement Bidding
    # TOS_bidding = 50
    # ROS_bidding = 30
    # PP_bidding = 10
    # AB_bidding = 10
    # dynamic_bidding = "AUTO_FOR_SALES"
    # default_bid = 3.0
    # keyword_text = "kids toy"
    # match_type = "EXACT"
    # bid = 2.0
    # sku = "EC-0IZA-WFCV"
    # asin = "B00DZL9HZU"
    access_token = get_access_token(creds)

    cid = create_campaign(campaign_name, budget, state, access_token, creds, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding)
    # print("Payload:", payload)
    print("TOS_bidding:", TOS_bidding)
    agid = create_ad_group(cid, ad_group_name, default_bid, access_token, creds, state)
    kid = create_keyword(access_token, creds, cid, agid, keyword_text, match_type, bid, state)
    pid = create_product_ad(cid, agid, asin, sku, access_token, creds, state)

    return {
        "campaignId": cid,
        "adGroupId": agid,
        "keywordId": kid,
        "productAdId": pid
    }
