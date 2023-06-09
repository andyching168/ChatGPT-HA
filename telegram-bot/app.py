#!/usr/bin/python
# -*- coding: UTF-8 -*-



import os
import logging
from dotenv import load_dotenv
from telegram import Update,InputFile
from telegram.ext import Updater, Filters, CallbackContext
from telegram.ext import MessageHandler, CommandHandler, InlineQueryHandler, CallbackQueryHandler
import openai
import requests
import json
import time
import azure.cognitiveservices.speech as speechsdk

HA_URL=""
HA_APIKEY=""
OpenAI_APIKEY=""

data = {
    '書房房間溫度': 'sensor.temperature_humidity_sensor_b721_temperature',
    '書房房間濕度': 'sensor.temperature_humidity_sensor_b721_humidity',
    '室外溫溼度感應器-溫度': 'sensor.shi_wai_wen_shi_du_gan_ying_qi_temperature',
    '室外溫溼度感應器-濕度': 'sensor.shi_wai_wen_shi_du_gan_ying_qi_humidity',
    '書房門(off為關上，on為開著)': 'binary_sensor.men',
    '書房窗戶(off為關上，on為開著)': 'binary_sensor.chuang_hu',
    '書房房間人體感應器(off為沒人，on為有人)': 'binary_sensor.fang_jian_ren_ti_gan_ying_qi_occupancy',
    '書房桌機開關狀態': 'binary_sensor.zhuo_ji_kai_guan_zhuang_tai',
    '書房螢幕HDMI訊號源': 'sensor.hdmizhuang_tai',
    '書房螢幕': 'switch.ying_mu_cha_zuo_1',
    '橘5往景安(-1分是末班已過)': 'sensor.ju_5_wang_jing_an',
    '橘5往板橋(-1分是末班已過)': 'sensor.ju_5_wang_ban_qiao',
    '985往新莊(-1分是末班已過)': 'sensor.985_wang_xin_zhuang',
    '985往台北(-1分是末班已過)': 'sensor.985_wang_tai_bei',
    '307往板橋(-1分是末班已過)': 'sensor.307_wang_ban_qiao',
    '307往台北(-1分是末班已過)': 'sensor.307_wang_tai_bei',
    '藍18往新莊(-1分是末班已過)': 'sensor.lan_18_wang_xin_zhuang',
    '室外溫度': 'sensor.shi_wai_wen_du',
    '客廳溫度': 'sensor.ke_ting_wen_du',
    '原神樹脂量(160代表已滿)': 'sensor.yuan_shen_shu_zhi_liang',
    '原神洞天寶錢數': 'sensor.yuan_shen_dong_tian_bao_qian_shu',
    '原神週本減半次數(最高為3,最低為0)': 'sensor.yuan_shen_zhou_ben_jian_ban_ci_shu',
    '原神探索派遣完成數(最多為5)': 'sensor.yuan_shen_tan_suo_pai_qian_wan_cheng_shu',
    '原神每日委託完成個數(最高為4)': 'sensor.yuan_shen_mei_ri_wei_tuo_wan_cheng_ge_shu',
    '書房大燈': 'light.da_deng',
    '書房檯燈': 'light.tai_deng',
    '書房床頭燈': 'light.chuang_tou_deng',
    '書房展示櫃燈': 'light.showcaselight',
    '書房紅外線小燈': 'light.ir_light',
    '書房螢幕燈開關': 'light.ying_mu_deng_kai_guan',
    '書房風扇': 'fan.feng_shan',
    '書房循環風扇': 'fan.xun_huan_feng_shan',
    '書房循環扇': 'fan.xun_huan_shan',
    '書房冷氣': 'climate.shu_fang_leng_qi',
    '書房進風扇': 'fan.jin_feng_shan',
    '客廳燈': 'light.ke_ting_deng',
    '客廳窗簾': 'cover.ke_ting_chuang_lian'
}
def call_home_assistant_get_data(deviceID):
    url = HA_URL+"/api/states/" + deviceID
    headers = {
        "Authorization": "Bearer "+HA_APIKEY,
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Exception occurred", exc_info=True)
        return None

    return response.text


def load_secrets():
    with open("secret.txt", "r") as f:
        secrets = f.read().splitlines()
        if len(secrets) == 6:
            return secrets
        else:
            raise ValueError("Invalid secret.txt format. Expected 6 lines.")
secrets = load_secrets()
HA_URL = secrets[0]
HA_APIKEY = secrets[1]
OpenAI_APIKEY = secrets[2]
AzureTTS_KEY=secrets[3]
AzureTTS_REGION=secrets[4]
TELEGRAM_TOKEN=secrets[5]
openai.api_key = OpenAI_APIKEY

speech_config = speechsdk.SpeechConfig(subscription=AzureTTS_KEY, region=AzureTTS_REGION)
audio_config = speechsdk.audio.AudioOutputConfig(filename="./file.wav")
speech_config.speech_synthesis_voice_name='zh-CN-XiaoyiNeural'


def azureTTS_speak(text):
    #os.remove("file.wav")
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
    del speech_synthesizer


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
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Exception occurred", exc_info=True)
        return None

    return response.text

def call_home_assistant_control(text):
    url = HA_URL+"/api/conversation/process"
    headers = {
        "Authorization": "Bearer "+HA_APIKEY,
        "content-type": "application/json",
    }
    data = {"language": "zh-tw","text": text}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Exception occurred", exc_info=True)
        return None

    return response.text
# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

def message_handler(update: Update, context: CallbackContext):
    try:
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
            azureTTS_speak(assistant_answer)
            context.bot.send_message(chat_id=update.message.chat.id, text=assistant_answer)
            voice_file = open('./file.wav', 'rb')
            voice = InputFile(voice_file)
            context.bot.send_voice(chat_id=update.message.chat.id, voice=voice)
            voice_file.close()
            os.remove("file.wav")
            #print(assistant_answer)
        elif "[" not in assistant_answer and "]" not in assistant_answer:
            azureTTS_speak(assistant_answer)
            context.bot.send_message(chat_id=update.message.chat.id, text=assistant_answer)
            voice_file = open('./file.wav', 'rb')
            voice = InputFile(voice_file)
            context.bot.send_voice(chat_id=update.message.chat.id, voice=voice)
            voice_file.close()
            os.remove("file.wav")
            #print(assistant_answer)
        else:
            chat_response,api_command = process_gpt_response(assistant_answer)
            azureTTS_speak(chat_response)
            voice_file = open('./file.wav', 'rb')
            voice = InputFile(voice_file)
            context.bot.send_message(chat_id=update.message.chat.id, text=chat_response)
            context.bot.send_voice(chat_id=update.message.chat.id, voice=voice)
            voice_file.close()
            os.remove("file.wav")
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
            azureTTS_speak(assistant_answer)
            context.bot.send_message(chat_id=update.message.chat.id, text=assistant_answer)
            voice_file = open('./file.wav', 'rb')
            voice = InputFile(voice_file)
            context.bot.send_voice(chat_id=update.message.chat.id, voice=voice)
            voice_file.close()
            os.remove("file.wav")
            #print(assistant_answer)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
    

updater = Updater(TELEGRAM_TOKEN)
updater.dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=message_handler))

if __name__ == "__main__":
    try:
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
    finally:
        updater.stop()
