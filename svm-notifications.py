#!/usr/bin/env python
import json
import datetime
import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys

try:
    with open(os.path.join(os.path.dirname(__file__), 'data_svm.json'), 'r', encoding='utf-8') as json_file:
        json_data = json.loads(json_file.read())
        svm_usr = json_data.get('svm_usr')
        svm_pwd = json_data.get('svm_pwd')
        slack_notifications = json_data.get('slack_notifications')
        if slack_notifications is True:
            webhook = json_data.get('slack_webhook')
            payload_text = json_data.get('slack_payload')
            original_text = payload_text['text']
        gmail_notifications = json_data.get('gmail_notigications')
        if gmail_notifications is True:
            gmail_usr = json_data.get('gmail_usr')
            gmail_app_pwd = json_data.get('gmail_app_pwd')
            email_from = json_data.get('email_settings').get('from')
            email_to = json_data.get('email_settings').get('to')
except Exception as exc:
    print(exc)
    sys.exit()

assert slack_notifications is True or gmail_notifications is True, 'need to choose at least one notification option'

loop = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))
report = open(os.path.join(os.path.dirname(__file__), 'report_svm.txt'), 'a+')

url = 'http://www.svenskamagic.com/login.php'
params = {'loginusername': svm_usr, 'password': svm_pwd, 'action': 'process_login_attempt', 'x': 14, 'y': 10}
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
email_body = ''
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


def start_notifications(event_string):
    global email_body
    if slack_notifications is True:
        loop.run_until_complete(post_slack(event_string))
    if gmail_notifications is True:
        email_body = email_body + '{}\n'.format(event_string)


response = loop.run_until_complete(get_url(url, params))
the_page = BeautifulSoup(response, 'html.parser')
hits = 0

try:
    new_mail = the_page.find(id='new_mail')
    events = new_mail.descendants
    for event in events:
        if ('mail!' in str(event.string) and 'NavigableString' in str(event.__class__)):
            hits += 1
            start_notifications(event.string)
except Exception:
    pass

try:
    nyamess = the_page.find(id='nyamess')
    events = nyamess.descendants
    for event in events:
        for keyword in keywords:
            if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                hits += 1
                start_notifications(event.string)
except Exception:
    pass

try:
    nyamess = the_page.find(id='nyamess_auktion')
    events = nyamess.descendants
    for event in events:
        for keyword in keywords_auktion:
            if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                hits += 1
                start_notifications(event.string)
except Exception:
    pass

if hits > 0:
    report.write('{}: new activity!\n'.format(now))
    if gmail_notifications is True:
        try:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(gmail_usr, gmail_app_pwd)

            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = 'New svm activity'

            msg.attach(MIMEText(email_body))
            server.sendmail(email_from, email_to, msg.as_string())
        except Exception as exc:
            print(exc)
else:
    report.write('{}: nothing new\n'.format(now))

report.close()
session.close()
loop.close()
