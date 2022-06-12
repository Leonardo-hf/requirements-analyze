import os.path
import shutil
import zipfile

from get_packages import get_packages_list, ensure_dir, extract_package, get
# from parse import parse
from pretreat import pretreat
from analyze import draw

if __name__ == '__main__':
    # shutil.rmtree('packages/1')
    extract_package('aisling-connector')
    # pretreat()
    # parse()
    # draw()
