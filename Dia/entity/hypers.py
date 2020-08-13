from easydict import EasyDict as ED

BASIC_DATA_MAX_LEN = 128
EXT_DATA_MAX_LEN = 256

ENAME_MAX_LEN = 64

ENT_TYPE_CHS = (
    ('fold', '文件夹'),
    ('doc', '文档'),
)
ENT_TYPE = ED()
ENT_TYPE.fold = 'fold'
ENT_TYPE.doc = 'doc'

CHECK_ENAME = lambda d: 0 <= len(d) <= ENAME_MAX_LEN
