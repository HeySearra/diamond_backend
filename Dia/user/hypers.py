import os
import re
from Dia.settings import MEDIA_ROOT
# choices
# from Cuby.settings import MEDIA_ROOT

GENDER_CHS = (
    ('0', '未知'),
    ('1', '男'),
    ('2', '女'),
)
GENDER_DICT = {e[0]: e[1] for e in GENDER_CHS}
IDENTITY_CHS = (
    ('user', '普通用户'),
    ('vip', '会员'),
    ('admin', '管理员'),
)
MESSAGE_type = (
    ('join', '被邀请加入团队'),
    ('accept', '对方接受或拒绝加入团队的邀请'),
    ('out', '踢出团队'),
    ('dismiss', '解散团队'),
    ('doc', '文档新增评论'),
)
IDENTITY_DICT = {e[0]: e[1] for e in IDENTITY_CHS}
DEFAULT_PROFILE_ROOT = MEDIA_ROOT + '/profile'
MAX_UPLOADED_FSIZE = 500 * 1024
FNAME_DEFAULT_LEN = 20

# constants
MINI_DATA_MAX_LEN = 32
BASIC_DATA_MAX_LEN = 96
EXT_DATA_MAX_LEN = 256
NAME_MAX_LEN = 16
PWD_MIN_LEN = 6
PWD_MAX_LEN = 16
DESC_MAX_LEN = 200
MAX_WRONG_PWD = 5

# checker lambdas
_TEL_REG = r'^[0-9]+$'
_EMAIL_REG = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
_PRINTABLE_UNICODES_WITHOUT_BLANK = lambda s: s.isprintable() and ' ' not in s
_PRINTABLE_ASCIIS_WITHOUT_BLANK = lambda s: _PRINTABLE_UNICODES_WITHOUT_BLANK(s) and all(ord(c) < 128 for c in s)

CHECK_NAME = lambda n: all([
    0 < len(n) <= NAME_MAX_LEN,
    _PRINTABLE_UNICODES_WITHOUT_BLANK(n),
])

_CHECK_EMAIL = lambda e: all([
    0 < len(e) <= MINI_DATA_MAX_LEN,
    _PRINTABLE_ASCIIS_WITHOUT_BLANK(e),
    re.match(_EMAIL_REG, e),
])

_CHECK_TEL = lambda tel: all([
    0 < len(tel) <= MINI_DATA_MAX_LEN,
    all((c.isnumeric() or c == '+' or c == '-') for c in tel),
    re.match(_TEL_REG, tel),
])

CHECK_ACC = lambda acc: _CHECK_EMAIL(acc)

CHECK_PWD = lambda pwd: all([
    PWD_MIN_LEN <= len(pwd) <= PWD_MAX_LEN,
    _PRINTABLE_ASCIIS_WITHOUT_BLANK(pwd),
    any(c.isupper() for c in pwd)
    + any(c.islower() for c in pwd)
    + any(c.isnumeric() for c in pwd)
    + any(not c.isalnum() for c in pwd)
    >= 2
])

CHECK_DESCS = lambda d: 0 <= len(d) <= DESC_MAX_LEN
