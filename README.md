# ChatGPT-HA
用python串接ChatGPT和Home Assistant，創建一隻"賽博貓娘"，  
使ChatGPT可以控制和查詢Home Assistant裝置  

---
專案所使用的python-telegram-bot為13.13
可以使用以下指令安裝:
```
pip install python-telegram-bot==13.13
```
在使用之前要在專案資料夾和telegram-bot資料夾建立secret.txt，  
專案資料夾根目錄內secret.txt格式如下:
```
Home Assistant站點URL
Home Assistant的API Key
OpenAI的API KEY
```
telegram-bot資料夾內secret.txt格式如下:
```
Home Assistant站點URL
Home Assistant的API Key
OpenAI的API KEY
Telegram的API Key
```
