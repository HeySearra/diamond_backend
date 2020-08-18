import datetime
import re
import json
import base64
import urllib


def encode(s):
    return urllib.parse.quote(base64.b64encode(str(s).encode()).decode(encoding="utf-8"))
    # return str(s)


def decode(s):
    if isinstance(s, bytes):
        s = s.decode()
    s = urllib.parse.unquote(s)
    return base64.b64decode(s).decode(encoding="utf-8")
    # return s


def data_to_str(data: object):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)


def str_to_data(s: str):
    return json.loads(s) if s else None


def parse_datetime(datetime):
    return [int(x) for x in filter(lambda s: len(s) <= 4, re.split('[-:/ .]', str(datetime)))]


def cur_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


