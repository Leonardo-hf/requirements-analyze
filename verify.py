import math
import os
import re
import signal
import time
from multiprocessing import Process, cpu_count

from bs4 import BeautifulSoup

from get_packages import spider, base_url


def term(sig_num, addtion):
    os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)


class VerifyProcess(Process):
    def __init__(self, packages):
        Process.__init__(self)
        self.packages = packages

    def run(self):
        verify(self.packages)


def multi_verify(splice=cpu_count()):
    signal.signal(signal.SIGTERM, term)
    path = 'packages'
    with open('verified.out', 'r') as correct:
        verified = set(map(lambda line: str(line).strip(), correct.readlines()))
    with open('verify.out', 'w'):
        pass
    if os.path.exists(path):
        all_p = os.listdir(path)
        all_p = list(filter(lambda p: p not in verified, all_p))
        if len(all_p) == 0:
            return
        n = math.ceil(len(all_p) / splice)
        processes = []
        for i in range(0, len(all_p), n):
            process = VerifyProcess(all_p[i:i + n])
            process.daemon = True
            process.start()
            processes.append(process)
        try:
            for process in processes:
                process.join()
        except Exception as e:
            print(str(e))
        merge()


def merge():
    for file in os.listdir():
        if re.match('verify[0-9]+[.]out', file):
            with open(file, 'r') as v:
                with open('verify.out', 'a') as out:
                    out.writelines(v.readlines())
            os.remove(file)
        if re.match('verified[0-9]+[.]out', file):
            with open(file, 'r') as v:
                with open('verified.out', 'a') as correct:
                    correct.writelines(v.readlines())
            os.remove(file)


def verify(packages):
    suffix = ['tar.gz', 'tar.bz2', 'zip', 'egg']
    for package in packages:
        trans = str.maketrans('._-', '   ')
        editions = list(
            filter(lambda name: str(package).translate(trans) in str(name).lower().translate(trans),
                   os.listdir('packages/{}'.format(package))))
        try:
            html = spider('{}/{}/'.format(base_url, package)).text
        except Exception as e:
            print('pid: {}, error: {}'.format(os.getpid(), e))
            continue
        soup = BeautifulSoup(html, "html.parser")
        packages = soup.findAll('a')
        editions_set = set()
        for p in packages:
            p = p.string
            for s in suffix:
                if str(p).endswith(s):
                    editions_set.add(p[0:p.find(s) - 1])
                    break
        # print('{}: {}'.format(len(editions), editions))
        # print('{}: {}'.format(len(editions_set), editions_set))
        if len(editions_set) != len(editions):
            with open('verify{}.out'.format(os.getpid()), 'a') as out:
                out.write(package + '\n')
        else:
            with open('verified{}.out'.format(os.getpid()), 'a') as correct:
                correct.write(package + "\n")


if __name__ == "__main__":
    multi_verify()
