import argparse
import os

from colorama import Fore


def walk_check(key):
    lines = 0
    for path, dirs, files in os.walk('.'):
        if any(s in path for s in ['__pycache__', 'migrations', 'frontend']):
            continue
        for f_name in files:
            if not f_name.endswith('.py'):
                continue
            f_name = os.path.join(path, f_name)
            with open(f_name, encoding='utf-8') as fp:
                contains = []
                for i, line in enumerate(fp):
                    lines += 1
                    if key in line:
                        contains.append(i+1)
                if len(contains) == 0:
                    continue
                print(f'`{key}` found in  {f_name:20s}:  [line {str(contains).strip("[]")}]')
                # print(f''
                #       + Fore.GREEN + f'`{key}`' + Fore.RESET + ' found in '
                #       + Fore.CYAN + f' {f_name:20s}' + Fore.RESET + ': '
                #       + Fore.BLUE + f'[line {str(lines).strip("[]")}]' + Fore.RESET)
    print(f'\n[total lines of DiaDoc backend: {lines}]')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('key', type=str, default=None)
    args = parser.parse_args()
    # if args.key is None:
    #     args.key = input('please input the key: ')
    walk_check(args.key)
