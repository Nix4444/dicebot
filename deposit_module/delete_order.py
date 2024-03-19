import requests
import json

def delete_sellix_order(api_key, uniqid):
    """
    Delete an order from Sellix.

    :param api_key: Your Sellix API key
    :param uniqid: The unique identifier for the order you want to delete
    :return: A tuple (success: bool, message: str)
    """
    url = f"https://dev.sellix.io/v1/payments/{uniqid}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.delete(url, headers=headers)
    stripped_string = response.text.replace('void time config', '')
    r = json.loads(stripped_string)
    if (r.get("status")) == 200:
        err_msg = "NULL"
        return True, err_msg
    else:
        err_msg = r.get("error")
        return False, err_msg
'''url = f"https://dev.sellix.io/v1/payments/fc4deb-3a9075dd36-2b7c78"
headers = {
        "Authorization": f"Bearer fnrYmOOCNNPilmJacS2J86rB38mLteBnC1WbpTcIvjbNrL1k1Va6SF7oN9EvdccL"
    }

response = requests.delete(url, headers=headers)
stripped_string = response.text.replace('void time config', '')
json_data = json.loads(stripped_string)

print(json_data.get('status'))
'''