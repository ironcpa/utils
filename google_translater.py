import sys
from bs4 import BeautifulSoup
import urllib
from urllib.parse import urlencode
import requests


def test_on_web_page():
    params = {
        'h1': "hl=ko#ja/ko/[MDTM-366] 中出し専用！僕だけの"
    }
    #request = urllib.request.Request('https://translate.google.co.kr/', urlencode(params))
    url = 'https://translate.google.co.kr/'
    header = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'}
    res = requests.get(url + '?' + urlencode(params), headers=header)
    #res = requests.get(url, headers=header)

    print(res.text)

    bs = BeautifulSoup(res.text, 'html.parser')
    result = bs.find('span', {'id': 'result_box'})

    print(result.children)
    for c in result.children:
        print(c)


def test_googletrans():
    from googletrans import Translator

    tr = Translator()
    rslt = tr.translate('안녕하세요')
    print(rslt.src, '=>', rslt.text)

    rslt = tr.translate('[MDTM-366] 中出し専用！僕だけの', src='ja', dest='ko')
    print(rslt.src, '=>', rslt.text)



if __name__ == '__main__':
    test_googletrans()
