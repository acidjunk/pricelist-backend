import json
import os
import sys

import requests
from client_examples.config import HOST

default_headers = {"content-type": "application/json"}

if not os.getenv("EMAIL") or not os.getenv("PASSWORD"):
    print("EMAIL and PASSWORD os env vars are both needed")
    sys.exit()

r = requests.post(
    HOST + "/login",
    data=json.dumps({"email": os.getenv("EMAIL"), "password": os.getenv("PASSWORD")}),
    headers=default_headers,
)

response = r.json()
token = response["response"]["user"]["authentication_token"]  # set token value
user_id = response["response"]["user"]["id"]  # set token value
print(f"Received token: {token}, user_id: {user_id}")
