# -*-coding:utf-8-*-

import re

import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
from selenium import webdriver
import time


def search_result(max_count, text):
    search_url = 'https://www.kukudas.com/bbs/search.php?srows={}&sfl=wr_subject&stx={}&sop=and&gr_id=jav&onetable=JAV1A'

    search_string = '+'.join(text.split())
    html = urlopen(search_url.format(max_count, search_string))
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


def search_detail_list(search_text, max_count):
    # return [
    #     # ('title0', 'SDMU-738 카토 모모카(加藤ももか, Momoka Kato)\nSOD의 새로운 마사지 게임 개발에 실험체가 된 것은 카토 모모카(加藤ももか) (21)', '', None, None),
    #     # ('[FHD]JUX-999 타니하라 노조미(谷原希美, Nozomi Tanihara)', '이웃 사람 조교 ~유부녀가 교화되어 암캐 성 봉사~', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('[FHD]JUX-999 타니하라 노조미(Nozomi Tanihara)', '이웃 사람 조교 ~유부녀가 교화되어 암캐 성 봉사', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title1', 'desc1', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title2', 'desc2', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title3', 'desc3', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title4', 'desc4', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    # ]

    content = search_result(max_count, search_text)
    bs = BeautifulSoup(content, 'html.parser')

    media_root = bs.find('div', {'class': 'search-media'})

    results = []
    if not media_root:
        return results

    medias = media_root.find_all('div', 'media')
    for m in medias:
        title = m.find('div', {'class': 'media-heading'}).a.get_text().replace('\n', '')
        desc = m.find('div', {'class': 'media-content'}).find('span', {'class': 'text-muted'}).get_text().replace('\n', '')
        desc = desc[:desc.index('imgdream.net')] if 'imgdream.net' in desc else desc
        img_url = m.find('div', {'class': 'photo pull-left'}).img.attrs['src']
        content_url = 'https://www.kukudas.com/bbs' + m.find('div', {'class': 'media-content'}).a.attrs['href'][1:]
        torrent_url, _, _ = get_content_detail(content_url)
        results.append((title, desc, img_url, torrent_url, content_url))

    return results


def search_main_page(page_count=1):
    search_url = 'https://www.kukudas.com/bbs/board.php?bo_table=JAV1A&page={}'

    results = []
    for page in range(page_count):
        html = urlopen(search_url.format(page))
        content = html.read().decode('utf-8')

        bs = BeautifulSoup(content, 'html.parser')

        list_tags = bs.find('div', {'class': 'list-body'}).find_all('div', {'class': 'list-row'})
        # list_tags = list_tags[:1]
        for l in list_tags:
            desc_tag = l.find('div', {'class': 'list-desc'})
            img_tag = l.find('div', {'class': 'list-img'})

            title = desc_tag.a.strong.get_text()
            img_url = img_tag.find('div', {'class': 'img-item'}).img.attrs['src']
            content_url = desc_tag.a.attrs['href']
            torrent_url, desc, _ = get_content_detail(content_url)

            results.append((title, desc, img_url, torrent_url, content_url))
    return results


def get_content_detail(content_url):
    html = urlopen(content_url)
    content = html.read().decode('utf-8')
    bs = BeautifulSoup(content, 'html.parser')

    torrent_url = bs.find(text=re.compile('torrent')).parent.attrs['href']
    desc = bs.find('div', {'class': 'view-content'}).find_all('p')[2].get_text()
    img_url = bs.find('div', {'class': 'view-content'}).find('img').attrs['src']
    print(torrent_url)

    return torrent_url, desc, img_url


def download_torrents(content_download_url_pairs):
    """
    not completed
    doesn't work as expected -> 오류 페이지 다운
    """
    driver = webdriver.PhantomJS()
    for p in content_download_url_pairs:
        driver.get(p[0])
        time.sleep(1)
        urllib.request.urlretrieve(p[1], 'test_download_phantomjs')
    driver.close()
    print('downloaded')