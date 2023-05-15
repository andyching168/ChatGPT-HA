import requests
import json
def load_secrets():
    with open("secret.txt", "r") as f:
        secrets = f.read().splitlines()
        if len(secrets) == 3:
            return secrets
        else:
            raise ValueError("Invalid secret.txt format. Expected 3 lines.")
def call_home_assistant_control(text):
    url = HA_URL+"/api/conversation/process"
    headers = {
        "Authorization": "Bearer "+HA_APIKEY,
        "content-type": "application/json",
    }
    data = {"language": "zh-tw","text": text}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    return response.text
secrets = load_secrets()
HA_URL = secrets[0]
HA_APIKEY = secrets[1]
OpenAI_APIKEY = secrets[2]
question=input("請輸入指令:")
home_assistant_response = call_home_assistant_control(question)
print(home_assistant_response)