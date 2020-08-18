from collections import namedtuple

BASIC_DATA_MAX_LEN = 128
EXT_DATA_MAX_LEN = 256

ENAME_MAX_LEN = 64
COMMENT_MAX_LEN = 2048

ENT_TYPE_CHS = (
    ('fold', '文件夹'),
    ('doc', '文档'),
)
ENT_TYPE = namedtuple('___', ['fold', 'doc'])('fold', 'doc')

CHECK_ENAME = lambda d: 0 <= len(d) <= ENAME_MAX_LEN and any(ch.isprintable() for ch in d)
CHECK_COMMENT = lambda d: 0 <= len(d) <= COMMENT_MAX_LEN
