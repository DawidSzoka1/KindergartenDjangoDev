from django.core.paginator import Paginator
import json
from children.models import Kid
from teacher.models import Employee
from .forms import ParentUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from director.models import Director, ContactModel
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import ParentA
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import random
import string
from django.conf import settings
from django.db.models import Q, Count
from django.db import transaction
from blog.views import get_active_context


@csrf_exempt
def create_parent_ajax(request):
    role, profile_id, k_id = get_active_context(request)

    if request.method != "POST" or role != 'director':
        return JsonResponse({"success": False, "error": "Brak uprawnień dyrektora"})

    try:
        body = json.loads(request.body)
        email = body.get('email', '').strip().lower()

        if not email or '@' not in email:
            return JsonResponse({"success": False, "error": "Wpisz poprawny e-mail"})

        with transaction.atomic():
            # 1. Pobieramy lub tworzymy użytkownika
            target_user = User.objects.filter(email=email).first()
            created_new_user = False
            password = None

            if not target_user:
                # Tworzymy całkiem nowe konto
                import random, string
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                target_user = User.objects.create_user(email=email, password=password)
                created_new_user = True
            else:
                # Sprawdzamy, czy użytkownik nie ma już profilu rodzica w TEJ placówce
                if ParentA.objects.filter(user=target_user, kindergarten_id=k_id).exists():
                    return JsonResponse({"success": False, "error": "Ten użytkownik jest już rodzicem w tej placówce"})

            # 2. Tworzymy profil ParentA przypisany do placówki (k_id)
            # KindergartenOwnedModel automatycznie obsługuje pole kindergarten_id
            par_profile = ParentA.objects.create(
                user=target_user,
                kindergarten_id=k_id
            )

            # 3. Nadajemy uprawnienie 'is_parent' (bez czyszczenia starych!)
            content_type = ContentType.objects.get_for_model(ParentA)
            permission = Permission.objects.get(content_type=content_type, codename='is_parent')
            if not target_user.has_perm('parent.is_parent'):
                target_user.user_permissions.add(permission)

            # 4. Przygotowanie e-maila
            if created_new_user:
                subject = "Zaproszenie do przedszkola – konto rodzica"
                template = 'email_to_parent.html'
                msg_pass = password
            else:
                subject = "Nowy profil rodzica w systemie"
                template = 'email_to_parent.html' # Informacja o dodaniu profilu do istniejącego konta
                msg_pass = "Twoje dotychczasowe hasło"

            html_content = render_to_string(template, {
                'password': msg_pass,
                'email': email,
                'login_url': f"{request.scheme}://{request.get_host()}",
                'kindergarten_name': par_profile.kindergarten.name
            })

            msg = EmailMultiAlternatives(
                subject,
                f"Twoje konto rodzica w {par_profile.kindergarten.name} jest gotowe.",
                settings.EMAIL_HOST_USER,
                [email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            return JsonResponse({
                "success": True,
                "email": email,
                "parent_id": par_profile.id,
                "is_new": created_new_user
            })

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Błąd serwera: {str(e)}"})


class InviteParentView(LoginRequiredMixin, View):
    def get(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        # Szukamy dziecka tylko w ramach aktywnej placówki
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)
        return render(request, 'parent-invite.html', {'kid': kid})

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)
        parent_email = request.POST.get('email', '').strip().lower()

        if not parent_email:
            messages.error(request, 'Proszę podać adres e-mail.')
            return redirect('invite_parent', pk=pk)

        try:
            with transaction.atomic():
                # 1. Sprawdzamy, czy użytkownik już istnieje
                target_user = User.objects.filter(email=parent_email).first()
                created_new_user = False
                password = None

                if not target_user:
                    # Tworzymy nowe konto
                    password = User.objects.make_random_password()
                    target_user = User.objects.create_user(email=parent_email, password=password)
                    created_new_user = True

                # 2. Pobieramy lub tworzymy profil ParentA dla TEJ placówki
                # Rodzic może już istnieć w systemie, ale nie mieć profilu w tym przedszkolu
                parent_profile, created_profile = ParentA.objects.get_or_create(
                    user=target_user,
                    kindergarten_id=k_id
                )

                # 3. Przypisujemy dziecko do rodzica (relacja ManyToMany w modelu ParentA lub Kid)
                # Zakładając, że ParentA ma pole ManyToMany 'kids'
                if kid not in parent_profile.kids.all():
                    parent_profile.kids.add(kid)

                # 4. Nadajemy uprawnienie techniczne (bezpiecznie, bez clear())
                content_type = ContentType.objects.get_for_model(ParentA)
                permission = Permission.objects.get(content_type=content_type, codename='is_parent')
                if not target_user.has_perm('parent.is_parent'):
                    target_user.user_permissions.add(permission)

                # 5. Przygotowanie treści e-maila
                if created_new_user:
                    subject = f"Zaproszenie – konto rodzica dla dziecka: {kid.first_name}"
                    template = 'email_to_parent.html'
                    msg_pass = password
                else:
                    subject = f"Nowe dziecko przypisane do Twojego konta: {kid.first_name}"
                    template = 'email_to_parent.html'
                    msg_pass = "Twoje obecne hasło"

                html_content = render_to_string(template, {
                    'password': msg_pass,
                    'email': parent_email,
                    'kid': kid,
                    'kindergarten': parent_profile.kindergarten.name
                })

                msg = EmailMultiAlternatives(subject, "Zaproszenie", settings.EMAIL_HOST_USER, [parent_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            messages.success(request, f"Pomyślnie zaproszono rodzica ({parent_email}) dla dziecka {kid.first_name}")
            return redirect('list_kids')

        except Exception as e:
            messages.error(request, f'Wystąpił nieoczekiwany błąd: {e}')
            return redirect('invite_parent', pk=pk)


class AddParentToKidView(LoginRequiredMixin, View):
    PAGINATE_BY = 10

    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Szukamy rodzica w ramach TEJ SAMEJ placówki
        parent = get_object_or_404(ParentA, id=pk, kindergarten_id=k_id)

        search_query = request.GET.get('search', '').strip()
        page_number = request.GET.get('page')

        # 1. Pobieramy dzieci aktywne z TEJ placówki, które nie są jeszcze przypisane do tego rodzica
        kids_qs = Kid.objects.filter(
            kindergarten_id=k_id,
            is_active=True
        ).exclude(parenta=parent)

        # 2. Filtrowanie wyszukiwania
        if search_query:
            kids_qs = kids_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            ).distinct()

        # Sortowanie i paginacja
        kids_qs = kids_qs.order_by('last_name', 'first_name')
        paginator = Paginator(kids_qs, self.PAGINATE_BY)
        kids_list = paginator.get_page(page_number)

        context = {
            'kids_list': kids_list,
            'parent': parent,
            'search_query': search_query,
            # Przekazujemy listę ID dzieci już przypisanych (opcjonalnie do UI)
            'assigned_kids_ids': list(parent.kids.values_list('id', flat=True))
        }
        return render(request, 'parent-kid-add.html', context)

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        parent = get_object_or_404(ParentA, id=pk, kindergarten_id=k_id)

        # 1. Obsługa wyszukiwania przez POST (opcjonalnie)
        if 'search_button' in request.POST:
            search = request.POST.get('search', '').strip()
            return redirect(f"{request.path}?search={search}")

        # 2. Logika przypisywania dzieci
        kids_ids_to_link = request.POST.getlist('kids', [])

        if not kids_ids_to_link:
            messages.warning(request, 'Wybierz co najmniej jedno dziecko.')
            return redirect(request.path)

        # Pobieramy obiekty dzieci, upewniając się, że należą do placówki dyrektora
        valid_kids = Kid.objects.filter(
            id__in=kids_ids_to_link,
            kindergarten_id=k_id,
            is_active=True
        )

        count = 0
        for kid in valid_kids:
            # Zakładając relację ManyToMany 'kids' w modelu ParentA
            if kid not in parent.kids.all():
                parent.kids.add(kid)
                count += 1

        messages.success(request, f'Poprawnie przypisano {count} dzieci do rodzica {parent.user.email}')
        # Upewnij się, że nazwa widoku profilu rodzica to 'parent_profile'
        return redirect('parent_profile', pk=parent.id)


class ParentListView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)
        search_query = request.GET.get('search', '')

        # 1. LOGIKA FILTRACJI ZALEŻNA OD ROLI
        if role == 'director':
            # Dyrektor widzi wszystkich rodziców w swojej placówce
            parents_qs = ParentA.objects.filter(kindergarten_id=k_id)

        elif role == 'teacher':
            # Pobieramy konkretny profil nauczyciela dla tej placówki
            teacher = get_object_or_404(Employee, id=profile_id, kindergarten_id=k_id)

            if not teacher.group:
                # Jeśli nauczyciel nie ma grupy, nie widzi rodziców
                parents_qs = ParentA.objects.none()
            else:
                # Nauczyciel widzi rodziców dzieci ze swojej grupy w tej placówce
                parents_qs = ParentA.objects.filter(
                    kids__group=teacher.group,
                    kids__kindergarten_id=k_id,
                    kindergarten_id=k_id
                ).distinct()
        else:
            raise PermissionDenied

        # 2. WYSZUKIWANIE (Pamiętaj, że imiona są w modelu User)
        if search_query:
            parents_qs = parents_qs.filter(
                Q(user__email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        # 3. STATYSTYKI I PAGINACJA
        # Liczymy dzieci tylko w ramach TEJ placówki
        parents_qs = parents_qs.annotate(
            num_children=Count('kids', filter=Q(kids__kindergarten_id=k_id))
        ).select_related('user').order_by('last_name')

        paginator = Paginator(parents_qs, 15)
        page_obj = paginator.get_page(request.GET.get("page"))

        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'active_role': role
        }
        return render(request, 'parents-list.html', context)

    def post(self, request):
        search = request.POST.get('search', '').strip()
        if search:
            return redirect(f"{request.path}?search={search}")
        return redirect('list_parent')


class ParentProfileView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        # Pobieramy rodzica, upewniając się, że należy do TEJ placówki
        parent = get_object_or_404(ParentA, id=pk, kindergarten_id=k_id)

        context = {
            'parent': parent,
            'active_role': role,
            # Pobieramy dzieci rodzica tylko z tej konkretnej placówki
            'kids_in_kindergarten': parent.kids.filter(kindergarten_id=k_id, is_active=True)
        }

        # 1. LOGIKA DLA RODZICA (dostęp do własnego profilu)
        if role == 'parent':
            # Sprawdzamy, czy ID z sesji zgadza się z ID profilu (jako stringi lub inty)
            if str(parent.id) == str(profile_id):
                return render(request, 'parent_profile.html', context)

        # 2. LOGIKA DLA DYREKTORA (dostęp do wszystkich rodziców w placówce)
        elif role == 'director':
            # get_object_or_404 po k_id już zweryfikował przynależność do placówki
            return render(request, 'parent_profile.html', context)

        # 3. LOGIKA DLA NAUCZYCIELA (dostęp tylko jeśli uczy dziecko tego rodzica)
        elif role == 'teacher':
            teacher = get_object_or_404(Employee, id=profile_id, kindergarten_id=k_id)

            if teacher.group:
                # Sprawdzamy, czy rodzic ma przynajmniej jedno aktywne dziecko w grupie nauczyciela
                has_access = parent.kids.filter(
                    group=teacher.group,
                    is_active=True,
                    kindergarten_id=k_id
                ).exists()

                if has_access:
                    return render(request, 'parent_profile.html', context)

        raise PermissionDenied


class ParentUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        # Pobieramy rodzica w ramach aktywnej placówki
        parent = get_object_or_404(ParentA, id=pk, kindergarten_id=k_id)

        # WERYFIKACJA UPRAWNIEŃ
        # 1. Dyrektor może edytować każdego rodzica w swojej placówce
        # 2. Rodzic może edytować tylko swój własny profil (porównanie ID z sesji)
        if role == 'parent' and str(parent.id) == str(profile_id):
            form = ParentUpdateForm(instance=parent)
            return render(request, 'parent-update.html', {'form': form, 'parent': parent})

        raise PermissionDenied

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        parent = get_object_or_404(ParentA, id=pk, kindergarten_id=k_id)

        if role == 'parent' and str(parent.id) == str(profile_id):
            form = ParentUpdateForm(request.POST, instance=parent)

            if form.is_valid():
                # save() automatycznie zaktualizuje pola modelu ParentA zdefiniowane w Meta.fields/exclude
                form.save()

                # Opcjonalnie: Jeśli imiona są w modelu User, a chcesz je edytować tutaj:
                # user = parent.user
                # user.first_name = request.POST.get('first_name')
                # user.last_name = request.POST.get('last_name')
                # user.save()

                messages.success(request, 'Poprawnie zmieniono dane.')
                return redirect('parent_profile', pk=parent.id)

            messages.error(request, 'Wystąpił błąd walidacji formularza.')
            return render(request, 'parent-update.html', {'form': form, 'parent': parent})

        raise PermissionDenied


class ParentDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        # Pobieramy kontekst z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Szukamy profilu rodzica w ramach aktywnej placówki
        parent = get_object_or_404(ParentA, id=pk, kindergarten_id=k_id)
        parent_email = parent.user.email

        # 1. Odpinamy rodzica od wszystkich jego dzieci W TEJ placówce
        # Robimy to, aby nie zostawić "osieroconych" relacji w bazie
        kids_in_this_kindergarten = parent.kids.filter(kindergarten_id=k_id)
        for kid in kids_in_this_kindergarten:
            parent.kids.remove(kid)

        # 2. Usuwamy tylko ten konkretny profil rodzica
        # Obiekt User pozostaje nienaruszony!
        parent.delete()

        # 3. Opcjonalnie: Jeśli to był ostatni profil ParentA tego użytkownika,
        # można rozważyć odebranie uprawnienia is_parent, ale zazwyczaj się tego nie robi,
        # by nie psuć dostępu do innych przedszkoli.

        messages.success(request, f'Profil rodzica {parent_email} został usunięty z tej placówki.')
        return redirect('list_parent')


class ParentSearchView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy kontekst z sesji
        role, profile_id, k_id = get_active_context(request)

        # Tylko dyrektor i nauczyciel powinni mieć dostęp do wyszukiwarki rodziców
        if role not in ['director', 'teacher']:
            raise PermissionDenied

        search_query = request.GET.get('search', '').strip()

        # 1. Bazowy QuerySet dla aktywnej placówki
        #
        parents_qs = ParentA.objects.filter(kindergarten_id=k_id)

        # 2. Logika wyszukiwania
        if search_query:
            parents_qs = parents_qs.filter(
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        # 3. Dodatkowe ograniczenie dla nauczyciela (widzi tylko rodziców ze swojej grupy)
        if role == 'teacher':
            teacher = get_object_or_404(Employee, id=profile_id)
            if teacher.group:
                parents_qs = parents_qs.filter(kids__group=teacher.group).distinct()
            else:
                parents_qs = ParentA.objects.none()

        parents_qs = parents_qs.select_related('user').order_by('user__last_name')

        # 4. Paginacja
        paginator = Paginator(parents_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'active_role': role
        }

        return render(request, 'parents-list.html', context)

    def post(self, request):
        # Metoda POST służy tu tylko do przekierowania na GET z parametrem search
        search = request.POST.get('search', '').strip()
        if search:
            return redirect(f"{reverse('list_parent')}?search={search}")
        return redirect('list_parent')



class InviteAndAssignParentView(LoginRequiredMixin, View):
    template_name = 'parent-invite-standalone.html'
    PAGINATE_BY = 10

    def get(self, request):
        # 1. Pobieramy kontekst z sesji
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        search_query = request.GET.get('search', '').strip()
        page_number = request.GET.get('page')

        # 2. Pobieramy dzieci TYLKO z tej konkretnej placówki
        kids_qs = Kid.objects.filter(kindergarten_id=k_id, is_active=True).order_by('last_name', 'first_name')

        if search_query:
            kids_qs = kids_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        paginator = Paginator(kids_qs, self.PAGINATE_BY)
        page_obj = paginator.get_page(page_number)

        context = {
            'kids_list': page_obj,
            'search_query': search_query,
            'active_role': role
        }
        return render(request, self.template_name, context)

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        # Obsługa wyszukiwania (przekierowanie na GET)
        if 'search_button' in request.POST:
            search = request.POST.get('search', '').strip()
            return redirect(f"{request.path}?search={search}")

        parent_email = request.POST.get('email', '').strip().lower()
        kid_ids = request.POST.getlist('kid_id')

        if not parent_email:
            messages.error(request, 'Pole Email Rodzica jest wymagane.')
            return redirect(request.path)

        try:
            with transaction.atomic():
                # 1. Pobierz lub utwórz Użytkownika (User)
                target_user = User.objects.filter(email=parent_email).first()
                created_new_user = False
                password = None

                if not target_user:
                    password = User.objects.make_random_password()
                    target_user = User.objects.create_user(email=parent_email, password=password)
                    created_new_user = True

                # 2. Pobierz lub utwórz profil ParentA dla TEJ placówki
                # To zapobiega błędom, gdy rodzic ma już profil w innym Twoim przedszkolu
                parent_profile, created_profile = ParentA.objects.get_or_create(
                    user=target_user,
                    kindergarten_id=k_id
                )

                # 3. Przypisz wybrane dzieci (tylko te z tej placówki!)
                if kid_ids:
                    valid_kids = Kid.objects.filter(id__in=kid_ids, kindergarten_id=k_id)
                    parent_profile.kids.add(*valid_kids)

                # 4. Nadaj uprawnienie techniczne (BEZ .clear())
                content_type = ContentType.objects.get_for_model(ParentA)
                permission = Permission.objects.get(content_type=content_type, codename='is_parent')
                if not target_user.has_perm('parent.is_parent'):
                    target_user.user_permissions.add(permission)

                # 5. Wyślij odpowiedni e-mail
                if created_new_user:
                    subject = "Zaproszenie do systemu KinderManage"
                    template = 'email_to_parent.html'
                    msg_pass = password
                else:
                    subject = f"Nowy profil rodzica w placówce {parent_profile.kindergarten.name}"
                    template = 'email_to_parent.html' # Szablon informujący o nowym profilu
                    msg_pass = "Twoje dotychczasowe hasło"

                html_content = render_to_string(template, {
                    'password': msg_pass,
                    'email': parent_email,
                    'kindergarten_name': parent_profile.kindergarten.name
                })

                msg = EmailMultiAlternatives(subject, "Zaproszenie", settings.EMAIL_HOST_USER, [parent_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            messages.success(request, f"Pomyślnie przetworzono zaproszenie dla {parent_email}.")
            return redirect('list_parent')

        except Exception as e:
            messages.error(request, f'Wystąpił błąd: {e}')
            return redirect(request.path)


class RemoveKidFromParentView(LoginRequiredMixin, View):
    def post(self, request, parent_pk, kid_pk):
        # 1. Pobieramy aktywny kontekst z sesji
        role, profile_id, k_id = get_active_context(request)

        # 2. Weryfikacja roli dyrektora
        if role != 'director':
            raise PermissionDenied

        # 3. Pobieramy rodzica i dziecko, upewniając się, że należą do TEJ SAMEJ placówki
        # Zapobiega to manipulacji ID w celu odpinania dzieci w innych przedszkolach
        parent = get_object_or_404(ParentA, pk=parent_pk, kindergarten_id=k_id)
        kid = get_object_or_404(Kid, pk=kid_pk, kindergarten_id=k_id)

        # 4. Sprawdzamy, czy relacja istnieje i usuwamy ją
        if kid in parent.kids.all():
            parent.kids.remove(kid)
            # Używamy user.first_name, bo dane są w modelu User
            messages.success(request, f"Pomyślnie odpięto dziecko {kid.first_name} od rodzica {parent.user.email}.")
        else:
            messages.warning(request, "To dziecko nie jest przypisane do tego rodzica w tej placówce.")

        # 5. Przekierowanie na profil rodzica
        return redirect('parent_profile', pk=parent.id)
