# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import logging
import os
import ujson
import sys


async def get_url(urlparse, params):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        async with sem, session.post(urlparse, data=params, headers=headers) as response:
            return await response.read(), response.status
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return e, 404


def load_settings():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'settings.json'), 'r', encoding='utf-8') as json_file:
            json_data = ujson.loads(json_file.read())
            settings = {}
            settings['url'] = 'https://www.svenskamagic.com/login.php'
            settings['url2'] = 'https://www.svenskamagic.com/marketplace/index.php?what=havewant'
            settings['params'] = {'loginusername': json_data.get('svm_usr'), 'password': json_data.get('svm_pwd'), 'action': 'process_login_attempt', 'x': 14, 'y': 10}
            settings['webhook'] = json_data.get('slack_webhook')
            settings['payload_text'] = json_data.get('slack_payload')
            settings['original_text'] = json_data.get('slack_payload').get('text')
        return settings
    except Exception as e:
        logging.error(e)
        return False


async def main():
    global hits
    hits = 0
    response, status = await get_url(settings.get('url'), settings.get('params'))
    response, status = await get_url(settings.get('url2'), settings.get('params'))
    if status == 200:
        try:
            the_page = BeautifulSoup(response, 'html.parser')
            cards = the_page.findAll('a', class_='text_vit noline')
            for card in cards:
                if 'inloggade' in card.parent.text:
                    continue
                elif 'TORGET' in card.parent.text:
                    continue
                elif 'på biz' in card.parent.text:
                    continue
                try:
                    card_name = card.string
                    card_set = card.parent.parent.previous_sibling
                    card_count = card.parent.text[:card.parent.text.find(' ')]
                    while card_set.name != 'b':
                        card_set = card_set.parent.previous_sibling
                    print(f'{card_count}\t{card_name.strip()}\t{card_set.string}')
                except Exception:
                    continue
        except Exception as e:
            logging.error(f'couldn\'t parse page: {e}')
            return
    else:
        logging.error(f'{status}: couldn\'t load site: {response}')
    await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))
sys.setrecursionlimit(10000)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    settings, tasks = load_settings(), []
    search_ids = ['nyamess_auktion', 'new_mail', 'nyamess']  # id's to look for when logged in
    keywords = ['biz', 'betalt', 'mail!', 'bud']  # string to look for in id if found

    if settings is not False:
        loop.run_until_complete(main())

session.close()
loop.close()
