import json
import boto3

def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----
    
    asin = "B009GCTZWC"
    event_payload = {
        "budget": "200.00",
        "budgetType": "daily",
        "startDate": "20260125",
        "tactic": "T00020",
        "state": "enabled",
        "defaultBid": 1,
        "bidOptimization": "clicks",
        "sku": "BI-CGOZ-MFIV",
        "asin": "B009GCTZWC",
        # "endDate": "20270108",
        "portfolioId": "null",
        "costType": "cpc",
        "bid": 2.0,
        # "bid_retarget": "2.0",
        "bid_category": "1.5",
        "min_price": 100,
        "max_price": 200,
        "client_code": "client_1",
        "campaignName": f"{asin} - FaizanCategoryId2s",
        # "campaignName": "FaizanCategory1s",
        "adGroupName": "Test Ad Group Category"
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
    function_name = "SD-Contextual-Category"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
