from collections import namedtuple

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
