import json

from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from django.views import View
from easydict import EasyDict as ED
from easydict import EasyDict
from entity.hypers import BASIC_DATA_MAX_LEN
from entity.models import Entity
from utils.cast import decode, encode, cur_time
from utils.meta_wrapper import JSR
from user.models import User
from chat.models import Chat


class ChatList(View):
    @JSR('list', 'status')
    def get(self, request):

        E = ED()
        E.u, E.k, E.au = -1, 1, 2

        if not request.session.get('is_login', False):
            return [], E.au

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return [], E.au
        u = u.get()

        chats = Chat.objects.filter(Q(user1_id=u.id) | Q(user2_id=u.id)).order_by('-send_time')

        another_users = []
        for chat in chats:
            if chat.user1_id == u.id and (chat.user2_id not in another_users):
                another_users.append(chat.user2_id)
            if chat.user2_id == u.id and (chat.user1_id not in another_users) and chat.content != '':
                another_users.append(chat.user1_id)

        chatlist = []
        for another_user in another_users:
            chat = Chat.objects.filter((Q(user1_id=u.id) & Q(user2_id=another_user)) | (Q(user1_id=another_user) & Q(user2_id=u.id))).order_by('send_time')
            is_read = True
            for c in chat:
                if (not c.is_read) and (c.user2_id == u.id):
                    is_read = False
            try:
                print(chat.count())
                last_message = chat.last().content
            except:
                return [], E.u
            ano_u = User.objects.filter(id=another_user)
            if not ano_u.exists():
                return [], -1
            ano_u = ano_u.get()
            name = ano_u.name
            src = ano_u.portrait
            chatlist.append({
                'uid': encode(another_user),
                'is_read': is_read,
                'last_message': last_message,
                'name': name,
                'src': src
            })
        return chatlist, 0


class ChatContent(View):
    @JSR('cur_dt', 'user_info', 'another_info', 'list', 'status')
    def get(self, request):

        E = ED()
        E.u, E.k, E.au = -1, 1, 2

        if not request.session.get('is_login', False):
            return '', {}, {}, [], E.au

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return '', {}, {}, [], E.au
        u = u.get()

        anotheru = User.objects.filter(id=int(decode(request.GET.get('uid'))))
        if not anotheru.exists():
            return '', {}, {}, [], E.au
        anotheru = anotheru.get()

        user_info = {'uid': encode(u.id), 'src': u.portrait}
        another_info = {'uid': encode(anotheru.id), 'src': anotheru.portrait}
        chats = Chat.objects.filter(Q(user2_id=u.id) & Q(user1_id=anotheru.id))
        for chat in chats:
            chat.is_read = True
            chat.save()

        chatlist = []
        chats = Chat.objects.filter((Q(user1_id=u.id) & Q(user2_id=anotheru.id)) | (Q(user1_id=anotheru.id) & Q(user2_id=u.id))).order_by('send_time')
        for chat in chats:
            if chat.content != '':
                chatlist.append({
                    'is_mine': True if chat.user1_id == u.id else False,
                    'dt': chat.dt_str,
                    'text': chat.content
                })
        return cur_time(), user_info, another_info, chatlist, 0


class SendChat(View):
    @JSR('status')
    def post(self, request):

        E = ED()
        E.u, E.k, E.au = -1, 1, 2

        if not request.session.get('is_login', False):
            return E.au

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'uid', 'text'}:
            return E.k

        u1 = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u1.exists():
            return E.au
        u1 = u1.get()

        u2 = User.objects.filter(id=int(decode(kwargs['uid'])))
        if not u2.exists():
            return E.au
        u2 = u2.get()

        try:
            Chat.objects.create(user1=u1, user2=u2, content=kwargs['text'], send_time=cur_time())
        except:
            return E.u

        return 0


# 未读私信数量
class ChatCount(View):
    @JSR('count', 'status')
    def get(self, request):

        E = ED()
        E.u, E.k, E.au = -1, 1, 2

        if not request.session.get('is_login', False):
            return 0, E.au

        try:
            u = User.objects.filter(id=int(decode(request.session['uid'])))
        except:
            uid = request.session['uid'].decode() if isinstance(request.session['uid'], bytes) else request.session['uid']
            u = User.objects.filter(id=int(uid))

        if not u.exists():
            return 0, 2
        u = u.get()
        request.session['uid'] = encode(u.id)
        request.session.save()
        return Chat.objects.filter(Q(user2_id=u.id) & Q(is_read=False)).count(), 0


class BuildChat(View):
    @JSR('status')
    def post(self, request):

        E = ED()
        E.u, E.k, E.au, E.acc = -1, 1, 2, 3

        if not request.session.get('is_login', False):
            return E.au

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'uid'}:
            return E.k

        uto = User.objects.filter(id=int(decode(kwargs['uid'])))
        if not uto.exists():
            return E.au
        uto = uto.get()

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return E.au
        u = u.get()

        Chat.objects.create(user1=u, user2=uto, content='', send_time=cur_time())
        return 0
