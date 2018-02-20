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


async def post_slack(event, settings):
    payload = settings.get('payload_text')
    payload['text'] = f'{settings.get("original_text")}{event}'
    logging.debug(payload)
    try:
        async with sem, session.post(settings['webhook'], data=ujson.dumps(payload)) as response:
            return await response.read()
    except Exception as e:
        logging.error(f'failed to post to slack: {e}')


async def get_url(urlparse, params):
    try:
        async with sem, session.post(urlparse, data=params) as response:
            return await response.read(), response.status
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return e, 404


def start_notifications(event_string, settings):
    global email_body
    if settings.get('slack_notifications') is True:
        response = loop.run_until_complete(post_slack(event_string, settings))
        logging.debug(response)
        if response != b'ok':
            logging.error(f'slack response: {response}. \'{settings.get("original_text")}{event_string}\'')
    if settings.get('gmail_notifications') is True:
        email_body = email_body + '{event_string}\n'


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
        if response == 200:
            try:
                the_page = BeautifulSoup(response, 'html.parser')
            except Exception as e:
                logging.error(f'couldn\'t parse page: {e}')
                the_page = ''
            hits = 0

            try:
                new_mail = the_page.find(id='new_mail')
                events = new_mail.descendants
                for event in events:
                    if ('mail!' in str(event.string) and 'NavigableString' in str(event.__class__)):
                        hits += 1
                        start_notifications(event.string, settings)
            except Exception as e:
                pass

            try:
                nyamess = the_page.find(id='nyamess')
                events = nyamess.descendants
                for event in events:
                    for keyword in keywords:
                        if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                            hits += 1
                            start_notifications(event.string, settings)
            except Exception as e:
                pass

            try:
                nyamess = the_page.find(id='nyamess_auktion')
                events = nyamess.descendants
                for event in events:
                    for keyword in keywords_auktion:
                        if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                            hits += 1
                            start_notifications(event.string, settings)
            except Exception as e:
                pass

            if hits > 0:
                logging.info('f{now}: new activity!')
                if settings.get('gmail_notifications') is True:
                    try:
                        server = smtplib.SMTP('smtp.gmail.com:587')
                        server.ehlo()
                        server.starttls()
                        server.login(settings('gmail_usr'), settings.get('gmail_app_pwd'))

                        msg = MIMEMultipart()
                        msg['From'] = settings.get('email_from')
                        msg['To'] = settings.get('email_to')
                        msg['Subject'] = 'New svm activity'

                        msg.attach(MIMEText(email_body))
                        server.sendmail(settings.get('email_from'), settings.get('email_to'), msg.as_string())
                    except Exception as e:
                        logging.error(f'mail notification failed: {e}')
            else:
                logging.info(f'{now}: nothing new')
        else:
            logging.error(f'{status} couldn\'t load site: {response}')

session.close()
loop.close()
