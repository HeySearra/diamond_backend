from datetime import datetime
from django.db import models

from teamwork.hypers import TEAM_NAME_MAX_LENGTH
from user.hypers import *
from meta_config import TIME_FMT
from utils.cast import encode, decode


class Chat(models.Model):

    @staticmethod
    def get_via_encoded_id(encoded_id):
        e = Chat.objects.filter(id=int(decode(encoded_id)))
        return e.get() if e.exists() and not e.get().backtrace_deleted else None

    @property
    def encoded_id(self) -> str:
        return encode(self.id)

    user1 = models.ForeignKey(to='user.User', related_name='chat_user1', verbose_name="私聊消息发送者", on_delete=models.CASCADE, null=True)
    user2 = models.ForeignKey(to='user.User', related_name='chat_user2', verbose_name="私聊消息接收者", on_delete=models.CASCADE, null=True)
    is_read = models.BooleanField(blank=True, verbose_name='私聊信息是否读取', default=False)
    content = models.TextField(blank=False, verbose_name='私聊消息内容', max_length=512, default='')
    send_time = models.DateTimeField(default=datetime.now, verbose_name='消息发送时间')
