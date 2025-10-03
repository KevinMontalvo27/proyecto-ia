import requests, certifi

response = requests.get("https://huggingface.co", verify=certifi.where())
print("Status:", response.status_code)
