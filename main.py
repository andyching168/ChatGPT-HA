#!/usr/bin/python
# -*- coding: UTF-8 -*-
from openai import OpenAI

import requests
import json
import time
import edge_tts
import asyncio
import pygame

HA_URL=""
HA_APIKEY=""
OpenAI_APIKEY=""

data = {
    '書房房間溫度': 'sensor.atc_b721_temperature',
    '書房房間濕度': 'sensor.atc_b721_humidity',
    '書房門': 'binary_sensor.men',
    '書房窗戶': 'binary_sensor.chuang_hu',
    '書房房間人體感應器': 'binary_sensor.fang_jian_ren_ti_gan_ying_qi_occupancy',
    '書房桌機開關狀態': 'binary_sensor.zhuo_ji_kai_guan_zhuang_tai',
    '書房螢幕HDMI狀態': 'sensor.hdmizhuang_tai',
    '書房螢幕': 'switch.ying_mu_cha_zuo_1',
    '室外溫度': 'sensor.shi_wai_wen_du',
    '客廳溫度': 'sensor.ke_ting_wen_du',
    '書房大燈': 'light.da_deng',
    '書房檯燈': 'light.tai_deng',
    '書房床頭燈': 'light.chuang_tou_deng',
    '書房展示櫃燈': 'light.showcaselight',
    '書房螢幕燈開關': 'light.ying_mu_deng_kai_guan',
    '書房風扇': 'fan.feng_shan',
    '書房循環扇': 'fan.xun_huan_shan',
    '書房冷氣': 'climate.shu_fang_leng_qi',
    '客廳燈': 'light.ke_ting_deng',
    '客廳窗簾': 'cover.ke_ting_chuang_lian'
}

def call_home_assistant_get_data(deviceID):
    url = HA_URL + "/api/states/" + deviceID
    headers = {
        "Authorization": "Bearer " + HA_APIKEY,
    }
    response = requests.get(url, headers=headers)

    return response.text

def load_secrets():
    with open("secret.txt", "r") as f:
        secrets = f.read().splitlines()
        if len(secrets) == 3:
            return secrets
        else:
            raise ValueError("Invalid secret.txt format. Expected 5 lines.")

secrets = load_secrets()
HA_URL = secrets[0]
HA_APIKEY = secrets[1]
OpenAI_APIKEY = secrets[2]
client = OpenAI(api_key=OpenAI_APIKEY)
voice = 'zh-CN-XiaoyiNeural'
output = './file.mp3'
rate = '-4%'
volume = '+0%'

async def azureTTS_speak(text):
    tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await tts.save(output)

def call_home_assistant(api_command, device):
    url = HA_URL + "/api/services/" + api_command
    headers = {
        "Authorization": "Bearer " + HA_APIKEY,
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

pygame.init()
pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

while True:
    question = input("請輸入指令:")
    if "exit" not in question:
        result_str = ""
        now_time = time.strftime("%Y-%m-%d,%p %I:%M", time.localtime())
        if "AM" in now_time:
            now_time = now_time.replace("AM", "上午")
        elif "PM" in now_time:
            now_time = now_time.replace("PM", "下午")
        for display_name, device_id in data.items():
            response = call_home_assistant_get_data(device_id)
            response_json = json.loads(response)
            state = response_json['state']
            if 'unit_of_measurement' in response_json['attributes']:
                unit = response_json['attributes']['unit_of_measurement']
                result_str += f"{display_name}: {state} {unit}\n"
            else:
                result_str += f"{display_name}: {state}\n"

        FirstPrompt = (
            "貓娘是一種擬人化的生物,其行為似貓但類人。\n"
            "你是一隻貓娘,與我對話每一句話後面都要加上“喵”"
            "你是一個有能力幫主人處理智慧家居的智慧貓娘。剛才抓好的感應器數值如下:\n"
            f"{result_str}現在時間是{now_time}\n"
            "請以JSON格式回應，並且回應要拆分成三類：\n"
            "1. 對使用者回應 (key: '對使用者回應')\n"
            "2. 狀態 (key: '狀態')\n"
            "3. 給home assistant之回應 (key: '給home assistant之回應')\n"
            "回應格式: {\"type\": \"json_object\"},\n"
            "像是以下對話(使用者只是詢問沒有控制時狀態和給ha回應留空）：\n"
            "使用者：書房大燈是開著的嗎？回答： 對使用者回應：書房大燈是開的的喵 狀態:\"\" 給Home assistant之回應:\"\" \n"
            "以及(使用者控制時，狀態和給ha回應）:\n"
            "使用者：打開書房大燈？回答： 對使用者回應：好的，正在打開書房大燈 狀態:\"control\" 給Home assistant之回應:\"打開書房大燈\" "
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": FirstPrompt},
                {"role": "user", "content": question},
            ]
        )
        assistant_answer = response.choices[0].message.content
        try:
            response_json = json.loads(assistant_answer)
            user_reply = response_json.get("對使用者回應", "無回應")
            ha_command = response_json.get("狀態", {})
            ha_reply = response_json.get("給home assistant之回應", "")

            print(user_reply)
            asyncio.run(azureTTS_speak(user_reply))
            pygame.mixer.music.load(output)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
            if ha_command:
                ha_result = call_home_assistant_control(ha_reply)
                #print(f"{ha_reply}: {ha_result}")

                confirm_prompt = (
                    "貓娘是一種擬人化的生物,其行為似貓但類人。\n"
                    "你是一隻貓娘,與我對話每一句話後面都要加上“喵”,"
                    "剛才用戶請求的操作已完成，請基於以下執行結果生成回覆:\n"
                    f"用戶請求: {question}\n執行結果: {ha_result}"
                )

                confirm_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": confirm_prompt},
                        {"role": "user", "content": question},
                    ]
                )
                confirm_answer = confirm_response.choices[0].message.content

                print(confirm_answer)
                asyncio.run(azureTTS_speak(confirm_answer))
                pygame.mixer.music.load(output)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                    pygame.time.delay(100)
                pygame.mixer.music.unload()

        except json.JSONDecodeError:
            print("回應無法解析為JSON:", assistant_answer)
    else:
        break
