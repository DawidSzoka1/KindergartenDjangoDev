from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegisterForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import User
from director.models import Director, ContactModel, Kindergarten
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Register(View):
    def get(self, request):
        if request.user.is_active:
            messages.info(request, 'Masz juz konto')
            return redirect('home_page')
        form = UserRegisterForm()
        return render(request, "register.html", {'form': form})

    def post(self, request):
        if request.user.is_active:
            messages.info(request, 'Masz juz konto')
            return redirect('home_page')
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            k_name = form.cleaned_data.get('kindergarten_name')
            user = User.objects.filter(email=email).first()
            if not user:
                # Jeśli użytkownik nie istnieje, tworzymy go standardowo
                user = form.save()
                new_director = user.director_profiles.first()
                kindergarten = new_director.kindergarten
                kindergarten.name = k_name
                kindergarten.save()
                messages.success(request, 'Konto zostało utworzone.')
            else:
                # Jeśli użytkownik istnieje, sprawdzamy czy już jest dyrektorem
                kindergarten = Kindergarten.objects.create(name=k_name)
                new_director = Director.objects.create(user=user, kindergarten=kindergarten)
                ContactModel.objects.create(director=new_director, kindergarten=kindergarten, email_address=email)

                # Upewniamy się, że ma uprawnienia dyrektora
                content_type = ContentType.objects.get_for_model(Director)
                perm = Permission.objects.get(content_type=content_type, codename='is_director')
                user.user_permissions.add(perm)

                messages.success(request, f'Dodano nową placówkę {k_name} do Twojego konta.')

            # 2. Inicjalizacja sesji, aby użytkownik wszedł jako Dyrektor
            request.session['active_role'] = 'director'
            request.session['active_kindergarten_id'] = kindergarten.id

            return redirect('login')
        else:
            messages.error(request, "W formularzu wystąpiły błędy. Sprawdź pola.")
        return render(request, "register.html", {'form': form})


class ProfilePasswordUpdate(LoginRequiredMixin, View):
    def get(self, request):

        password_form = PasswordChangeForm(request.user)

        context = {
            'password_form': password_form,
        }
        return render(request, 'change_password.html', context)

    def post(self, request):
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)

            return redirect('home_page')
        messages.error(request, 'wypelnij poprawnie formularz')
        return redirect('password_change')
