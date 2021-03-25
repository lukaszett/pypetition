from .models import Signature
from django.core.exceptions import ValidationError
from .util import hash_email

def unique_email_validator(email):
    if Signature.objects.filter(email_hash=hash_email(email)).exists():
        raise ValidationError(
            "Mit dieser E-Mail-Adresse wurde schon unterschrieben."
        )