import os
from collections import defaultdict

import pandas as pd
import tqdm

from requirements_detector import detect


def transfer(r):
    r = r.name
    if 'unknown' in r:
        r = r[r.rfind('/') + 1:r.find('.git')]
    return r


def get_requirements(name):
    p = 'pypi/{}'.format(name)
    try:
        requirements = detect.find_requirements(p)
        return set(map(lambda r: transfer(r), requirements))
    except:
        return {}


def parse(path='files/f_requirements_pypi.csv'):
    csv = defaultdict(list)
    packages = os.listdir('pypi')
    for i in tqdm.tqdm(range(len(packages)), total=len(packages), desc="解析依赖进度"):
        requirements = get_requirements(packages[i])
        for r in requirements:
            csv['package'].append(packages[i].lower())
            csv['requirement'].append(r.lower())
    df = pd.DataFrame(data=csv).drop_duplicates(subset=['package', 'requirement'])
    df.to_csv(path, index=False)





