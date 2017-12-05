# -*-coding:utf-8-*-

from urllib.request import urlopen
from bs4 import BeautifulSoup


def search_titles(pno):
    max_page_row = 100
    search_url = 'http://www.kukudas.com/bbs/search.php?srows={}&sfl=wr_subject&stx={}&sop=and&gr_id=jav&onetable=JAV1A'

    html = urlopen(search_url.format(max_page_row, pno))
    content = html.read().decode('utf-8')
    # print(content)

    bs = BeautifulSoup(content, 'html.parser')
    media_tags = bs.find_all('div', {'class': "media-heading"})
    print(len(media_tags))

    if len(media_tags) > 0:
        return [m.a.get_text().replace('\n', '') for m in media_tags]
    else:
        return ['no result']


def search_detail_list(search_text):
    return [
        ('title1', 'desc1', 'http://pythonscraping.com/img/gifts/img1.jpg'),
        ('title2', 'desc2', 'http://pythonscraping.com/img/gifts/img1.jpg'),
        ('title3', 'desc3', 'http://pythonscraping.com/img/gifts/img1.jpg'),
        ('title4', 'desc4', 'http://pythonscraping.com/img/gifts/img1.jpg'),
    ]