from django.views import View
from meta_config import HELL_WORDS

class HellWords(View):
    @JSR('words', 'status')
    def get(self, request):
        return HELL_WORDS, 0
