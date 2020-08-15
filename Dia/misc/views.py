from django.views import View
from meta_config import HELL_WORDS
from utils.meta_wrapper import JSR

# for ckeditor image upload
from Dia import settings
import random
import string
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


