#!/usr/bin/env python

import urllib
import json
import os
import pandas as pd
import datetime
import pymongo
from pymongo import MongoClient
import random
import re

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)
uri = "mongodb://Fantasylin:A1598753@ds151463.mlab.com:51463/english_bang"

# datetime物件轉成 20181016 這種字串
def to_string(date):
    return date.strftime("%Y%m%d")

@app.route("/", methods=['GET'])
def hello():
    return "Hello World!"

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeWebhookResult(req):
    global collection
    # mongodb連線。 client是伺服器, english_bang是資料庫名稱, Test是collection名稱
    client = MongoClient(uri)
    db = client.english_bang
    collection = db.Test

    # askweather的地方是Dialogflow>Intent>Action 取名的內容
    fulfillmentText2=''
    fulfillmentText3=''
    if req.get("queryResult").get("action") == "recommend":
        date_parameter = req.get("queryResult").get("parameters").get("date_chinese")
        fulfillmentText = notice_if_first_day(date_parameter)
        fulfillmentText2 = get_recommend(date_parameter)
        fulfillmentText3 = '學完單字就來做點測驗吧!\n\n輸入:“我要今天單字測驗”'
        
    elif req.get("queryResult").get("action") == "topic":
        date_parameter = req.get("queryResult").get("parameters").get("date_chinese")
        fulfillmentText = get_topic(date_parameter)
        fulfillmentText2 = '看不懂沒關係!\n\n先來看點單字慢慢學吧!\n\n輸入:“我要今天單字”'
        
    elif req.get("queryResult").get("action") == "sentence":
        date_parameter = req.get("queryResult").get("parameters").get("date_chinese")
        fulfillmentText = get_sentence(date_parameter)
        fulfillmentText2 = '今天的學習就到這囉\n\n如果你有跳過哪些步驟請回頭去看看吧\n\n期待明天的見面'
        fulfillmentText3 = get_learnfinish_topic(date_parameter)
        
    elif req.get("queryResult").get("action") == "unonestar":
        fulfillmentText = get_unonestar()
        
    elif req.get("queryResult").get("action") == "onestar":
        fulfillmentText = get_onestar()

    elif req.get("queryResult").get("action") == "quiz":
        date_parameter = req.get("queryResult").get("parameters").get("date_chinese")
        fulfillmentText = get_quiz(date_parameter)
        
    elif req.get("queryResult").get("action") == "sentence-ans":
        user_say = req.get("queryResult").get("queryText")
        temp = req.get("queryResult").get("outputContexts")
        date_parameter = temp[0]['parameters']['date_chinese']
        fulfillmentText = get_solution(user_say,date_parameter)
        fulfillmentText2 = '練習過句子了吧\n\n來看看完整句子吧!\n\n請輸入:“我要今天句子”'
        
    elif req.get("queryResult").get("action") == "word_quiz":
        date_parameter = req.get("queryResult").get("parameters").get("date_chinese")
        fulfillmentText = get_word_quiz(date_parameter)
        
    elif req.get("queryResult").get("action") == "word-ans":
        user_say = req.get("queryResult").get("queryText")
        temp = req.get("queryResult").get("outputContexts")
        date_parameter = temp[0]['parameters']['date_chinese']
        fulfillmentText = get_word_solution(user_say,date_parameter)
        fulfillmentText2 = '練習過單字了吧\n\n來試試句子練習吧!\n\n請輸入:“我要今天句子測驗”'
    
        
    else:
        return {}
    
    print("Response:")
    print(fulfillmentText)
    # 回傳
    return {
        "fulfillmentText": fulfillmentText,
        'fulfillmentMessages':[{"text":{"text":[fulfillmentText]}},{"text":{"text":[fulfillmentText2]}},{"text":{"text":[fulfillmentText3]}}],
        "source": "agent"
    }


def get_recommend(date_parameter):
    result = ""
    # 預設datetime為今天
    input_date = datetime.date.today()

    if date_parameter == '今天':
        input_date = datetime.date.today()
    elif date_parameter == '明天':
        input_date = datetime.date.today() + datetime.timedelta(days=1)
    elif date_parameter == '昨天':
        input_date = datetime.date.today() + datetime.timedelta(days=-1)

    result += "【" + to_string(input_date) + "的單字】\n\n\n"

    """ one_json_row -> 一串json資料，像是這樣
    {
        "_id" : ObjectId("5be0600ee58fb92b3c0b4798"),
        "日期" : "20181106",
        "單字1" : "algorithm",
        "單字2" : "classification",
        "單字3" : "sequence"
    } """
    one_json_row = collection.find_one({"日期": to_string(input_date)})

    for i in range(5):
        tmp_string = "單字" + str(i+1)
        word = one_json_row[tmp_string]
        translation = one_json_row["單字翻譯" + str(i+1)]
        result += "【"+tmp_string+"】" + word + ' :\n'+ translation +"\n\n"
    return result


def get_topic(date_parameter):
    result = ""
    # 預設datetime為今天
    input_date = datetime.date.today()

    if date_parameter == '今天':
        input_date = datetime.date.today()
    elif date_parameter == '明天':
        input_date = datetime.date.today() + datetime.timedelta(days=1)
    elif date_parameter == '昨天':
        input_date = datetime.date.today() + datetime.timedelta(days=-1)
        
    one_json_row = collection.find_one({"日期": to_string(input_date)})

    uva_num = int(one_json_row["題目編號"])
    div = int(uva_num/100)
    result = 'https://uva.onlinejudge.org/external/' + str(div)+'/'+str(int(uva_num))+'.pdf'
    result = "這是"+date_parameter+"的題目\n" + result
    
    return result

def get_sentence(date_parameter):

    today = datetime.date.today()
    result = ''
    
    if date_parameter == '昨天':
        day = (today + datetime.timedelta(days=-1)).strftime("%Y%m%d")
    elif date_parameter == '明天':
        day = (today + datetime.timedelta(days=+1)).strftime("%Y%m%d")
    else:
        day=today.strftime("%Y%m%d")
        
    result = '【'+day+'的句子】'
    i=collection.find_one({'日期':day})
    a=1
    for j in range(1,6):
        k=i['單字數每日句子'+str(j)]
        if(k==''):
            k=0
        if(int(k)>0):
            result += ('\n\n【句子'+str(j)+'】:'+i['每日句子'+str(j)]+'\n[在句子中學到的單字是]:')
            b=1
            while(b<=int(k)):
                result += ('\n'+str(a)+'. '+i['單字'+str(a)])#加翻譯太雜
                a=a+1
                b=b+1
            result += ('\n\n【句子'+str(j)+'的翻譯】:'+i['翻譯句子'+str(j)])
    
    return result
    
def get_onestar():
    result = 'CPE的一顆星選集:\n'
    df = pd.read_excel('CPE一顆星選集.xlsx')
    question=df['題目編號']
    for uva_num in question:
        div = int(uva_num/100)
        result += 'https://uva.onlinejudge.org/external/' + str(div)+'/'+str(uva_num)+'.pdf\n'
    return result

def get_unonestar():
    result = 'CPE尚未考過的一顆星選集:\n'
    df = pd.read_excel('CPE一顆星選集猜題.xlsx')
    question=df['題目編號']
    for uva_num in question:
        div = int(uva_num/100)
        result += 'https://uva.onlinejudge.org/external/' + str(div)+'/'+str(uva_num)+'.pdf\n'
    return result

def get_quiz(date_parameter):
    result = ""
    input_date = datetime.date.today()

    if date_parameter == '今天':
        input_date = datetime.date.today()
    elif date_parameter == '明天':
        input_date = datetime.date.today() + datetime.timedelta(days=1)
    elif date_parameter == '昨天':
        input_date = datetime.date.today() + datetime.timedelta(days=-1)

    result += "【" + to_string(input_date) + "的填充練習題】\n"

    one_json_row = collection.find_one({"日期": to_string(input_date)})

    result += "請依正確的順序回答數字配對\nEX:43512\n\n"

    # 題目
    for i in range(5):
        temp='句子'+str(i+1)
        tmp_string = "填空題" + str(i+1)
        quiz = one_json_row[tmp_string]
        if quiz=="":
            break
        result += temp + ":\n" + quiz + "\n"
        result += ('【翻譯'+str(i+1)+'】:'+one_json_row['翻譯句子'+str(i+1)]+'\n\n')

    order = one_json_row['亂數順序']
    # 作出推播順序專門用的數字index。 order:43521->push_order:54213 這邊預設為12345
    push_order = list('12345')
    for i in range(5):
        x = int(order[i]) -1
        push_order[x] = i +1

    # 寫入打亂過後的推播單字
    for i in range(5):
        tmp_string = "單字" + str(push_order[i])
        # 用'單字1'找到一整筆資料row
        word = one_json_row[tmp_string]
        # ->(1) verify\n
        result += "(" + str(i+1) + ") " + word + "\n"
    return result

def get_solution(inp,date_parameter):
    
    input_date = datetime.date.today()

    if date_parameter == '今天':
        input_date = datetime.date.today()
    elif date_parameter == '明天':
        input_date = datetime.date.today() + datetime.timedelta(days=1)
    elif date_parameter == '昨天':
        input_date = datetime.date.today() + datetime.timedelta(days=-1)
    
    one_json_row = collection.find_one({"日期": to_string(input_date)})
    
    inp_str=re.findall('[0-9]',inp)
    oup_str=list(one_json_row['亂數順序'])
    
    count_A=count_B=count_N=0
    
    if len(inp_str)!=5:
        return '空格有5格你打'+str(len(inp_str))+'個\n你很Cool嗎' 
    
    for i in range(5):
        if inp_str[i] == oup_str[i]:
            count_A+=1
        elif inp_str[i] in oup_str:
            count_B+=1
        else:
            count_N+=1
    
    if count_A == 5 and count_B == 0 and count_N == 0:
        return '全對了!\n\n你好棒!  好棒!好棒!好棒!'
    else:
        return '正確的答案順序是 : '+str(one_json_row['亂數順序']) +'\n\n看來你有哪裡答錯囉\n\n回頭再看一次吧!'

def get_word_quiz(date_parameter):
    result = ""
    input_date = datetime.date.today()
    if date_parameter == '今天':
        input_date = datetime.date.today()
    elif date_parameter == '明天':
        input_date = datetime.date.today() + datetime.timedelta(days=1)
    elif date_parameter == '昨天':
        input_date = datetime.date.today() + datetime.timedelta(days=-1)

    result += "【" + to_string(input_date) + "的單字配對練習題】\n\n"

    one_json_row = collection.find_one({"日期": to_string(input_date)})

    # 題目
    for i in range(5):
        tmp_string = "單字" + str(i+1)
        quiz = one_json_row[tmp_string]
        if quiz=="":
            break
        result += "(  ):" + quiz + "\n"

    order = one_json_row['亂數順序1']
    # 作出推播順序專門用的數字index。 order:43521->push_order:54213 這邊預設為12345
    push_order = list('12345')
    for i in range(5):
        x = int(order[i]) -1
        push_order[x] = i +1

    result += "請依順序由上到下，依以下單字翻譯的編號作配對 \nEX:43512\n\n"

    # 寫入打亂過後的推播單字
    for i in range(5):
        tmp_string = "單字翻譯" + str(push_order[i])
        # 用'單字1'找到一整筆資料row
        word = one_json_row[tmp_string]
        # ->(1) verify\n
        result += "(" + str(i+1) + ") " + word + "\n"
    return result

def get_word_solution(inp,date_parameter):
    
    input_date = datetime.date.today()

    if date_parameter == '今天':
        input_date = datetime.date.today()
    elif date_parameter == '明天':
        input_date = datetime.date.today() + datetime.timedelta(days=1)
    elif date_parameter == '昨天':
        input_date = datetime.date.today() + datetime.timedelta(days=-1)
    
    one_json_row = collection.find_one({"日期": to_string(input_date)})
    
    inp_str=re.findall('[0-9]',inp)
    oup_str=list(one_json_row['亂數順序1'])
    
    count_A=count_B=count_N=0
    
    if len(inp_str)!=5:
        return '空格有5格你打'+str(len(inp_str))+'個\n你很Cool嗎' 
    
    for i in range(5):
        if inp_str[i] == oup_str[i]:
            count_A+=1
        elif inp_str[i] in oup_str:
            count_B+=1
        else:
            count_N+=1
    
    if count_A == 5 and count_B == 0 and count_N == 0:
        return '全對了!\n\n你好棒!  好棒!好棒!好棒!'
    else:
        return '正確的答案順序是 : '+str(one_json_row['亂數順序1']) +'\n\n看來你有哪裡答錯囉\n\n回頭再看一次吧!'
    
def get_learnfinish_topic(date_parameter):
    if date_parameter == '今天':        
        result = ""
        # 預設datetime為今天
        today_date = datetime.date.today()
        #取昨天的日期
        yesterday_date = datetime.date.today() + datetime.timedelta(days=-1)
        result = ""
        one_json_row = collection.find_one({"日期": to_string(today_date)})
        second_json_row = collection.find_one({"日期": to_string(yesterday_date)})
        #取編號
        uva_num_today = int(one_json_row["題目編號"])
        uva_num_yesterday= int(second_json_row["題目編號"])
        #判斷題目編號是否一樣
        if uva_num_today!=uva_num_yesterday:    
            div = int(uva_num_yesterday/100)
            result = 'https://uva.onlinejudge.org/external/' + str(div)+'/'+str(int(uva_num_yesterday))+'.pdf'
            result = "已經有題目學習完囉，到UVa網站解題看看吧\n" + result
        return result
    else:
        return ''
def notice_if_first_day(date_parameter):
    if (date_parameter != '今天'):
        return ""

    result = ""
    # 今天的日期，資料結構為datetime
    today = datetime.date.today()
    # 今天的題目編號
    today_uva_num = int(collection.find_one({"日期": to_string(today)})["題目編號"])
    # 今天的題目編號跟前一天的作比較，不一樣的話今天就是新題目第一天
    if(today_uva_num != int(collection.find_one({"日期": to_string(today+datetime.timedelta(days=-1))})["題目編號"])):
        # 持續天數
        last_days = 1
        while True:
            next_uva_num = int(collection.find_one({"日期": to_string(today+datetime.timedelta(days=last_days))})["題目編號"])
            if(next_uva_num!=today_uva_num):
                break
            last_days +=1

        result += "安安，今天是新的題目喔~\n\n預估會需要%d天左右的時間學習\n\n" % last_days

        div = int(today_uva_num/100)
        result += '點我看看今天的題目是什麼吧:\nhttps://uva.onlinejudge.org/external/' + str(div)+'/'+str(int(today_uva_num))+'.pdf'
    return result
    
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
