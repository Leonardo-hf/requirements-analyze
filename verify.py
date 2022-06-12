import os

from bs4 import BeautifulSoup

from get_packages import spider, base_url


def verify():
    path = 'packages'
    suffix = ['tar.gz', 'tar.bz2', 'zip']
    correct = open('verified.out', 'a+')
    correct.seek(0)
    verified = list(map(lambda line: str(line).strip(), correct.readlines()))
    correct.seek(2)
    out = open('verify.out', "w")
    i = 1
    if os.path.exists(path):
        all_p = os.listdir(path)
        for package in all_p:
            print('verifying··· {}/{}'.format(i, len(all_p)))
            i += 1
            if package in verified:
                continue
            editions = list(
                filter(lambda name: package in str(name).lower(), os.listdir('packages/{}'.format(package))))
            html = spider('{}/{}/'.format(base_url, package)).text
            soup = BeautifulSoup(html, "html.parser")
            packages = soup.findAll('a')
            editions_set = set()
            for p in packages:
                p = p.string
                for s in suffix:
                    if s in p:
                        editions_set.add(p[0:p.find(s)])
                        break
            if len(editions_set) != len(editions):
                out.write(package + '\n')
            else:
                correct.write(package + "\n")
    correct.close()
    out.close()


if __name__ == "__main__":
    verify()
