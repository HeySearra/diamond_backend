from django.db import models

# Create your models here.
from entity.models import Entity
from teamwork.hypers import *
from user.models import User
from utils.cast import encode, decode


class Team(models.Model):
    @staticmethod
    def get_via_encoded_id(encoded_id):
        return Team.objects.get(id=int(decode(encoded_id)))

    @property
    def encoded_id(self):
        return encode(self.id)

    root = models.ForeignKey(to='entity.Entity', related_name='root_team', on_delete=models.CASCADE)
    name = models.CharField(verbose_name='团队名', max_length=TEAM_NAME_MAX_LENGTH, default='未命名', blank=True)
    intro = models.CharField(verbose_name='团队介绍', max_length=TEAM_INTRO_MAX_LENGTH, default='这个团队很懒，暂时还没有介绍~', blank=True)
    img = models.ImageField(verbose_name='团队头像', upload_to='', default='', blank=True)
    create_dt = models.DateTimeField(verbose_name='团队创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-create_dt']


class Member(models.Model):
    @staticmethod
    def get_via_encoded_id(encoded_id):
        return Member.objects.get(id=int(decode(encoded_id)))

    @property
    def encoded_id(self):
        return encode(self.id)

    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    member = models.ForeignKey(to=User, on_delete=models.CASCADE)
    auth = models.CharField(verbose_name='个人权限', choices=TEAM_AUTH_CHS, default='member', max_length=AUTH_MAX_LENGTH)
    join_dt = models.DateTimeField(verbose_name='参与团队时间', auto_now_add=True)
