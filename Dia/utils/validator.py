from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class LambdaValidator(object):
    def __init__(self, l, code=0, message=''):
        self.l, self.code, self.message = l, code, message
    
    def __call__(self, *args, **kwargs):
        if not self.l(*args, **kwargs):
            raise ValidationError(f'{self.message}', code=self.code)
