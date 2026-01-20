import json
import boto3


def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----

    asinList = ["B009GCTZWC", "B0089IOXMG", "B009GCSI8Y"]
    event_payload = {
        "budget": 100,
        "videoAdName": "Toys",
        "startDate": "2026-01-29",
        "headline": "Check out our latest tech!",
        "adGroupVideoName": "SB Product Collection",
        "keywordText": "fun",
        "matchType": "exact",
        "bid": 1.5,
        "goal": "PAGE_VISIT",
        "costType": "CPC",
        "state": "ENABLED",
        "storeUrl": "https://www.amazon.com/stores/brand/page",
        "brandName": "Toy Collection",
        "consentToTranslate": True,
        "client_code": "client_1",
        "adName": "SB Store spotlight Ad",
        # "name": "Video Ad",
        "videoAssetIds": ["amzn1.assetlibrary.asset1.0db11e16586c5aa9f57269295d7aae37:version_v1"],
        "client_code": "client_1",
        "campaignName": f"{asinList} - FaizanSB-Store-Spotlight1h",
        # "campaignName": "FaizanSB-Store-Spotlight1d",
        "adGroupName": "SBV Single Asin Single keyword",
        "asinList": ["B009GCTZWC", "B0089IOXMG", "B009GCSI8Y"],
        "brandLogoAssetId": "amzn1.assetlibrary.asset1.e4d585103a5203ee7f8721dc73d0d285:version_v1",
        "brandEntityId": "ENTITYMAKUDSW0EU3U",
        "brandRegistryName": "Skillofun",
        "customImageAssetId": "amzn1.assetlibrary.asset1.fad9e58b811891d52bc3794f85cc144f:version_v1",
        "productName": "SB Product Collection Ad",
        "homePageUrl": "https://www.amazon.in/stores/page/0E28396F-B993-4ECD-8693-7788715097D8?ingress=2&lp_context_asin=B009GCTZWC&visitId=2ecde11e-dc28-4db3-9624-a066ffdced86&store_ref=bl_ast_dp_brandLogo_sto&ref_=ast_bln",
        "subPages": 
                [
                {
                    "pageTitle": "Toy Collection",
                    "asin": "B009GCTZWC",
                    "url": "https://www.amazon.in/stores/page/A1133467-0D0E-4ADE-AD04-5D59C061A040"
                },
                {
                    "pageTitle": "Learning Toys",
                    "asin": "B0089IOXMG",
                    "url": "https://www.amazon.in/stores/page/2C8ABEB1-952A-4E3F-832F-228E8D617844"
                },
                {
                    "pageTitle": "Puzzle Toys",
                    "asin": "B009GCSI8Y",
                    "url": "https://www.amazon.in/stores/page/A8FAA4A6-C634-429C-9EA1-9645C76B2F11"
                }
                ]


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
    function_name = "SB-Single_Asin-Single-Keyword-store-Spotlight"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
