from django.db import models
# Create your models here.
from django.db.models import QuerySet

from meta_config import *
from teamwork.hypers import TEAM_MEM, TEAM_NAME_MAX_LENGTH, TEAM_INTRO_MAX_LENGTH, TEAM_AUTH_CHS, AUTH_MAX_LENGTH, \
    TEAM_MEM_CHS
from user.models import User
from utils.cast import encode, decode


class Team(models.Model):
    @staticmethod
    def get_via_encoded_id(encoded_id):
        t: QuerySet = Team.objects.filter(id=int(decode(encoded_id)))
        return t.get() if t.exists() else None

    @property
    def encoded_id(self):
        return encode(self.id)

    @property
    def owner(self):
        return Member.objects.filter(team=self, auth=TEAM_MEM.owner).get().member

    def contains_user(self, user_or_raw_id):
        d = user_or_raw_id.id if isinstance(user_or_raw_id, User) else user_or_raw_id
        return self.member_set.filter(member_id=d).exists()

    root = models.ForeignKey(to='entity.Entity', related_name='root_team', on_delete=models.CASCADE, null=True)
    name = models.CharField(verbose_name='团队名', max_length=TEAM_NAME_MAX_LENGTH+1, default='未命名', blank=True)
    intro = models.CharField(verbose_name='团队介绍', max_length=TEAM_INTRO_MAX_LENGTH, default='这个团队很懒，暂时还没有介绍~', blank=True)
    portrait = models.CharField(verbose_name='团队头像', blank=True, null=True, default='', max_length=512)
    create_dt = models.DateTimeField(verbose_name='团队创建时间', auto_now_add=True)

    @property
    def create_dt_str(self):
        return self.create_dt.strftime(TIME_FMT)

    class Meta:
        ordering = ['-create_dt']


class Member(models.Model):
    @staticmethod
    def get_members_via_member_encoded_id(member_encoded_id):
        m: QuerySet = Member.objects.filter(member_id=int(decode(member_encoded_id)))
        return m

    @property
    def encoded_id(self):
        return encode(self.id)

    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    member = models.ForeignKey(to=User, on_delete=models.CASCADE)
    membership = models.CharField(verbose_name='身份', choices=TEAM_MEM_CHS, default='member', max_length=AUTH_MAX_LENGTH)
    auth = models.CharField(verbose_name='个人权限', choices=TEAM_AUTH_CHS, default='wirte', max_length=AUTH_MAX_LENGTH)
    join_dt = models.DateTimeField(verbose_name='参与团队时间', auto_now_add=True)
