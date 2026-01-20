import json
import boto3


def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----

    asins = ["B009GCTZWC", "B0089IOXMG", "B009GCSI8Y"]
    event_payload = {
        "budget": 100,
        "videoAdName": "Toys",
        "startDate": "2026-01-29",
        "headline": "Check out our latest tech!",
        "adGroupVideoName": "SB Product Collection",
        "keywordText": "fun",
        "matchType": "broad",
        "bid": 1.5,
        "goal": "PAGE_VISIT",
        "costType": "CPC",
        "state": "ENABLED",
        "storeUrl": "https://www.amazon.com/stores/brand/page",
        "brandName": "Toy Collection",
        "consentToTranslate": True,
        "client_code": "client_1",
        # "name": "Video Ad",
        "videoAssetIds": ["amzn1.assetlibrary.asset1.0db11e16586c5aa9f57269295d7aae37:version_v1"],
        "campaignName": f"{asins} - Faizan SB Product Collection2h",
        # "campaignName": "Faizan SB Product Collection1a",
        "adGroupName": "SBV Single Asin Single keyword",
        "asins": ["B009GCTZWC", "B0089IOXMG", "B009GCSI8Y"],
        "brandLogoAssetId": "amzn1.assetlibrary.asset1.e4d585103a5203ee7f8721dc73d0d285:version_v1",
        "brandEntityId": "ENTITYMAKUDSW0EU3U",
        "brandRegistryName": "Skillofun",
        "customImageAssetId": "amzn1.assetlibrary.asset1.fad9e58b811891d52bc3794f85cc144f:version_v1",
        "productName": "SB Product Collection Ad"


    }

    # ---- Create Lambda client ----
    lambda_client = boto3.client("lambda")

    # ---- Invoke Lambda ----
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event_payload).encode("utf-8")
    )

    # ---- Read Lambda Response ----
    raw_payload = response["Payload"].read().decode("utf-8")
    result = json.loads(raw_payload)

    # ---- If body is JSON string, parse it ----
    if "body" in result and isinstance(result["body"], str):
        try:
            result["body"] = json.loads(result["body"])
        except:
            pass

    return result


# ---- Run Locally ----
if __name__ == "__main__":
    function_name = "SB-Single_Asin-Single-Keyword-Prod-Collection"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
