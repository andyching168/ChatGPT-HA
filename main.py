import openai
import requests
import json
HA_URL=""
HA_APIKEY=""
OpenAI_APIKEY=""
devices = {
    "書房大燈": "light.da_deng",
    "客廳大燈": "light.ke_ting_da_deng",
    "展示櫃燈": "light.showcaselight",
    "床頭燈": "light.chuang_tou_deng",
    "檯燈": "light.tai_deng",
    "紅外線小燈": "light.ir_light",
    "螢幕燈開關": "light.ying_mu_deng_kai_guan",
    "進風扇": "fan.jin_feng_shan",
    "螢幕開關": "switch.ying_mu_cha_zuo_1"
    # 加入其他裝置...
}

def load_secrets():
    with open("secret.txt", "r") as f:
        secrets = f.read().splitlines()
        if len(secrets) == 3:
            return secrets
        else:
            raise ValueError("Invalid secret.txt format. Expected 3 lines.")

secrets = load_secrets()
HA_URL = secrets[0]
HA_APIKEY = secrets[1]
OpenAI_APIKEY = secrets[2]
openai.api_key = OpenAI_APIKEY

def get_device_id(device_name):
    return devices.get(device_name)

openai.api_key = OpenAI_APIKEY


def process_gpt_response(text):
    # 分割回答，得到API指令和裝置名稱
    api_command, device_name = text.strip().split("][")
    api_command = api_command.split("[")
    Chat_Response = api_command[0]
    device_name = device_name.split("]")

    return Chat_Response,api_command[1], device_name[0]
def call_home_assistant(api_command,device):
    url = HA_URL+"/api/services/" + api_command
    headers = {
        "Authorization": "Bearer "+HA_APIKEY,
        "content-type": "application/json",
    }
    data = {"entity_id": device}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    return response.text
def call_home_assistant_control(text):
    url = HA_URL+"/api/conversation/process"
    headers = {
        "Authorization": "Bearer "+HA_APIKEY,
        "content-type": "application/json",
    }
    data = {"language": "zh-tw","text": text}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    return response.text
while(1):
  question=input("請輸入指令:")
  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
          {"role": "system", "content": "現在你是一個可以用指令控制我家裡開關和燈的GPT，叫你HomeGPT好了。具體而言，像是以下對話:\nUSER:請你幫我打開大燈\nHomeGPT:沒問題，正在打開大燈。[light/turn_on][大燈]\n---\nUSER:請你幫我關掉風扇\nHomeGPT:沒問題，正在關掉風扇。[fan/turn_off][風扇]\n---\nUSER:請你幫我關掉螢幕開關\nHomeGPT:沒問題，正在關掉螢幕開關。[switch/turn_off][螢幕開關]"},
          {"role": "user", "content": question},
      ]
  )
  assistant_answer = response['choices'][0]['message']['content']

  chat_response,api_command, device_name = process_gpt_response(assistant_answer)
  print(chat_response)
  #print(f"API指令: {api_command}")
  #print(f"裝置名稱: {device_name}")


  device_id=get_device_id(device_name)
  api_command
  home_assistant_response = call_home_assistant(api_command,device_id)

  #待實作:控制多個裝置，預計是讓ChatGPT產生多組請求，再用Python判斷是單次請求還是多次請求
  #單次:沒問題，正在關掉大燈。[Single][1][light/turn_off][大燈]
  #多次:沒問題，正在關掉大燈和風扇。[Multi][2][light/turn_off][大燈][fan/turn_off][風扇]