import json
from get_data import get_result


def lambda_handler(event, context):
    return {"statusCode": 200, "body": json.dumps(get_result())}
