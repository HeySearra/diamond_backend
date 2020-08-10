from django.db import models



class Complain(models.Model):
    # 它的功能是举报
    content = models.CharField(verbose_name="举报理由", max_length=512, default='')
    condition = models.BooleanField(verbose_name='被处理', default=False)
    result = models.BooleanField(verbose_name='处理结果', default=False)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    owner = models.ForeignKey('user.User', related_name='complain_owner', verbose_name="举报者", on_delete=models.CASCADE)
    handler = models.ForeignKey('user.User', related_name='complain_handler', verbose_name="处理者", null=True, on_delete=models.CASCADE)
    
    article = models.ForeignKey('article.Article', null=True, on_delete=models.CASCADE)
    resource = models.ForeignKey('resource.Resource', null=True, on_delete=models.CASCADE)
    article_comment = models.ForeignKey('article.ArticleComment', null=True, on_delete=models.CASCADE)
    resource_comment = models.ForeignKey('resource.ResourceComment', null=True, on_delete=models.CASCADE)
    user = models.ForeignKey('user.User', null=True, on_delete=models.CASCADE)


class Tag(models.Model):
    name = models.CharField(verbose_name="标签名", max_length=256, default='')
    article = models.ManyToManyField('article.Article', related_name='tagged_article')
    resource = models.ManyToManyField('resource.Resource', related_name='tagged_resource')


class Collection(models.Model):
    name = models.CharField(verbose_name="收藏夹名", max_length=256, default='')
    total_num = models.IntegerField(verbose_name="收藏内容数量", default=0)
    hide = models.BooleanField(verbose_name='是否隐藏', default=False)
    
    owner = models.ForeignKey('user.User', on_delete=models.CASCADE)
    articles = models.ManyToManyField('article.Article', verbose_name='收藏的文章', related_name='articles_in_collection', through='ArticleCollect')
    resources = models.ManyToManyField('resource.Resource', verbose_name='收藏的资源', related_name='resources_in_collection', through='ResourceCollect')


class ArticleCollect(models.Model):
    time = models.DateTimeField(verbose_name='收藏时间', auto_now_add=True)
    
    user = models.ForeignKey('Collection', on_delete=models.CASCADE)
    article = models.ForeignKey('article.Article', on_delete=models.CASCADE)


class ResourceCollect(models.Model):
    time = models.DateTimeField(verbose_name='收藏时间', auto_now_add=True)
    
    user = models.ForeignKey('Collection', on_delete=models.CASCADE)
    resource = models.ForeignKey('resource.Resource', on_delete=models.CASCADE)


class Message(models.Model):
    # 收到评论才提示，点赞、收藏都不提示
    # 举报被处理
    owner = models.ForeignKey(to='user.User', related_name="message_owner", on_delete=models.CASCADE)
    article_comment = models.ForeignKey(to='article.ArticleComment', related_name="article_comment_message", null=True, on_delete=models.CASCADE)
    resource_comment = models.ForeignKey(to='resource.ResourceComment', related_name="resource_comment_message", null=True, on_delete=models.CASCADE)
    complain = models.ForeignKey(to=Complain, related_name='complain_message', null=True, on_delete=models.CASCADE)
    condition = models.BooleanField(default=False, verbose_name="是否已读")
    time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    message = models.CharField(verbose_name='消息内容', max_length=512, default='')
