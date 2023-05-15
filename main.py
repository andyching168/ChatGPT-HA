#!/usr/bin/python
# -*- coding: UTF-8 -*-
import openai
import requests
import json
HA_URL=""
HA_APIKEY=""
OpenAI_APIKEY=""


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
    api_command, device_name = text.split("]")
    api_command = api_command.split("[")
    Chat_Response = api_command[0]

    return Chat_Response,api_command[1]
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
          {"role": "system", "content": "現在你是一個可以用指令控制我家裡開關和燈的GPT，叫你HomeGPT好了。你有可能接收到用戶的各種自然語言指令 ，而你在前面可以用你的方式回答用戶，而在後面框住的地方需要用固定格式輸出 。具體而言，像是以下對話:\nUSER:請你幫我打開書房大燈\nHomeGPT:沒問題，正在打開書房大燈。[打開書房大燈]\n---\nUSER:請你幫我關掉書房的所有風扇\nHomeGPT:沒問題，正在關掉風扇。[關掉書房的風扇]\n---\nUSER:請你幫我關掉螢幕開關\nHomeGPT:沒問題，正在關掉螢幕開關。[關掉螢幕開關]\n注意:在打開或關掉一個區域內所有東西時，不要用[所有]，用[的]，像是你想用[關掉書房所有燈]就要轉成[關掉書房的燈]，另外，當你不清楚的話，請在最後輸出[error]"},
          {"role": "user", "content": question},
      ]
  )
  assistant_answer = response['choices'][0]['message']['content']
  #print(assistant_answer)
  if "error" in assistant_answer:
    print("ChatGPT Error")
  else:
    chat_response,api_command = process_gpt_response(assistant_answer)
    print(chat_response)
    #print(f"API指令: {api_command}")
    #print(f"裝置名稱: {device_name}")
    HA_Result=call_home_assistant_control(api_command)
    #print(HA_Result)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
              {"role": "system", "content": "現在你是一個可以用指令控制我家裡開關和燈的GPT，叫你HomeGPT好了。剛才用戶問你:"+question+"\n，然後你用Home Assistant的API處理之後返回的結果是:"+HA_Result+"請用簡短的方式告訴用戶資訊"},
              {"role": "user", "content": question},
          ]
    )
    assistant_answer = response['choices'][0]['message']['content']
    print(assistant_answer)