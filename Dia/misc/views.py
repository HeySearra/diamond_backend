from django.views import View

from entity.models import Entity
from meta_config import HELL_WORDS
from user.models import User
from utils.meta_wrapper import JSR
from misc.models import *
from easydict import EasyDict as ED

# for ckeditor image upload
from Dia import settings
import random
import string
import json
from user.hypers import *


class HellWords(View):
    @JSR('words', 'status')
    def get(self, request):
        return HELL_WORDS, 0


class UploadImg(View):
    @JSR('code', 'url')
    def post(self, request):
        print('receive img')
        file = request.FILES.get('img')
        file_name = ''.join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + \
                    str(file.name).split(".")[-1]
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        print(request.FILES.get('img'))
        return 0, 'http://localhost:8000/store/' + file_name


class FSShareKey(View):
    def get_key(self, type):
        key = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)])
        if type == 'write':
            if WriteAuth.objects.filter(key=key).exists():
                return self.get_key('write')
        elif type == 'comment':
            if CommentAuth.objects.filter(key=key).exists():
                return self.get_key('comment')
        elif type == 'read':
            if ReadAuth.objects.filter(key=key).exists():
                return self.get_key('read')
        return key

    @JSR('status', 'key')
    def post(self, request):
        E = ED()
        E.u, E.k, E.au, E.update = -1, 1, 2, 3
        if not request.session.get('is_login', False):
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'auth'}:
            return E.k
        did = kwargs.get('did')
        auth = kwargs.get('auth')
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.k

        wa = WriteAuth.objects.filter(ent=e)
        if not wa.exists():
            wa = WriteAuth.objects.create(ent=e)
            wa.user.add(e.creator)
            wa.key = self.get_key('write')
            wa.save()
        else:
            wa = wa.get()

        if auth == 'write':
            if u not in wa.user.all():
                return E.au, ''
            else:
                return 0, wa.key
        if auth == 'comment':
            ca = CommentAuth.objects.filter(ent=e)
            if not ca.exists():
                ca = CommentAuth.objects.create(ent=e)
                ca.key = self.get_key('comment')
                ca.save()
            else:
                ca = ca.get()
            if u not in ca.user.all() and u not in wa.user.all():
                return E.au, ''
            else:
                return 0, ca.key
        if auth == 'read':
            ra = ReadAuth.objects.filter(ent=e)
            if not ra.exists():
                ra = ReadAuth.objects.create(ent=e)
                ra.key = self.get_key('read')
                ra.save()
            else:
                ra = ra.get()
            ca = CommentAuth.objects.filter()
            if (ca.exists() and u in ca.get().user.all()) or u in ra.user.all() or u in wa.user.all():
                return 0, ra.key
            else:
                return E.au, ''
        return E.k, ''

