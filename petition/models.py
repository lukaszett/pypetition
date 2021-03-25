from django.db import models
from django import forms
import uuid
from .util import hash_email


class PetitionField(models.Model):
    REGEXP = "RE"
    EMAIL = "EM"
    NONE ="NO"
    CHOICE = "CH"
    MAXLEN = "ML"
    INT = "IN"

    VALIDATOR_CHOICES = [
        (REGEXP, "Regexp"),
        (EMAIL, "Email"),
        (CHOICE, "Auswahl"),
        (NONE, "Keiner"),
        (MAXLEN, "Maximale Länge"),
        (INT, "Zahl")
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.IntegerField(default=0, blank=False)
    label = models.CharField(max_length=200, blank=False)
    slug = models.SlugField(blank=False)
    validator = models.CharField(max_length=2, choices=VALIDATOR_CHOICES, default=NONE)
    help_text = models.CharField(max_length=250, blank=True)
    unique = models.BooleanField(default=False)
    required = models.BooleanField(default=False)

    show_in_recent_signatures = models.BooleanField(default=False)
    
    validator_regexp_key = models.TextField(default="*", blank=False)
    validator_choice_keys = models.TextField(default = "eintrag 1, eintrag 2", blank=False)
    validator_max_len = models.IntegerField(default=100, blank=False)
    validator_int_min = models.IntegerField(default=0, blank=False)
    validator_int_max = models.IntegerField(default=100, blank=False)

    def __str__(self):
        return self.label


# Create your models here.
class Petition(models.Model):
    slug = models.SlugField(blank=False, primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=False)
    require_mail_confirmation = models.BooleanField(default=True)
    fields = models.ManyToManyField(PetitionField, blank=True)
    custom_css = models.TextField(blank=True)
    n_recent_signatures = models.IntegerField(default=15)

    def __str__(self):
        return self.title

    def get_field_entries(self, only_confirmed=True, show_in_recent=False, limit=-1):
        # get all signatures for petition
        signatures = self.signatures.order_by("-timestamp")
        # preload all fields for petition
        fields = self.fields.order_by("order")
        slugs = fields.values("slug")

        # only show confirmed signatures?
        if only_confirmed:
            signatures = signatures.filter(confirmed=True)

        if limit != -1:
            signatures = signatures[:limit]

        # if show_in_recent is true, we only return fields tagged as "show_in_recent"
        if show_in_recent:
            fields = fields.filter(show_in_recent_signatures=True)

        # save all entries for petition in dict, this way we dont have to run anymore queries
        entries = PetitionFieldEntry.objects.filter(signature__petition = self, signature__in=signatures, field__in = fields).values()
              
        signature_data_list = []
        for signature in signatures:
            signature_data = {
                "confirmed": signature.confirmed,
                "timestamp": str(signature.timestamp),
                "public_name": signature.public_name,
            }

            if not show_in_recent:
                signature_data.update({
                    "name": signature.name,
                    "vorname": signature.vorname,
                    "email": signature.email,
                })
            if fields:
                signature_data["data"] = {}
            for field in fields:
                field_entry = list(filter(
                    lambda x: x["field_id"]==field.id and x["signature_id"]==signature.id,
                    entries
                ))
                try:
                    signature_data["data"][field.slug] = field_entry.pop()["value"]
                except:
                    pass
            signature_data_list.append(signature_data)
        
        return signature_data_list

    def get_all_signatures(self):
        signatures = self.signatures
        if self.require_mail_confirmation:
            signatures = signatures.filter(confirmed=True)
        else:
            signatures = signatures.all()
        return signatures

    def get_recent_signatures(self):
        # filter signatures depending on required mail confirmation
        signatures = self.get_field_entries(show_in_recent=True,only_confirmed=self.require_mail_confirmation,limit=self.n_recent_signatures)
        return signatures

    def get_n_signatures(self):
        return self.get_all_signatures().count()
    

class Signature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE, related_name="signatures")
    email = models.EmailField(blank=True)
    email_hash = models.CharField(max_length=64, editable=False)
    name = models.CharField(max_length=250)
    vorname = models.CharField(max_length=250)
    public_name = models.CharField(max_length=500, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    stay_informed = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.vorname + self.name

    def save(self, *args, **kwargs):
        self.public_name = f"{self.vorname} {self.name[0]}."
        super(Signature, self).save(*args, **kwargs)

    def anonymize_email(self):
        self.email = ""

    def hash_email(self):
        self.email_hash = hash_email(self.email)
    


class PetitionFieldEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(PetitionField, related_name="entries", on_delete=models.CASCADE)
    signature = models.ForeignKey(Signature, related_name="data", on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f"{self.signature.public_name}: {self.field.slug} {self.value}"
    