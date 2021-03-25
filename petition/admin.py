from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Petition)
admin.site.register(PetitionField)
admin.site.register(PetitionFieldEntry)
admin.site.register(Signature)