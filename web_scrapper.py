# -*-coding:utf-8-*-

import re

from urllib.request import urlopen
from bs4 import BeautifulSoup


def search_result(max_count, text):
    search_url = 'https://www.kukudas.com/bbs/search.php?srows={}&sfl=wr_subject&stx={}&sop=and&gr_id=jav&onetable=JAV1A'
    html = urlopen(search_url.format(max_count, text))
    content = html.read().decode('utf-8')
    # print(content)

    return content


def search_titles(pno):
    if 'cd' in pno:
        pno = pno[:pno.index('cd')]

    content = search_result(100, pno)

    bs = BeautifulSoup(content, 'html.parser')
    # media_tags = bs.find_all('div', {'class': "media-heading"})
    # print(len(media_tags))
    #
    # if len(media_tags) > 0:
    #     return [m.a.get_text().replace('\n', '') for m in media_tags]
    # else:
    #     return ['no result']

    product_infos = bs.find_all('div', {'class': 'media'})
    results = []
    for info in product_infos:
        title = info.find('div', {'class': 'media-heading'}).a.get_text().replace('\n', '')
        desc = info.find('div', {'class': 'media-content'}).find('span', {'class': 'text-muted'}).get_text().replace('\n', '')
        results.append(title + ', ' + desc)

    if len(results) > 0:
        return results
    else:
        return ['no result']


def search_detail_list(search_text):
    # return [
    #     ('title1', 'desc1', 'http://pythonscraping.com/img/gifts/img1.jpg'),
    #     ('title2', 'desc2', 'http://pythonscraping.com/img/gifts/img1.jpg'),
    #     ('title3', 'desc3', 'http://pythonscraping.com/img/gifts/img1.jpg'),
    #     ('title4', 'desc4', 'http://pythonscraping.com/img/gifts/img1.jpg'),
    # ]

    content = search_result(3, search_text)
    bs = BeautifulSoup(content, 'html.parser')

    media_root = bs.find('div', {'class': 'search-media'})

    results = []
    if not media_root:
        return results

    medias = media_root.find_all('div', 'media')
    for m in medias:
        title = m.find('div', {'class': 'media-heading'}).a.get_text().replace('\n', '')
        desc = m.find('div', {'class': 'media-content'}).find('span', {'class': 'text-muted'}).get_text().replace('\n', '')
        img_url = m.find('div', {'class': 'photo pull-left'}).img.attrs['src']
        content_url = 'https://www.kukudas.com/bbs' + m.find('div', {'class': 'media-content'}).a.attrs['href'][1:]
        torrent_url = get_torrent_url(content_url)
        results.append((title, desc, img_url, torrent_url, content_url))

    return results


def get_torrent_url(content_url):
    # content_url = 'https://www.kukudas.com/bbs' + content_url[1:]
    html = urlopen(content_url)
    content = html.read().decode('utf-8')
    bs = BeautifulSoup(content, 'html.parser')

    download_url = bs.find(text=re.compile('torrent')).parent.attrs['href']
    print(download_url)
    return download_url
