from collections import namedtuple

from entity.models import Entity
from user.models import User

AUTH_MAX_LENGTH = 20

TEAM_AUTH_CHS = (
    ('owner', '创建者'),
    ('admin', '管理员'),
    ('member', '普通成员'),
)
TEAM_AUTH = namedtuple('___', ['owner', 'admin', 'member'])('owner', 'admin', 'member')

DOC_AUTH_CHS = (
    ('write', '可编辑'),
    ('comment', '可评论'),
    ('read', '只读'),
)
DOC_AUTH = namedtuple('___', ['write', 'comment', 'read'])('write', 'comment', 'read')

TEAM_NAME_MAX_LENGTH = 64
TEAM_INTRO_MAX_LENGTH = 1024


def check_auth(user: User, ent: Entity, auth: str) -> bool:
    if ent.first_person(user):
        return True
    if ent.is_locked:
        return False
    
    assert auth in list(zip(*DOC_AUTH_CHS))[0]
    
    if auth == 'write':
        ...
    ...

