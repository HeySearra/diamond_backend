import json
import time
import functools
import traceback
from datetime import datetime
import random
from string import ascii_uppercase

from django.http import JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from colorama import Fore, Back

import meta_config
from pprint import pprint, pformat
from typing import List
from collections import OrderedDict


def JSR(*keys):
    def decorator(req_func):
        @functools.wraps(req_func)
        def wrapper(*args, **kw):
            req_type, func_name = '', ''
            debug = meta_config.DEBUG and len(args) == 2
            # user.UnreadCount.GET
            self, request = args
            req_type = req_func.__name__.upper()
            # req_type = 'POST' if hasattr(request, 'body') and len(request.body) > 0 else 'GET'
            func_name: str = meta_config.CLS_PARSE_REG.findall(str(type(self)))[0].replace(".views.", ".")
            func_name = '' if len(func_name) < 2 else func_name
            func_name += f'.{req_type}'
            # func_name += f'.{req_type} ({random.choice(ascii_uppercase) + random.choice(ascii_uppercase)})'
            # func_name += '.' + req_type.lower()

            # print(Fore.BLUE + f'[{req_type}] called: {func_name}')
            if req_type == 'POST':
                try:
                    inputs = pformat(json.loads(request.body))
                except:
                    inputs = '[cannot preview body]'
            else:  # req_type == 'GET':
                inputs = f'session: {pformat(dict(request.session))}'
                if len(dict(request.GET).keys()):
                    inputs += f', GET: {pformat(dict(request.GET))}'

            prev_time = time.time()
            try:
                values = req_func(*args, **kw)
            except Exception as e:
                time_cost = time.time() - prev_time
                time.sleep(0.2)
                print(Fore.MAGENTA + f'[{func_name}] ====! FATAL ERR !==== : {e}, {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                                     f'\n input: {inputs}, time: {time_cost:.2f}s')
                time.sleep(0.2)
                # traceback.print_exc()
                raise e
            else:
                time_cost = time.time() - prev_time
                values = list(values) if isinstance(values, (tuple, list)) else [values]
                # values = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else x, values))
                [values.append('') for _ in range(len(keys) - len(values))]
                ret_dict = dict(zip(keys, values))
                if debug and func_name != 'user.UnreadCount.GET':
                    c = Fore.RED if ret_dict.get('status', 0) else Fore.GREEN
                    print(c + f'[{func_name}] input: {inputs}\n ret: {pformat(ret_dict)}, time: {time_cost:.2f}s')
                return JsonResponse(ret_dict)

        return wrapper

    return decorator
