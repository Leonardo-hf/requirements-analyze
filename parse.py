import os
from collections import defaultdict

import numpy as np
import requirements

import pandas as pd


def compare_edition(a, b):
    if a == b:
        return True
    a_bits = a.split(".")
    b_bits = b.split(".")

    if len(a_bits) >= len(b_bits):
        amount = len(a_bits) - len(b_bits)
        for q in range(amount):
            a_bits.append("0")
    else:
        amount = len(b_bits) - len(a_bits)
        for q in range(amount):
            b_bits.append("0")

    for q in range(len(a_bits)):
        if int(a_bits[q]) > int(b_bits[q]):
            return True
        elif int(a_bits[q]) < int(b_bits[q]):
            return False
    return True


def parse():
    datadict = defaultdict(list)
    latest = defaultdict(str)
    with open('requirements.txt', 'r') as infile:
        new_package = True
        for line in infile:
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
                edition = edition[str(edition).rindex('-') + 1:]
                # find the latest edition of the package
                if compare_edition(edition, latest[package_name]):
                    latest[package_name] = edition
                new_package = False
            else:
                # This line gives a requirement for the current package
                try:
                    for req in requirements.parse(line):
                        datadict['package'].append(package_name)
                        datadict['requirement'].append(req.name)
                except ValueError as e:
                    print(str(e))
                    pass

    # Convert to dataframe
    df = pd.DataFrame(data=datadict)
    df.head()
    df.to_excel('1.xlsx')
