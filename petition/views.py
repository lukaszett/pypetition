from django.shortcuts import render,redirect
from django.views.generic import DetailView
from django.contrib import messages
from .models import Petition, PetitionFieldEntry, PetitionField, Signature
from .forms import SignPetitionForm

class ConfirmMailView(DetailView):
    model = Signature

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.confirmed=True
        self.object.save()
        messages.success(request, "Du hast deine E-Mail-Adresse bestätigt.")
        return redirect('petition', slug=self.object.petition.slug)

# Create your views here.
class PetitionView(DetailView):
    model = Petition
    template_name = "petition/petition.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_object = context["object"]
        # if we return from a failed attempt at posting the form-key is already set and has some errors attached
        if not "form" in context:
            context["form"] = SignPetitionForm(detail_object)
        context["n_signatures"] = detail_object.get_n_signatures()
        context["recent_signatures"] = detail_object.get_recent_signatures()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SignPetitionForm(self.get_object(),request.POST)
        if form.is_valid():
            form.on_valid(request)
        else:
            messages.warning(request, "Da hat etwas nicht geklappt. Bitte überprüfe deine Eingaben.")
        context = self.get_context_data()
        context.update({"form":form})
        return self.render_to_response(context)