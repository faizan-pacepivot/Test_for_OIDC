import json
import boto3

def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----
    
    asin = "B009GCTZWC"
    SKUS = [
        "BI-CGOZ-MFIV",
        "BL-DWN2-3SEL",
        "BV-0DRT-HJYX",
        "BX-85TD-A52M",
        "C2-4C1O-T3YJ",
        "C9-MLGL-2MUL",
        "CA-HF92-DQ5O",
        "DF-MYL1-AB0Z",
        "DR-XM4F-S8J6",
        "DV-WZTZ-LC74"
    ]
    # keyword_text = "kids"
    event_payload = {
        "budget": 100,
        "TOS_bidding": 50,
        "ROS_bidding": 30,
        "PP_bidding": 10,
        "AB_bidding": 10,
        "dynamic_bidding":"AUTO_FOR_SALES",
        "default_bid": 3.0,
        "client_code": "client_1",
        # "keyword_text": keyword_text,
        "match_type": "EXACT",
        "bid": 2.0,
        # "sku": "BI-CGOZ-MFIV",
        "SKUS": SKUS,
        "asin": asin,
        "state": "ENABLED",
        "targetingType": "MANUAL",
        "campaignName": f"{asin} - FaizanMultiProduct1g",
        "adGroupName": "Test Ad Group Audience"
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
    function_name = "Single_Asin_Multi_Product"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
