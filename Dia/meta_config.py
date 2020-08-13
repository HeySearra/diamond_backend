import re
import colorama

colorama.init(autoreset=True)

DEBUG = True

CLS_PARSE_REG = re.compile(r"['](.*?)[']", re.S)

KB = 1 << 10
MB = KB * KB
GB = KB * MB
