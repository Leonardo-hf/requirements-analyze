import os
from collections import defaultdict

import numpy as np
import pandas as pd


def compare_edition(a, b):
    if a == b:
        return True
    a_bits = a.split(".")
    b_bits = b.split(".")

    if len(a_bits) >= len(b_bits):
        amount = len(a_bits) - len(b_bits)
        for q in range(amount):
            b_bits.append("0")
    else:
        amount = len(b_bits) - len(a_bits)
        for q in range(amount):
            a_bits.append("0")
    for q in range(len(a_bits)):
        try:
            if int(a_bits[q]) > int(b_bits[q]):
                return True
            elif int(a_bits[q]) < int(b_bits[q]):
                return False
        except:
            if a_bits[q] > b_bits[q]:
                raise Exception(True)
            elif a_bits[q] < b_bits[q]:
                raise Exception(False)
    return True


def parse_relation(line):
    relations = []
    # types = ['<=', '<', '>=', '>', '~=', '==']
    f = ['<', '>', '~', '=']
    requirement = ''
    r = ''
    re = -1
    relation = []
    for i in range(0, len(line)):
        if line[i] in f:
            if len(relations) == 0 and len(requirement) == 0:
                requirement = line[:i].strip()
                relation.append(requirement)
            r = r + line[i]
        else:
            if len(r) > 0:
                re = i
                if len(relation) == 1:
                    relation.append(r)
                else:
                    relation[1] = r
                r = ''
            if line[i] == ',':
                relation.append(line[re:i].strip())
                relations.append(list(relation))
    if len(relations) == 0:
        if len(relation) == 0:
            relation = [line.strip(), 'latest', 'NaN']
        else:
            relation.append(line[re:].strip())
    else:
        relation[2] = line[re:].strip()
    relations.append(relation)
    return relations


def parse():
    datadict = defaultdict(list)
    latest = defaultdict(str)
    with open('parse_error.txt', 'w'):
        pass
    with open('requirements.txt', 'r') as infile:
        new_package = True
        i = 1
        for line in infile:
            print(i)
            i += 1
            line = line.strip()
            if line == '':
                new_package = True
                if package_name not in datadict['package']:
                    datadict['package'].append(package_name)
                    datadict['edition'].append(edition)
                    datadict['requirement'].append(np.nan)
                    datadict['constraint'].append(np.nan)
                    datadict['type'].append(np.nan)
                continue

            if new_package:
                # If this is the case, the current line gives the name of the package
                package_name, edition = line.split(os.path.sep)
                edition = edition[len(package_name) + 1:]
                # find the latest edition of the package
                try:
                    if latest[package_name] == '' or compare_edition(edition, latest[package_name]):
                        latest[package_name] = edition
                except Exception as e:
                    with open('parse_error.txt', 'a') as error:
                        error.write('error occurs when comparing {} & {} of package: {}\n'
                                    .format(edition, latest[package_name], package_name))
                    if e:
                        latest[package_name] = edition
                new_package = False
            else:
                # This line gives a requirement for the current package
                try:
                    for relation in parse_relation(line):
                        datadict['package'].append(package_name)
                        datadict['edition'].append(edition)
                        datadict['requirement'].append(relation[0])
                        datadict['constraint'].append(relation[2])
                        datadict['type'].append(relation[1])
                except Exception as e:
                    with open('parse_error.txt', 'a') as error:
                        error.write('error occurs when parse_relation {} of package: {}\n'
                                    .format(line, package_name))
    length = len(datadict['requirement'])
    for i in range(0, length):
        if datadict['type'][i] == 'latest':
            datadict['constraint'][i] = latest[datadict['requirement'][i]]
    # Convert to dataframe
    df = pd.DataFrame(data=datadict)
    df.head()
    df.to_csv('requirements.csv', index=False)


if __name__ == '__main__':
    parse()
    # print(parse_relation('pandas'))
