import argparse
import os

from colorama import Fore


def walk_check(key):
    for path, dirs, files in os.walk('.'):
        if '__pycache__' in path or 'migrations' in path:
            continue
        for f_name in files:
            if not f_name.endswith('.py'):
                continue
            f_name = os.path.join(path, f_name)
            with open(f_name, encoding='utf-8') as fp:
                lines = [i + 1 for i, line in enumerate(fp) if key in line]
                if len(lines) == 0:
                    continue
                print(f'`{key}` found in  {f_name:20s}:  [line {str(lines).strip("[]")}]')
                # print(f''
                #       + Fore.GREEN + f'`{key}`' + Fore.RESET + ' found in '
                #       + Fore.CYAN + f' {f_name:20s}' + Fore.RESET + ': '
                #       + Fore.BLUE + f'[line {str(lines).strip("[]")}]' + Fore.RESET)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('key', type=str, default=None)
    args = parser.parse_args()
    # if args.key is None:
    #     args.key = input('please input the key: ')
    walk_check(args.key)
