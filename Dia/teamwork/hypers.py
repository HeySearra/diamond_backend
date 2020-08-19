from collections import namedtuple

AUTH_MAX_LENGTH = 20
TEAM_MEM_CHS = (
    ('owner', '创建者'),
    ('admin', '管理员'),
    ('member', '普通成员')
)
TEAM_AUTH_CHS = (
    ('write', '写'),
    ('comment', '评论'),
    ('read', '读'),
)
TEAM_AUTH = namedtuple('___', ['owner', 'admin', 'member'])('owner', 'admin', 'member')

DOC_AUTH_CHS = (
    ('write', '可编辑'),
    ('comment', '可评论'),
    ('read', '只读'),
)
DOC_AUTH = namedtuple('___', ['write', 'comment', 'read', 'none'])('write', 'comment', 'read', 'none')

AUTH_DICT = namedtuple('___', ['write', 'comment', 'read', 'none'])(4, 3, 2, 1)

TEAM_NAME_MAX_LENGTH = 60
TEAM_INTRO_MAX_LENGTH = 1024

CHECK_TEAM_NAME = lambda d: 0 < len(d) <= TEAM_NAME_MAX_LENGTH and d.isprintable()
CHECK_TEAM_INTRO = lambda d: 0 < len(d) <= TEAM_INTRO_MAX_LENGTH and d.isprintable()
