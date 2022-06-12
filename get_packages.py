import logging
import math
import os
import random
import shutil
import signal
import tarfile
import time
import zipfile
from multiprocessing import Process, cpu_count

import requests
from bs4 import BeautifulSoup
from cloghandler import ConcurrentRotatingFileHandler


class SpiderProcess(Process):
    def __init__(self, packages, packages_own):
        Process.__init__(self)
        self.packages = packages
        self.packages_own = packages_own

    def run(self):
        get(self.packages, self.packages_own)


tsinghua_url = 'https://pypi.tuna.tsinghua.edu.cn/simple'
aliyun_url = 'https://mirrors.aliyun.com/pypi/simple/'
base_url = aliyun_url

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 '
                  'Safari/537.36',
    'Connection': 'close'
}

proxy = {
    'http': '172.31.30.45:8888',
    'https': '172.31.30.45:8888'
}


def spider(url):
    return requests.get(url, headers=headers, proxies=random.choice(proxy))


def download(url, path, chunk_s=1024):
    req = requests.get(url, stream=True, headers=headers, proxies=random.choice(proxy))
    with open(path, 'wb') as fh:
        for chunk in req.iter_content(chunk_size=chunk_s):
            if chunk:
                fh.write(chunk)


def get_packages_list():
    filename = "packages.txt"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return file.readlines()
    else:
        req = spider(base_url)
        html = req.text
        soup = BeautifulSoup(html, "html.parser")
        packages = soup.findAll('a')
        packages_list = []
        with open(filename, "w") as file:
            for package in packages:
                package_name = package.string
                file.write(package_name + '\n')
                packages_list.append(package_name)
        return packages_list


def term(sig_num, addtion):
    logging.info('current pid is %s, group id is %s' % (os.getpid(), os.getpgrp()))
    os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)


def multi_get(splice=cpu_count()):
    signal.signal(signal.SIGTERM, term)
    ensure_dir('packages')
    packages = get_packages_list()
    packages_own = set(os.listdir('packages'))
    if len(packages_own) == len(packages):
        return
    n = math.ceil(len(packages) / splice)
    processes = []
    for i in range(0, len(packages), n):
        process = SpiderProcess(packages[i:i + n], packages_own)
        process.daemon = True
        process.start()
        processes.append(process)
    try:
        for process in processes:
            process.join()
    except Exception as e:
        print(str(e))


def get(packages, packages_own):
    for i, package in enumerate(packages):
        package = package.strip()
        # logging.info('Extracting package {} ~ {} / {}'.format(package, i + 1, len(packages)))
        # logging.info(time.time())
        if package in packages_own:
            continue
        try:
            extract_package(package)
        except Exception as e:
            logging.error('pid: {}, package: {}, error: {}'.format(os.getpid(), package, str(e)))
            dire = 'packages/{}'.format(package)
            if os.path.exists(dire):
                shutil.rmtree(dire)
            time.sleep(3)


def ensure_dir(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)
        return False
    return True


def _extract_tar_files(package_file, path):
    try:
        tar_file = tarfile.open(name=package_file, mode='r:*', encoding='utf-8')
    except Exception as e:
        logging.error('extract error on {} : {}'.format(package_file, str(e)))
        return
    for member in tar_file.getmembers():
        if member.isfile() and \
                ('setup.py' in member.name or 'requirements' in member.name or 'requires.txt' in member.name):
            with open('{}/{}'.format(path, member.name[member.name.rfind('/') + 1:]), 'wb') as file:
                with tar_file.extractfile(member.name) as w:
                    file.write(w.read())


def _extract_zip_files(package_file, path):
    try:
        z_file = zipfile.ZipFile(package_file, "r")
    except Exception as e:
        logging.error('extract error on {} : {}'.format(package_file, str(e)))
        return
    for name in z_file.namelist():
        if 'setup.py' in name or 'requirements.txt' in name or 'requires.txt' in name:
            with open('{}/{}'.format(path, name[name.rfind('/') + 1:]), 'wb') as file:
                with z_file.open(name, 'r') as w:
                    file.write(w.read())


def extract_package(name):
    url = '{}/{}/'.format(base_url, name)
    html = spider(url).text
    soup = BeautifulSoup(html, "html.parser")
    edition_list = soup.findAll('a')
    for edition in edition_list:
        edition_name = str(edition.string)
        edition_url = str(edition.get('href'))
        edition_url = '{}/{}'.format(base_url[:-7], edition_url[6:])
        # logging.info(edition_name)
        if edition_name.endswith('tar.gz') or edition_name.endswith('tar.bz2'):
            split = edition_name.rfind('tar')
            suffix = edition_name[split:]
            prefix = edition_name[0:split - 1]
            outdir = 'packages/{}/{}'.format(name, prefix)
            ensure_dir(outdir)
            tmp_path = '/tmp/temp_tar{}.'.format(os.getpid()) + suffix
            download(edition_url, tmp_path)
            _extract_tar_files(tmp_path, path=outdir)
        elif edition_name.endswith('zip') or edition_name.endswith('egg'):
            tmp_path = '/tmp/temp_zip{}.zip'.format(os.getpid())
            prefix = edition_name[0:edition_name.rfind('.')]
            outdir = 'packages/{}/{}'.format(name, prefix)
            ensure_dir(outdir)
            download(edition_url, tmp_path)
            _extract_zip_files(tmp_path, path=outdir)
        elif not edition_name.endswith('whl'):
            with open('error.txt', 'a') as error:
                error.write('unknown file exts with {}\n'.format(edition_name))


def init_log():
    logfile = "get_packages.log"
    filesize = 800 * 1024 * 1024
    rotate_handler = ConcurrentRotatingFileHandler(logfile, "a", filesize, encoding="utf-8")
    datefmt_str = '%Y-%m-%d %H:%M:%S'
    format_str = '%(asctime)s\t%(levelname)s\t%(message)s '
    formatter = logging.Formatter(format_str, datefmt_str)
    rotate_handler.setFormatter(formatter)
    logging.getLogger().addHandler(rotate_handler)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


if __name__ == '__main__':
    init_log()
    # multi_get(splice=1)
    multi_get()
