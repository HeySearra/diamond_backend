from django.db import models

# Create your models here.
class Collection(models.Model):
    user = models.ForeignKey('user.User', related_name='related_collection', on_delete=models.CASCADE)
    ent = models.ForeignKey('entity.Entity', related_name='ent', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True, verbose_name='文件收藏时间')