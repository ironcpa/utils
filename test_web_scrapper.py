import sys
import asyncio
from bs4 import BeautifulSoup
import urllib
import aiohttp
import time
import pprint


REQ_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
              'referer': 'http://javtorrent.re/'}

BASE_URL = 'http://javtorrent.re'

def downloader():
    results = load_today_list()

    tasks_fetch_detail = [load_detail(i, x['detail_url']) for i, x in enumerate(results)]
    tasks_fetch_s_img = [load_image('small', i, x['small_img']) for i, x in enumerate(results)]

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    detail_results, _ = loop.run_until_complete(asyncio.wait(tasks_fetch_detail))
    s_img_results, _ = loop.run_until_complete(asyncio.wait(tasks_fetch_s_img))

    tasks_fetch_b_img = []
    for dr in detail_results:
        idx, url = dr.result()
        print('debug:', idx, url)
        tasks_fetch_b_img.append(load_image('big', idx, url))

    ''' 아래 코드는 에러발생: 답은 다음 코드에 있음
    tasks_fetch_b_img = [load_image('big', idx, url) for e in detail_results
                                                     for idx, url in e.result()]
                                                     '''

    ''' 아래 코드는 번갈아 가면서 값이 꺼내짐
    tasks_fetch_b_img = [print('test:', r) for e in detail_results
                         for r in e.result()]
                         '''

    b_img_results, _ = loop.run_until_complete(asyncio.wait(tasks_fetch_b_img))

    tasks_fetch_torrent = [load_torrent_link(x['product_id']) for x in results]
    #torrent_link_results, _ = loop.run_until_complete(asyncio.wait(tasks_fetch_torrent))

    # splitted run
    none_counter = 0
    for subtasks in get_chunks(tasks_fetch_torrent, 5):
        torrent_link_results, _ = loop.run_until_complete(asyncio.wait(subtasks))

        for i, task in enumerate(torrent_link_results):
            r = task.result()
            print(i, ':', r)
            if not r:
                none_counter += 1

        #time.sleep(5)
    print('failed req:', none_counter)

    print('all detail fetched')


def get_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]


def load_today_list():
    url = BASE_URL
    html = urllib.request.urlopen(url).read().decode('utf-8')
    bs = BeautifulSoup(html, 'html.parser')

    list_tags = bs.find('div', {'class': 'base'}).find_all('li')
    print(len(list_tags))
    results = []
    for l in list_tags:
        title_tag = l.a.find('span', {'class': 'base-t'})

        title = title_tag.text
        product_id = title[title.find('[')+1:title.find(']')]
        small_img = 'http:' + l.a.img['src']
        detail_url = BASE_URL + l.a.attrs['href']   # for big image

        results.append({'detail_url': detail_url,
                        'small_img': small_img,
                        'product_id': product_id})

    return results


async def load_detail(idx, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            html = await res.text()
            bs = BeautifulSoup(html, 'html.parser')

            big_img_url = bs.find('div', {'id': 'content'}).img['src']

    print('{} detail fetched: {}'.format(idx, big_img_url))
    return idx, 'http:' + big_img_url


async def load_image(type, idx, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            bin = await res.read()
            # create image data

    print('{} {} image fetched'.format(idx, type))
    return type, idx, bin


def load_torrents():
    torrent_tasks = [load_torrent_link('dvdms-254')]

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    done, _ = loop.run_until_complete(asyncio.wait(torrent_tasks))


async def load_torrent_link(product_no):
    #base_url = 'https://sukebei.nyaa.si/'
    base_url = 'https://sukebei.nyaa.si/?f=0&c=0_0&q={}'.format(product_no)
    url = base_url

    async with aiohttp.ClientSession(headers=REQ_HEADER) as session:
        async with session.get(url) as res:
            html = await res.text()
            bs = BeautifulSoup(html, 'html.parser')

            results = []
            try:
                if not bs.find('div', {'class': 'table-responsive'}):
                    print('fail')
                base = bs.find('div', {'class': 'table-responsive'}).find('tbody')
                rows = base.find_all('tr')

                print(product_no, len(rows))
                for tr in rows:
                    tds = tr.find_all('td')
                    size = get_float(tds[3].text)
                    link = tds[2].find_all('a')[1].attrs['href']
                    seeders = get_float(tds[5].text)
                    results.append({'size': size,
                                    'link': link,
                                    'seeders': seeders})

                sorted_r = sorted(results, key=lambda e: (e['size'], e['seeders']))

                if len(sorted_r) > 0 and 'link' in sorted_r[0]:
                    print('torrent link:{} {}'.format(product_no, sorted_r[0]['link'][:10]))

                return sorted_r[0]['link']
            except Exception as e:
                print('failed: >>>>>>>>>', product_no, e, url)


def get_float(s):
    return float(''.join(filter(lambda c: c.isdigit() or c == '.', s)))


if __name__ == '__main__':
    downloader()
    #load_torrents()
