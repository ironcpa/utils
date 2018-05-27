import sys
import asyncio
from bs4 import BeautifulSoup
import urllib
import aiohttp


REQ_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
              'referer': 'http://javtorrent.re/'}


def downloader():
    base_url = 'http://javtorrent.re'

    url = base_url
    html = urllib.request.urlopen(url).read().decode('utf-8')
    bs = BeautifulSoup(html, 'html.parser')

    list_tags = bs.find('div', {'class': 'base'}).find_all('li')
    print(len(list_tags))
    results = []
    for l in list_tags:
        title_tag = l.a.find('span', {'class': 'base-t'})

        small_img = 'http:' + l.a.img['src']
        detail_url = base_url + l.a.attrs['href']   # for big image

        results.append({'detail_url': detail_url,
                        'small_img': small_img})

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

    print('all detail fetched')


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


if __name__ == '__main__':
    downloader()
