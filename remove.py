import os
import shutil


def remove(file='verify.out'):
    if os.path.exists(file):
        with open(file, 'r') as f:
            packages = list(map(lambda line: str(line).strip(), f.readlines()))
            for package in packages:
                if package == '':
                    continue
                path = 'packages/{}'.format(package)
                if os.path.exists(path):
                    shutil.rmtree(path)


if __name__ == "__main__":
    remove()
