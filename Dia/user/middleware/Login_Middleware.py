from django.shortcuts import redirect, render
from django.shortcuts import reverse
from django.utils.deprecation import MiddlewareMixin
from user.models import User


class IsLogin(MiddlewareMixin):
    list = [
        '/captcha', '/register', '/administrator',
        '/resources', '/question',      # for android user, still developing...
        '/test',        # for developer to test new function remember to remove it when start server
        '/android/login', '/login', '/administrator',
        '/admin/', '/administrator',
    ]

    login = [
        '/',
        '/simple_user_info',
        '/article_view_card',
        '/register/submit',
        '/login/submit',
        '/index/recommend',
        '/base',
        '/search',
        '/collection/list',
        '/collection/info',
        '/side/user_info',
        '/article/all',
        '/resource/all',
        '/article/comment',
        '/resource/comment',
        '/comment/all',
        '/administrator',
    ]

    access_check_list = [
        '/administrator',
    ]

    def process_view(self, request, callback, callback_args, callback_kwargs):
        print("path:", request.path)
        # print("is_login:", request.session.get('is_login', None))
        # print(request.session.get('user_id'))
        # print(request.META.get('HTTP_USER_AGENT'))
        # print("session_key:", request.session.session_key)
        for s in IsLogin.login:
            if request.path.startswith(s):
                return callback(request, *callback_args, **callback_kwargs)
        for s in IsLogin.access_check_list:
            if request.path.startswith(s) and not request.session.get('permissions', None) in ['vip', 'admin']:
                return redirect(reverse('index'))
        if request.session.get('is_login'):
            try:
                user = User.objects.get(id=request.session.get('user_id'))
            except:
                for s in IsLogin.login:
                    if request.path.startswith(s):
                        return callback(request, *callback_args, **callback_kwargs)
                for s in IsLogin.access_check_list:
                    if request.path.startswith(s) and not request.session.get('permissions', None) in ['admin', 'teacher', 'assistant']:
                        return redirect(reverse('index'))
                user = None
                request.session.flush()
            if user is None or (request.session.session_key != user.session_key and user.session_key != ''):
                request.session.flush()
                return redirect(reverse('index'))
        if request.session.get('is_login', None) is None:
            return redirect(reverse('index'))
        return callback(request, *callback_args, **callback_kwargs)
