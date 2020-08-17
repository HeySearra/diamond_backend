import re

DEBUG = True

HOST_IP = 'localhost'

CLS_PARSE_REG = re.compile(r"['](.*?)[']", re.S)

KB = 1 << 10
MB = KB * KB
GB = KB * MB

TIME_FMT = '%Y-%m-%d %H:%M:%S'

ROOT_SUFFIX = '' # '\'s root'

HELL_WORDS = ['哦', '呀', '啊', '嘤', '惹', '呢', '！', '哼', '~', '嗷', '嘻', '¿']
