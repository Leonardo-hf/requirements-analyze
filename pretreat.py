import os

import requirements_detector.detect as detect


def pretreat():
    with open('requirements.txt', 'w') as res:
        packages = os.listdir('packages')
        for package in packages:
            path = os.path.join('packages', package)
            for edition in os.listdir(path):
                r = os.path.join(path, edition)
                res.write(os.path.join(package, edition) + '\n')
                try:
                    requirements = detect.find_requirements(r)
                    for e in requirements:
                        res.write(str(e) + '\n')
                except Exception as e:
                    print(str(e))
                res.write('\n')


if __name__ == '__main__':
    pretreat()
