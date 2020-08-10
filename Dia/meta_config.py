import re
import colorama

colorama.init(autoreset=True)

DEBUG = True

CLS_PARSE_REG = re.compile(r"['](.*?)[']", re.S)

