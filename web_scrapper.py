# -*-coding:utf-8-*-

import re
import collections

import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
from selenium import webdriver
import time

from PyQt5 import QtGui


class WebSearchResult:
    def __init__(self, date, title, desc, content_url, img_url, torrent_url):
        self.date = date
        self.title = title
        self.desc = desc
        self.content_url = content_url
        self.img_url = img_url
        self.torrent_url = torrent_url


def search_result(max_count, page_no, text):
    search_url_form = 'https://www.kukudas.com/bbs/search.php?srows={}&sfl=wr_subject&stx={}&sop=and&gr_id=jav&onetable=JAV1A&page={}'

    search_string = '+'.join(text.split())
    search_url = search_url_form.format(max_count, search_string, page_no)
    print(search_url)
    html = urlopen(search_url)
    content = html.read().decode('utf-8')

    return content


def search_titles(pno):
    if 'cd' in pno:
        pno = pno[:pno.index('cd')]

    content = search_result(100, 1, pno)

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


def search_detail_list(search_text, max_count, page_no, load_content=False):
    # return [
    #     # ('title0', 'SDMU-738 카토 모모카(加藤ももか, Momoka Kato)\nSOD의 새로운 마사지 게임 개발에 실험체가 된 것은 카토 모모카(加藤ももか) (21)', '', None, None),
    #     # ('[FHD]JUX-999 타니하라 노조미(谷原希美, Nozomi Tanihara)', '이웃 사람 조교 ~유부녀가 교화되어 암캐 성 봉사~', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('[FHD]JUX-999 타니하라 노조미(Nozomi Tanihara)', '이웃 사람 조교 ~유부녀가 교화되어 암캐 성 봉사', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title1', 'desc1', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title2', 'desc2', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title3', 'desc3', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    #     ('title4', 'desc4', 'http://pythonscraping.com/img/gifts/img1.jpg', None, None),
    # ]

    content = search_result(max_count, page_no, search_text)
    bs = BeautifulSoup(content, 'html.parser')

    media_root = bs.find('div', {'class': 'search-media'})

    results = []
    if not media_root:
        return results

    medias = media_root.find_all('div', 'media')
    for m in medias:
        date = ''
        title = m.find('div', {'class': 'media-heading'}).a.get_text().replace('\n', '')
        desc = m.find('div', {'class': 'media-content'}).find('span', {'class': 'text-muted'}).get_text().replace('\n', '')
        desc = desc[:desc.index('imgdream.net')] if 'imgdream.net' in desc else desc
        # img_url = m.find('div', {'class': 'photo pull-left'}).img.attrs['src']
        content_url = 'https://www.kukudas.com/bbs' + m.find('div', {'class': 'media-content'}).a.attrs['href'][1:]
        torrent_url, img_url = '', ''
        if load_content:
            date, torrent_url, _, img_url = get_content_detail(content_url)
        results.append(WebSearchResult(date, title, desc, content_url, img_url, torrent_url))

    return results


def search_main_page(start_page, page_count, load_content=False):
    search_url = 'https://www.kukudas.com/bbs/board.php?bo_table=JAV1A&page={}'

    results = []
    for page in range(start_page, start_page+page_count):
        url = search_url.format(page)
        html = urlopen(url)
        content = html.read().decode('utf-8')

        bs = BeautifulSoup(content, 'html.parser')

        list_tags = bs.find('div', {'class': 'list-body'}).find_all('div', {'class': 'list-row'})
        # list_tags = list_tags[:1]
        for l in list_tags:
            desc_tag = l.find('div', {'class': 'list-desc'})
            img_tag = l.find('div', {'class': 'list-img'})

            date = l.find('div', {'class': 'wr-date en'}).get_text()
            title = desc_tag.a.strong.get_text()
            # img_url = img_tag.find('div', {'class': 'img-item'}).img.attrs['src']
            content_url = desc_tag.a.attrs['href']
            torrent_url, desc, img_url = '', '', ''
            if load_content:
                date, torrent_url, desc, _ = get_content_detail(content_url)

            # results.append((title, desc, img_url, torrent_url, content_url))
            results.append(WebSearchResult(date, title, desc, content_url, img_url, torrent_url))

    return results


def get_content_detail(content_url):
    html = urlopen(content_url)
    content = html.read().decode('utf-8')
    bs = BeautifulSoup(content, 'html.parser')

    date = bs.find('div', {'class': 'panel-heading'}).find('span', {'class': 'hidden-xs pull-right'}).get_text().replace('\n', '')
    torrent_url = bs.find(text=re.compile('torrent')).parent.attrs['href']
    desc = bs.find('div', {'class': 'view-content'}).find_all('p')[2].get_text()
    img_url = bs.find('div', {'class': 'view-content'}).find('img').attrs['src']
    print('get_content_detail: {}'.format(torrent_url))

    return date, torrent_url, desc, img_url


def get_content_with_image(content_url):
    date, torrent_url, desc, img_url = get_content_detail(content_url)
    data = urllib.request.urlopen(img_url).read()
    image = QtGui.QImage()
    image.loadFromData(data)

    return date, torrent_url, desc, image


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


def download_torrents_chromedriver(content_download_url_pairs):
    # driver = webdriver.Chrome('C:\\__devenv\\chromedriver\\chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', {
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True
    })
    driver = webdriver.Chrome(executable_path='C:\\__devenv\\chromedriver\\chromedriver.exe', chrome_options=options)
    for p in content_download_url_pairs:
        driver.get(p[0])
        time.sleep(1)
        # urllib.request.urlretrieve(p[1], 'test_download_chrome.torrent')
        driver.get(p[1])
    # driver.close()
    print('downloaded')


if __name__ == '__main__':
    html = urlopen('https://hentaku.net/poombun.php')
    content = html.read().decode('utf-8')
    bs = BeautifulSoup(content, 'html.parser')
    print(content)

    # hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    #        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    #        'Accept-Encoding': 'none',
    #        'Accept-Language': 'en-US,en;q=0.8',
    #        'Connection': 'keep-alive'}
    # req = urllib.request.Request('https://hentaku.net/poombun.php')
    # req.add_header("User-Agent","Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13")

