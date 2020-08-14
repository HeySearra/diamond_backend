import json
import time
import functools
from datetime import datetime

from django.http import JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from colorama import Fore, Back

import meta_config
from pprint import pprint, pformat
from typing import List
from collections import OrderedDict


# todo: auto decoder of id
def JSR(*keys):
    def decorator(req_func):
        @functools.wraps(req_func)
        def wrapper(*args, **kw):
            req_type, func_name = '?', '?'
            debug = meta_config.DEBUG and len(args) == 2
            if debug:
                obj, request = args
                func_name: str = meta_config.CLS_PARSE_REG.findall(str(type(obj)))[0]
                func_name = f'{func_name[:func_name.find(".")]}, {func_name[func_name.rfind(".") + 1:]}'
                func_name = '?' if len(func_name) < 2 else func_name
                req_type = 'POST' if hasattr(request, 'body') and len(request.body) > 0 else 'GET'
                # func_name += '.' + req_type.lower()
                
                # print(Fore.BLUE + f'[{req_type}] called: {func_name}')
                if req_type == 'POST':
                    try:
                        body_str = pformat(json.loads(request.body))
                    except:
                        body_str = '[cannot preview body]'
                    para_from_frontend = f'[{req_type}, {func_name}] body: {body_str}'
                else:  # req_type == 'GET':
                    para_from_frontend = f'[{req_type}, {func_name}] session: {pformat(dict(request.session))}'
                    if len(dict(request.GET).keys()):
                        para_from_frontend += f', GET: {pformat(dict(request.GET))}'
                print(Fore.BLUE + para_from_frontend)
            prev_time = time.time()
            values = req_func(*args, **kw)
            time_cost = time.time() - prev_time
            values = list(values) if isinstance(values, (tuple, list)) else [values]
            # values = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else x, values))
            [values.append('') for _ in range(len(keys) - len(values))]
            ret_dict = dict(zip(keys, values))
            if debug:
                c = Fore.RED if ret_dict.get('status', 0) else Fore.GREEN
                print(c + f'[{req_type}, {func_name}] ret: {pformat(ret_dict)}, time: {time_cost:.2f}s')
            return JsonResponse(ret_dict)
        
        return wrapper
    
    return decorator
