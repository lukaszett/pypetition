from django.forms import Form, EmailField, CharField, ChoiceField, IntegerField, BooleanField
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from .validators import unique_email_validator

from .util import hash_email

from .models import Signature, PetitionFieldEntry

# dynamic generation of form at runtime 
# see https://jacobian.org/2010/feb/28/dynamic-form-generation/
class SignPetitionForm(Form):
    vorname = CharField(label="Vorname", required=True)
    name = CharField(label="Name", required=True)
    email = EmailField(label="Email", required=True, validators=[unique_email_validator])
    stay_informed = BooleanField(label="Newsletter abonnieren", required=False)

    def __init__(self, petition, *args, **kwargs):
        super(SignPetitionForm, self).__init__(*args, **kwargs)
        
        self.petition = petition
        extra = petition.fields.order_by("-order").all()

        for field in extra:
            # add extra field to form
            custom_field = CharField(label=field.label, required=field.required)

            # Email Field
            if(field.validator == "EM"):
                custom_field = EmailField()

            # MaxLength-Validator
            if(field.validator == "ML"):
                custom_field = CharField(max_length=field.validator_max_len)

            # Regexp-Validator
            if(field.validator == "RE"):
                custom_field = CharField(validators=RegexValidator(regex=field.validator_regexp_key))

            # Integer-Validator
            if(field.validator == "IN"):
                custom_field = IntegerField(max_value= field.validator_int_max, min_value= field.validator_int_min)

            # Choices-Validator
            if(field.validator == "CH"):
                # get list from comma seperated choices
                choices = field.validator_choice_keys.split(",")

                choices_tuples = []
                for i in range(len(choices)):
                    choices_tuples.append((choices[i].strip(), choices[i].strip()))

                custom_field = ChoiceField(choices=choices_tuples)

            custom_field.label = field.label
            custom_field.required = field.required

            self.fields[f"field_{field.slug}"] = custom_field

        # move stay_informed checkbox to the end of signing form
        stay_informed = self.fields.pop("stay_informed")
        self.fields["stay_informed"]=stay_informed


    def on_valid(self, request):
        fields = self.petition.fields.all()

        email = self.cleaned_data["email"]
        email_hash = hash_email(email)

        # add new signature
        signature = Signature(petition=self.petition,
                            email_hash = email_hash,
                            name=self.cleaned_data["name"],
                            vorname=self.cleaned_data["vorname"],
                            stay_informed=self.cleaned_data["stay_informed"])
        signature.save()

        # add a new petitionfield entry for each filled formfield
        entries = []
        for field in fields:
            key = f"field_{field.slug}"
            value = self.cleaned_data[key]
            if value:
                entries.append(PetitionFieldEntry(
                    field=field,
                    signature=signature,
                    value=value,
                ))
        # ... then bulkcreate them all to save som queries
        PetitionFieldEntry.objects.bulk_create(entries)


        if self.petition.require_mail_confirmation:
            # create confirmation url for the created signature
            confirm_url = settings.HOST + "" + reverse("confirm", kwargs={"pk":signature.id})

            messages.info(request, "Du musst deine E-Mail-Adresse noch verifizieren. Wir haben dir hierfür eine Mail geschrieben.")

            # send mail to the creater of this signature
            send_mail(
                subject="Bitte bestätige deine Unterschrift!",
                message=f"{confirm_url}",
                from_email=None,
                recipient_list=[email]
            )
        
        # if the signee wants to stay informed we safe the email
        # otherwise it gets discarded and we just keep the hash generated above
        if signature.stay_informed:
            signature.email = email
            signature.save()