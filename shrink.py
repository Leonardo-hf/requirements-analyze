import os.path

if __name__ == '__main__':
    with open('packages.txt', 'r') as origin:
        with open('s_packages.txt', 'w') as shrink:
            for line in origin.readlines():
                line = line.strip()
                if not os.path.exists(os.path.join('packages', line)):
                    shrink.write(line + '\n')
