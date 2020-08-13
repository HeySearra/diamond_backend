from django.db import models

# Create your models here.
from entity.models import Entity
from user.models import User
from teamwork.hypers import *


class Team(models.Model):
    root = models.ForeignKey(to='entity.Entity', related_name='root_team', on_delete=models.CASCADE)
    name = models.CharField(verbose_name='团队名', max_length=64, default='未命名', blank=True)
    intro = models.CharField(verbose_name='团队介绍', max_length=1024, default='这个团队很懒，暂时还没有介绍~', blank=True)
    img = models.ImageField(verbose_name='团队头像', upload_to='', default='', blank=True)
    create_dt = models.DateTimeField(verbose_name='团队创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-create_dt']


class Member(models.Model):
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    member = models.ForeignKey(to=User, on_delete=models.CASCADE)
    auth = models.CharField(verbose_name='个人权限', choices=TEAM_AUTH_CHS, default='member', max_length=AUTH_MAX_LENGTH)
    join_dt = models.DateTimeField(verbose_name='参与团队时间', auto_now_add=True)
