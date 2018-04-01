# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from svm_notifications import get_url, load_settings, session
import asyncio
import logging
import sys


async def main():
    global hits
    hits = 0
    response, status = await get_url(settings.get('url'), settings.get('params'))
    response, status = await get_url('https://www.svenskamagic.com/marketplace/index.php?what=havewant', '')
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

loopz = asyncio.get_event_loop()
sem = asyncio.Semaphore(5)
sys.setrecursionlimit(10000)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    settings, tasks = load_settings(), []

    if settings is not False:
        loopz.run_until_complete(main())

session.close()
loopz.close()
