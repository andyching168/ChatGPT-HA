# ChatGPT-HA
用python串接ChatGPT和Home Assistant，創建一隻"賽博貓娘"，  
使ChatGPT可以控制和查詢Home Assistant裝置  

---
在使用之前要在專案資料夾和telegram-bot資料夾建立secret.txt，  
專案資料夾根目錄內secret.txt格式如下:
```
Home Assistant站點URL
Home Assistant的API Key
OpenAI的API KEY
Azure的TTS的API Key
Azure的TTS的區域
```
telegram-bot資料夾內secret.txt格式如下:
```
Home Assistant站點URL
Home Assistant的API Key
OpenAI的API KEY
Azure的TTS的API Key
Azure的TTS的區域
Telegram的API Key
```
---
Azure的TTS從[這裡](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices)申請
