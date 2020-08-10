from typing import Set, Dict
from django.http import JsonResponse


class QueryMethod(object):
    
    def __init__(self, expected_keys: Set[str], status_map: Dict[str, str]):
        self.expected_keys, self.status_map = expected_keys, status_map
        
    def __call__(self, request) -> JsonResponse:
        raise NotImplementedError
