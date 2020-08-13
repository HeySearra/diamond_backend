BASIC_DATA_MAX_LEN = 64
EXT_DATA_MAX_LEN = 256

ENT_TYPE_CHS = (
    ('fold', '文件夹'),
    ('doc', '文档'),
)
ENT_TYPE_DICT = {e[0]: e[1] for e in ENT_TYPE_CHS}
