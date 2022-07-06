import math
import os
from multiprocessing import Process

from bs4 import BeautifulSoup

from get_packages import base_url, spider, ensure_dir, download, _extract_tar_files, _extract_zip_files


class SpiderProcess(Process):
    def __init__(self, packages):
        Process.__init__(self)
        self.packages = packages

    def run(self):
        dispatch(self.packages)


def dispatch(edition_list):
    for edition in edition_list:
        edition_name = str(edition.string)
        edition_url = str(edition.get('href'))
        edition_url = '{}/{}'.format(base_url[:-7], edition_url[6:])
        # logging.info(edition_name)
        if edition_name.endswith('tar.gz') or edition_name.endswith('tar.bz2'):
            split = edition_name.rfind('tar')
            suffix = edition_name[split:]
            prefix = edition_name[0:split - 1]
            outdir = 'packages/{}/{}'.format('frida', prefix)
            ensure_dir(outdir)
            tmp_path = '/tmp/temp_tar{}.'.format(os.getpid()) + suffix
            download(edition_url, tmp_path)
            _extract_tar_files(tmp_path, path=outdir)
        elif edition_name.endswith('zip') or edition_name.endswith('egg'):
            tmp_path = '/tmp/temp_zip{}.zip'.format(os.getpid())
            prefix = edition_name[0:edition_name.rfind('.')]
            outdir = 'packages/{}/{}'.format('frida', prefix)
            ensure_dir(outdir)
            download(edition_url, tmp_path)
            _extract_zip_files(tmp_path, path=outdir)
        elif not edition_name.endswith('whl'):
            with open('error.txt', 'a') as error:
                error.write('unknown file exts with {}\n'.format(edition_name))


if __name__ == '__main__':
    url = '{}/{}/'.format(base_url, 'frida')
    html = spider(url).text
    soup = BeautifulSoup(html, "html.parser")
    length = len(os.listdir('packages/frida'))
    edition_list = []
    a = soup.findAll('a')
    for edition in a:
        st = str(edition.string)
        if st.endswith('tar.gz') or st.endswith('egg'):
            edition_list.append(edition)
    edition_list = edition_list[length:]
    n = math.ceil(len(edition_list) / 8)
    processes = []
    for i in range(0, len(edition_list), n):
        process = SpiderProcess(edition_list[i:i + n])
        process.daemon = True
        process.start()
        processes.append(process)
    try:
        for process in processes:
            process.join()
    except Exception as e:
        print(str(e))
