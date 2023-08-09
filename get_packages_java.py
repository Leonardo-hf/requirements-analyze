from lxml import etree

from pypi.util import spider, ensure_dir

central_url = 'https://repo1.maven.org/maven2'
base_url = central_url


def search_all(start_page=base_url):
    page = etree.HTML(spider(start_page).text)
    folder = page.xpath('//*[@id="contents"]/a')
    for f in folder:
        f = f.text
        if f == '../':
            continue
        if f.endswith('/'):
            search_all('{}/{}'.format(start_page, f))
            continue
        if f.endswith('.pom'):
            pom = spider('{}{}'.format(start_page, f)).text
            with open('../../java/{}.xml'.format(start_page[32:].replace('/', '@'), 'w')) as f:
                f.write(pom)


if __name__ == '__main__':
    ensure_dir('../../java/')
    with open('files/packages_java.txt', 'r') as f:
        for l in f:
            start = l.strip()
            search_all(start)
