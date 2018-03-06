# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import logging
import os
import ujson


def find_id(search_id):
    global hits
    try:
        search_term = the_page.find(id=search_id)
        events = search_term.descendants
        for event in events:
            for keyword in keywords:
                if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                    hits += 1
                    post_slack(event.string, settings)
    except Exception as e:
        return


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


def load_settings():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'settings.json'), 'r', encoding='utf-8') as json_file:
            json_data = ujson.loads(json_file.read())
            settings = {}
            settings['url'] = 'https://www.svenskamagic.com/login.php'
            settings['params'] = {'loginusername': json_data.get('svm_usr'), 'password': json_data.get('svm_pwd'), 'action': 'process_login_attempt', 'x': 14, 'y': 10}
            settings['webhook'] = json_data.get('slack_webhook')
            settings['payload_text'] = json_data.get('slack_payload')
            settings['original_text'] = json_data.get('slack_payload').get('text')
        return settings
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
        hits = 0
        search_ids = ['nyamess_auktion', 'new_mail', 'nyamess']  # id's to look for when logged in
        keywords = ['biz', 'betalt', 'mail!', 'bud']  # string to look for in id if found

        response, status = loop.run_until_complete(get_url(settings.get('url'), settings.get('params')))
        if status == 200:
            try:
                the_page = BeautifulSoup(response, 'html.parser')
            except Exception as e:
                logging.error(f'couldn\'t parse page: {e}')
                the_page = ''

            for s in search_ids:
                find_id(s)
        else:
            logging.error(f'{status}: couldn\'t load site: {response}')

session.close()
loop.close()
