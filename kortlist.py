# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiohttp
import asyncio
import datetime
import logging
import os
import smtplib
import ujson


async def get_url(urlparse, params):
    try:
        async with sem, session.post(urlparse, data=params) as response:
            return await response.read(), response.status
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return e, 404


async def get_url2(urlparse):
    try:
        async with sem, session.get(urlparse, data=params) as response:
            return await response.read(), response.status
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return e, 404


def load_settings():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'data_svm.json'), 'r', encoding='utf-8') as json_file:
            json_data = ujson.loads(json_file.read())
            settings = {}
            settings['svm_usr'] = json_data.get('svm_usr')
            settings['svm_pwd'] = json_data.get('svm_pwd')
            settings['slack_notifications'] = json_data.get('slack_notifications')
            if settings.get('slack_notifications') is True:
                settings['webhook'] = json_data.get('slack_webhook')
                settings['payload_text'] = json_data.get('slack_payload')
                settings['original_text'] = settings.get('payload_text').get('text')
            settings['gmail_notifications'] = json_data.get('gmail_notifications')
            if settings.get('gmail_notifications') is True:
                settings['gmail_usr'] = json_data.get('gmail_usr')
                settings['gmail_app_pwd'] = json_data.get('gmail_app_pwd')
                settings['email_from'] = json_data.get('email_settings').get('from')
                settings['email_to'] = json_data.get('email_settings').get('to')
        if (settings.get('slack_notifications') is True or settings.get('gmail_notifications') is True):
            return settings
        else:
            logging.error('need to choose at least one notification option')
            return False
    except Exception as e:
        logging.error(e)
        return False


loop = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    settings = load_settings()
    if settings is not False:
        url = 'http://www.svenskamagic.com/login.php'
        params = {'loginusername': settings.get('svm_usr'), 'password': settings.get('svm_pwd'), 'action': 'process_login_attempt', 'x': 14, 'y': 10}
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        email_body = ''
        keywords = ['biz', 'betalt']
        keywords_auktion = ['bud']

        response, status = loop.run_until_complete(get_url(url, params))
        url = 'http://www.svenskamagic.com/marketplace/index.php?what=havewant'
        response, status = loop.run_until_complete(get_url2(url))
        try:
            the_page = BeautifulSoup(response, 'html.parser')
        except Exception as e:
            logging.error(f'couldn\'t parse page: {e}')
            the_page = ''
        test = the_page.find_all('a', class_='text_vit noline')
        cards = {}
        for t in test:
            if 'TORGET' in t.string or 'inloggade' in t.string:
                continue
            p = t.parent
            first_space = p.text.find(' ')
            if cards.get(t.string) is None:
                cards[t.string] = int(p.text[:first_space])
            else:
                cards[t.string] += int(p.text[:first_space])
    for key, value in cards.items():
        print(f'{key}\t{value}')

session.close()
loop.close()
