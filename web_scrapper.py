# -*-coding:utf-8-*-

from urllib.request import urlopen
from bs4 import BeautifulSoup


def search_titles(pno):
    if 'cd' in pno:
        pno = pno[:pno.index('cd')]
        
    max_page_row = 100
    search_url = 'https://www.kukudas.com/bbs/search.php?srows={}&sfl=wr_subject&stx={}&sop=and&gr_id=jav&onetable=JAV1A'
    # search_url = 'https://www.kukudas.com/bbs/board.php?bo_table=JAV1A&sca=&sfl=wr_subject&stx=club-421&sop=and'
    html = urlopen(search_url.format(max_page_row, pno))
    content = html.read().decode('utf-8')
    print(content)

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


    return [
        ('title1', 'desc1', 'http://pythonscraping.com/img/gifts/img1.jpg'),
        ('title2', 'desc2', 'http://pythonscraping.com/img/gifts/img1.jpg'),
        ('title3', 'desc3', 'http://pythonscraping.com/img/gifts/img1.jpg'),
        ('title4', 'desc4', 'http://pythonscraping.com/img/gifts/img1.jpg'),
    ]