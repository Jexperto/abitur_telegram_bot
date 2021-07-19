import requests
from bs4 import BeautifulSoup

domain = 'http://abitur.mtuci.ru'
# url = "http://abitur.mtuci.ru/upload/iblock/008/Spisok-mag.xls"
url = "http://abitur.mtuci.ru/ranked_lists/magistracy.php"


def get_file():
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    href_div = soup.findAll('div', {"class": "documents_list_item"})
    endpoint = href_div[0].contents[1]['href']
    if href_div is None:
        return None
    file = requests.get(domain + endpoint)
    if file.content is None:
        return None
    return file.content


# open('table.xls', 'wb').write(get_file())
