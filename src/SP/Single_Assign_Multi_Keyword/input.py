import json
import boto3

def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----
    
    asin = "B009GCTZWC"
    keywords = [
        {"text": "kids toy", "match_type": "EXACT", "bid": 2.0},
        {"text": "children toy", "match_type": "EXACT", "bid": 2.0},
        {"text": "baby toy", "match_type": "EXACT", "bid": 2.0}
    ]
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
        # "match_type": "EXACT",
        # "bid": 2.0,
        "keywords": keywords,
        "sku": "BI-CGOZ-MFIV",
        "asin": asin,
        "state": "ENABLED",
        "targetingType": "MANUAL",
        "campaignName": f"{asin} - Faizan18",
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
    function_name = "Single_Assign_Multi_Keyword"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
