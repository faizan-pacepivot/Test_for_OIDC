import requests
from datetime import datetime, timedelta
import os
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


# ------------------ KEYWORD ------------------
def create_keyword(access_token, creds, campaign_id, ad_group_id, keywords):
    """
    keywords = [
        {"text": "kids toy", "match_type": "EXACT", "bid": 2.0},
        {"text": "children toy", "match_type": "EXACT", "bid": 2.0},
        {"text": "baby toy", "match_type": "EXACT", "bid": 2.0}
    ]
    """
    url = "https://advertising-api-eu.amazon.com/sp/keywords"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": creds['client_id'],
        "Amazon-Advertising-API-Scope": creds['profile_id'],
        "Content-Type": "application/vnd.spKeyword.v3+json",
        "Accept": "application/vnd.spKeyword.v3+json"
    }

    payload = {
        "keywords": []
    }

    for kw in keywords:
        payload["keywords"].append({
            "campaignId": campaign_id,
            "adGroupId": ad_group_id,
            "keywordText": kw["text"],
            "matchType": kw["match_type"],
            "bid": kw["bid"],
            "state": "ENABLED"
        })

    r = requests.post(url, headers=headers, json=payload)
    print("Keyword Status:", r.status_code)
    print("Keyword Response:", r.text)

    return [
        k["keywordId"]
        for k in r.json()["keywords"]["success"]
    ]


# ------------------ PRODUCT AD ------------------
def create_product_ad(campaign_id, ad_group_id, access_token, creds, products):
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
                "asin": p["asin"],
                "sku": p["sku"],
                "state": "ENABLED"
            } for p in products
        ]
    }

    r = requests.post(url, headers=headers, json=payload)
    return [p["adId"] for p in r.json()["productAds"]["success"]]


# ------------------ LAMBDA HANDLER ------------------
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
    keywords = event.get("keywords")
    products = event.get("products")
    campaign_name = event.get("campaignName")
    ad_group_name = event.get("adGroupName")
    client_code = event.get("client_code")
    if not client_code:
        raise Exception("client_code missing in event")
    creds = load_credentials_from_s3(client_code)
    # budget = 100

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

    # keywords = [
    #     {"text": "kids toy", "match_type": "EXACT", "bid": 2.0},
    #     {"text": "children toy", "match_type": "EXACT", "bid": 2.0},
    #     {"text": "baby toy", "match_type": "EXACT", "bid": 2.0}
    # ]

    # products = [
    #     {"asin": "B00792NTR8", "sku": "0A-SLD7-P9Y1"},
    #     {"asin": "B007OUBIDC", "sku": "0B-S5LI-HUN6"},
    #     {"asin": "B009GCTRCU", "sku": "0L-Z03K-YKYE"}
    # ]

    cid = create_campaign(campaign_name, budget, access_token, creds, dynamic_bidding, TOS_bidding, ROS_bidding, PP_bidding, AB_bidding, targetingType, state)
    # print("Payload:", payload)
    # print("TOS_bidding:", TOS_bidding)
    agid = create_ad_group(cid, ad_group_name, default_bid, access_token, creds, state)
    # kid = create_keyword(access_token, cid, agid, keyword_text, match_type, bid)
    kid = create_keyword(access_token, creds, cid, agid, keywords)
    pid = create_product_ad(cid, agid, access_token, creds, products)

    return {
        "campaignId": cid,
        "adGroupId": agid,
        "keywordId": kid,
        "productAdId": pid
    }


# ------------------ LOCAL TEST ------------------
# if __name__ == "__main__":
#     print("DEBUG STARTED")
#     result = lambda_handler({}, {})
#     print("FINAL RESULT:", result)
