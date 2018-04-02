# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS
from svm_notifications import get_url, load_settings, session
import aiomysql
import asyncio
import logging
import sys
import ujson


def set_or_add(d, k, v):
    try:
        if k not in d:
            d[k] = v
        else:
            d[k] += v
    except Exception as e:
        logging.error(f'd: {type(d)} - k: {type(k)} - v: {type(v)} - e: {e}')


def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same


async def get_local_cards():
    try:
        async with aiomysql.create_pool(host='localhost', port=3306, user='root', password='', db='cards', charset='utf8', loop=loopz) as pool:
            async with pool.get() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT * FROM for_sale')
                    value = await cursor.fetchall()
                    return value
    except Exception as e:
        logging.error(f'couldnt get data from db: {e}')


async def get_set_info():
    try:
        async with aiomysql.create_pool(host='localhost', port=3306, user='root', password='', db='cards', charset='utf8', loop=loopz) as pool:
            async with pool.get() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT * FROM set_info')
                    value = await cursor.fetchall()
                    return value
    except Exception as e:
        logging.error(f'couldnt get data from db: {e}')


async def main():
    global hits
    hits = 0
    response, status = await get_url(settings.get('url'), settings.get('params'))
    response, status = await get_url('https://www.svenskamagic.com/marketplace/index.php?what=havewant', '')
    if status == 200:
        try:
            the_page = BS(response, 'html.parser')
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
                    card_set = card.parent.parent.previous_sibling if card.parent.parent.previous_sibling is not None else card.parent
                    card_count = card.parent.text[:card.parent.text.find(' ')]
                    while card_set.name != 'b':
                        card_set = card_set.previous_sibling
                    if card_name not in svm_cards:
                        svm_cards[card_name] = {}
                    set_or_add(svm_cards[card_name], card_set.string, int(card_count))
                except Exception:
                    continue
        except Exception as e:
            logging.error(f'couldn\'t parse page: {e}')
            return
    else:
        logging.error(f'{status}: couldn\'t load site: {response}')
    await asyncio.gather(*tasks)
    set_info = {}
    si = await get_set_info()
    for o in si:
        set_info[o[1]] = o[4]
    lc = await get_local_cards()
    for l in lc:
        if l[2] not in local_cards:
            local_cards[l[2]] = {}
        try:
            set_or_add(local_cards[l[2]], set_info.get(l[4]), l[1])
        except Exception as e:
            logging.error(f'{l[2]} - {set_info.get(l[4])} - {l[1]}: {e}')
    await session.close()
    added, removed, modified, same = dict_compare(svm_cards, local_cards)
    print(f'only svm: {ujson.dumps(added)}\nonly local: {ujson.dumps(removed)}\nmismatch: {ujson.dumps(modified)}')


loopz = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
sys.setrecursionlimit(10000)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    settings = load_settings()
    tasks, svm_cards, local_cards = [], {}, {}

    if settings is not False:
        loopz.run_until_complete(main())

loopz.close()
