import json
import boto3


def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----

    asin = "B009GCTZWC"
    event_payload = {
        "budget": 100,
        "videoAdName": "Toys",
        "startDate": "2026-01-29",
        "headline": "Check out our latest tech!",
        "adGroupVideoName": "SB video Ad Video",
        "keywordText": "fun",
        "matchType": "broad",
        "bid": 1.5,
        "goal": "PAGE_VISIT",
        "costType": "CPC",
        "state": "ENABLED",
        "client_code": "client_1",
        "storeUrl": "https://www.amazon.com/stores/brand/page",
        "brandName": "Toy Collection",
        "consentToTranslate": True,
        # "name": "Video Ad",
        "videoAssetIds": ["amzn1.assetlibrary.asset1.0db11e16586c5aa9f57269295d7aae37:version_v1"],
        "campaignName": f"{asin} - FaizanSBVideo1c",
        # "campaignName": "FaizanCategory1s",
        "adGroupName": "SBV Single Asin Single keyword",
        "asins": ["B009GCTZWC"]
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
    function_name = "SBV_Single_Asin_Single_Keyword"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
