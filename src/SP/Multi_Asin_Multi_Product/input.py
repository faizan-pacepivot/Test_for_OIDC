import json
import boto3

def invoke_ads_api_kw(function_name):
    # ---- Lambda Event Payload (INPUT) ----
    
    asin = "B009GCTZWC"
    products = [
        {"asin": "B009GCTZWC", "sku": "BI-CGOZ-MFIV"},
        {"asin": "B0089IOXMG", "sku": "BL-DWN2-3SEL"},
        {"asin": "B009GCSI8Y", "sku": "BV-0DRT-HJYX"},
        {"asin": "B00DZL9MUU", "sku": "BX-85TD-A52M"},
        {"asin": "B009GCTHOI", "sku": "C2-4C1O-T3YJ"},
        {"asin": "B009GCR1PA", "sku": "C9-MLGL-2MUL"},
        {"asin": "B007OU5Y5K", "sku": "CA-HF92-DQ5O"},
        {"asin": "B009GCRSGC", "sku": "DF-MYL1-AB0Z"},
        {"asin": "B009GCRMGI", "sku": "DR-XM4F-S8J6"},
        {"asin": "B007OU62LU", "sku": "DV-WZTZ-LC74"}
    ]
    event_payload = {
        "budget": 100,
        "TOS_bidding": 50,
        "ROS_bidding": 30,
        "PP_bidding": 10,
        "AB_bidding": 10,
        "dynamic_bidding":"AUTO_FOR_SALES",
        "default_bid": 3.0,
        "products": products,
        "match_type": "EXACT",
        "bid": 2.0,
        "sku": "BI-CGOZ-MFIV",
        "asin": asin,
        "state": "ENABLED",
        "targetingType": "MANUAL",
        "client_code": "client_1",
        "campaignName": f"{asin} - FaizanMulti_Asin_Multi_Product",
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
    function_name = "Multi_Asin_Multi_Product"
    output = invoke_ads_api_kw(function_name)
    print(json.dumps(output, indent=2))
