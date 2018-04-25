# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import logging
import os
import ujson


async def find_id(search_id, the_page):
    global hits
    try:
        search_term = the_page.find(id=search_id)
        if search_term is None:
            return
        events = search_term.descendants
        for event in events:
            for keyword in keywords:
                if (keyword in str(event.string) and 'NavigableString' in str(event.__class__)):
                    hits += 1
                    await post_slack(event.string, settings)
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
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        async with sem, session.post(urlparse, data=params, headers=headers) as response:
            return await response.read(), response.status
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return e, 404


def load_settings():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json'), 'r', encoding='utf-8') as json_file:
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


async def main():
    global hits
    hits = 0
    response, status = await get_url(settings.get('url'), settings.get('params'))
    if status == 200:
        try:
            the_page = BeautifulSoup(response, 'html.parser')
        except Exception as e:
            logging.error(f'couldn\'t parse page: {e}')
            return
        for s in search_ids:
            tasks.append(find_id(s, the_page))
    else:
        logging.error(f'{status}: couldn\'t load site: {response}')
    await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    settings, tasks = load_settings(), []
    search_ids = ['nyamess_auktion', 'new_mail', 'nyamess']  # id's to look for when logged in
    keywords = ['biz', 'betalt', 'mail!', 'bud']  # string to look for in id if found

    if settings is not False:
        loop.run_until_complete(main())
    session.close()
    loop.close()
