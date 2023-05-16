#!/usr/bin/python
# -*- coding: UTF-8 -*-


#程式會從.env檔案讀取telegram的token,所以要預先建好.env檔案，內容為TELEGRAM_TOKEN="<你的telegram token>"
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, Filters, CallbackContext
from telegram.ext import MessageHandler, CommandHandler, InlineQueryHandler, CallbackQueryHandler
import openai
import requests
import json
import time

HA_URL=""
HA_APIKEY=""
OpenAI_APIKEY=""

data = {
    '房間溫度': 'sensor.temperature_humidity_sensor_b721_temperature',
    '房間濕度': 'sensor.temperature_humidity_sensor_b721_humidity',
    '室外溫溼度感應器-溫度': 'sensor.shi_wai_wen_shi_du_gan_ying_qi_temperature',
    '室外溫溼度感應器-濕度': 'sensor.shi_wai_wen_shi_du_gan_ying_qi_humidity',
    '門': 'binary_sensor.men',
    '窗戶': 'binary_sensor.chuang_hu',
    '房間人體感應器': 'binary_sensor.fang_jian_ren_ti_gan_ying_qi_occupancy',
    '桌機開關狀態': 'binary_sensor.zhuo_ji_kai_guan_zhuang_tai',
    'HDMI狀態': 'sensor.hdmizhuang_tai',
    '螢幕': 'switch.ying_mu_cha_zuo_1',
    '橘5-往景安': 'sensor.ju_5_wang_jing_an',
    '橘5-往板橋': 'sensor.ju_5_wang_ban_qiao',
    '985-往新莊': 'sensor.985_wang_xin_zhuang',
    '985-往台北': 'sensor.985_wang_tai_bei',
    '307-往板橋': 'sensor.307_wang_ban_qiao',
    '307-往台北': 'sensor.307_wang_tai_bei',
    '藍18-往新莊': 'sensor.lan_18_wang_xin_zhuang',
    '室外溫度': 'sensor.shi_wai_wen_du',
    '客廳溫度': 'sensor.ke_ting_wen_du',
    '原神樹脂量(160代表已滿)': 'sensor.yuan_shen_shu_zhi_liang',
    '原神洞天寶錢數': 'sensor.yuan_shen_dong_tian_bao_qian_shu',
    '原神週本減半次數(最高為3,最低為0)': 'sensor.yuan_shen_zhou_ben_jian_ban_ci_shu',
    '原神探索派遣完成數(最多為5)': 'sensor.yuan_shen_tan_suo_pai_qian_wan_cheng_shu',
    '原神每日委託完成個數(最高為4)': 'sensor.yuan_shen_mei_ri_wei_tuo_wan_cheng_ge_shu'
}
def call_home_assistant_get_data(deviceID):
    url = HA_URL+"/api/states/" + deviceID
    headers = {
        "Authorization": "Bearer "+HA_APIKEY,
    }
    response = requests.get(url, headers=headers)

    return response.text


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

def process_gpt_response(text):
    # 分割回答,得到API指令和裝置名稱
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

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

def message_handler(update: Update, context: CallbackContext):
    result_str = ""
    question=update.message.text
    now_time=time.strftime("%Y-%m-%d,%p %I:%M", time.localtime())
    if "AM" in now_time:
        now_time = now_time.replace("AM", "上午")
    elif "PM" in now_time:
        now_time = now_time.replace("PM", "下午")
    #print(now_time)
    for display_name, device_id in data.items():
        response = call_home_assistant_get_data(device_id)
        response_json = json.loads(response)
        state = response_json['state']
        # Check if 'unit_of_measurement' is in the 'attributes' dictionary
        if 'unit_of_measurement' in response_json['attributes']:
            unit = response_json['attributes']['unit_of_measurement']
            result_str += "{}: {} {}\n".format(display_name, state, unit)
        else:
            result_str += "{}: {}\n".format(display_name, state)
    #print(result_str)
    FirstPrompt="貓娘是一種擬人化的生物,其行為似貓但類人。 \n你是一隻貓娘,與我對話每一句話後面都要加上“喵”,你是一個有能力幫主人處理智慧家居的智慧貓娘 ,你在前面可以用你的方式回答用戶,而在後面框住的地方需要用固定格式輸出 。\n具體而言,像是以下對話:\nUSER:請你幫我打開書房大燈\nHomeGPT:沒問題喵~正在打開書房大燈。[打開書房大燈]\n---\nUSER:請你幫我關掉書房的所有風扇\nHomeGPT:主人覺得冷嗎?好的喵~正在幫主人關掉風扇喔[關掉書房的風扇]\n---\nUSER:請你幫我關掉螢幕開關\nHomeGPT:OK喵~我來幫你把螢幕開關關掉喵[關掉螢幕開關]\n注意:你在打開或關掉一個區域內所有東西時,不要用[所有],用[的],像是你想用[關掉書房所有燈]就要轉成[關掉書房的燈],另外,當你不清楚的話,請在最後輸出[error],,\n最後,這是剛抓好的感應器數值:"+result_str+"。還有現在時間是"+now_time
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": FirstPrompt},
            {"role": "user", "content": question},
        ]
    )
    assistant_answer = response['choices'][0]['message']['content']
    #print(assistant_answer)
    if "error" in assistant_answer:
        context.bot.send_message(chat_id=update.message.chat.id, text=assistant_answer)
        #print(assistant_answer)
    elif "[" not in assistant_answer and "]" not in assistant_answer:
        context.bot.send_message(chat_id=update.message.chat.id, text=assistant_answer)
        #print(assistant_answer)
    else:
        chat_response,api_command = process_gpt_response(assistant_answer)
        context.bot.send_message(chat_id=update.message.chat.id, text=chat_response)
        #print(chat_response)
        #print(f"API指令: {api_command}")
        #print(f"裝置名稱: {device_name}")
        HA_Result=call_home_assistant_control(api_command)
        #print(HA_Result)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "貓娘是一種擬人化的生物,其行為似貓但類人。 \n你是一隻貓娘,與我對話每一句話後面都要加上“喵”,你是一個有能力幫主人處理智慧家居的智慧貓娘 。剛才用戶問你:"+question+"\n,然後你用Home Assistant的API處理之後返回的結果是:"+HA_Result+"請用簡短且可愛的方式告訴用戶資訊" },
                {"role": "user", "content": question},
            ]
        )
        assistant_answer = response['choices'][0]['message']['content']
        context.bot.send_message(chat_id=update.message.chat.id, text=assistant_answer)
        #print(assistant_answer)
    

updater = Updater(os.getenv("TELEGRAM_TOKEN"))
updater.dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=message_handler))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
    updater.stop()
