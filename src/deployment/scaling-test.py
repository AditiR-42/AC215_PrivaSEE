import requests

# Endpoint for your API
ENDPOINT = "http://34.138.235.192.sslip.io/recommend"

# Number of requests to send
REQUESTS = 200

# Query payload
QUERY = {"query": "I want an app like Facebook"}

def send_request():
    """Send a POST request to the API with the query."""
    try:
        response = requests.post(ENDPOINT, json=QUERY)
        print(f"Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

# Send multiple requests in a loop
for i in range(REQUESTS):
    print(f"Sending request {i + 1}/{REQUESTS}")
    send_request()

print(f"Sent {REQUESTS} requests to {ENDPOINT}")
