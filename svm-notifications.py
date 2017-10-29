#!/usr/bin/env python
import json
import datetime
import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup

loop = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))
with open(os.path.join(os.path.dirname(__file__), 'data_svm.json'), 'r', encoding='utf-8') as json_file:
    json_data = json.loads(json_file.read())
    svm_usr = json_data.get('svm_usr')
    svm_pwd = json_data.get('svm_pwd')
    webhook = json_data.get('slack_webhook')
    payload_text = json_data.get('slack_payload')
    original_text = payload_text['text']
report = open(os.path.join(os.path.dirname(__file__), 'report_svm.txt'), 'a+')
keywords = ['biz', 'betalt']
keywords_auktion = ['bud']


async def post_slack(event):
    global payload_text
    global original_text
    global webhook
    payload_text['text'] = '{}{}'.format(original_text, event)
    payload = json.dumps(payload_text)

    try:
        async with sem, session.post(webhook, data=payload) as response:
            return await response.read()
    except:
        report.write('')


async def get_url(urlparse, params):
    try:
        async with sem, session.post(urlparse, data=params) as response:
            if response.status == 200:
                return await response.read()
            else:
                return 'ERROR'
    except aiohttp.client_exceptions.ClientConnectorError as exc:
        print(exc)
        return exc


url = 'http://www.svenskamagic.com/login.php'
params = {'loginusername': svm_usr,
          'password': svm_pwd,
          'action': 'process_login_attempt',
          'x': 14,
          'y': 10}

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

response = loop.run_until_complete(get_url(url, params))
the_page = BeautifulSoup(response, 'html.parser')
hits = 0
try:
    new_mail = the_page.find(id='new_mail')
    events = new_mail.descendants
    for event in events:
        if ('mail!' in str(event.string) and 'NavigableString' in str(event.__class__)):
            hits += 1
            loop.run_until_complete(post_slack(event.string))
except Exception:
    pass
try:
    nyamess = the_page.find(id='nyamess')
    events = nyamess.descendants
    for event in events:
        for keyword in keywords:
            if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                hits += 1
                loop.run_until_complete(post_slack(event.string))
except Exception:
    pass
try:
    nyamess = the_page.find(id='nyamess_auktion')
    events = nyamess.descendants
    for event in events:
        for keyword in keywords_auktion:
            if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                hits += 1
                loop.run_until_complete(post_slack(event.string))
except Exception:
    pass

if hits > 0:
    report.write('{}: new biz!\n'.format(now))
else:
    report.write('{}: nothing new\n'.format(now))
report.close()
session.close()
loop.close()
