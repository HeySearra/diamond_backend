TEAM_AUTH_CHS = (
    ('owner', '创建者'),
    ('admin', '管理员'),
    ('member', '普通成员'),
)
TEAM_AUTH_DICT = {e[0]: e[1] for e in TEAM_AUTH_CHS}
AUTH_MAX_LENGTH = 20

AUTH_CHS = (
    ('write', '可编辑'),
    ('comment', '可评论'),
    ('read', '只读'),
)
AUTH_DICT = {e[0]: e[1] for e in AUTH_CHS}

TEAM_NAME_MAX_LENGTH = 64
TEAM_INTRO_MAX_LENGTH = 1024
