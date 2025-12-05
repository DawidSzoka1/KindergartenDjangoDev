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


@csrf_exempt
def create_parent_ajax(request):
    if request.method != "POST" or not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Brak dostępu"})
    body = json.loads(request.body)
    email = body.get('email', '').strip()
    try:
        if not email or '@' not in email:
            return JsonResponse({"success": False, "error": "Wpisz poprawny e-mail"})

        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "error": "Ten e-mail już jest zajęty"})

        # Generujemy hasło
        import random, string
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

        # Tworzymy użytkownika i rodzica
        user = User.objects.create_user(
            email=email,
            password=password
        )
        content_type = ContentType.objects.get_for_model(ParentA)
        permission = Permission.objects.get(content_type=content_type, codename='is_parent')
        principal = Director.objects.get(user=request.user.id)
        par_user = ParentA.objects.create(user=user)
        par_user.principal.add(principal)
        par_user.user.user_permissions.clear()
        par_user.user.user_permissions.add(permission)
        user.parenta.save()

        # Wysyłamy e-mail z hasłem
        subject = f"Zaproszenie do KinderManage – konto rodzica dla Twojego dziecka"
        text_content = f"Cześć!\n\nTwoje konto zostało utworzone.\nE-mail: {email}\nHasło: {password}\n\nZaloguj się tutaj: {request.scheme}://{request.get_host()}\n\nPozdrawiamy,\nZespół KinderManage"

        html_content = render_to_string('email_to_parent.html', {
            'password': password,
            'email': email,
            'login_url': f"{request.scheme}://{request.get_host()}"
        })

        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return JsonResponse({
            "success": True,
            "email": email
        })
    except Exception as e:
        User.objects.filter(email=email).first().delete()
        return JsonResponse({"success": False, "error": str(e)})


class InviteParentView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kid_set.filter(id=int(pk)).first()
        if kid:
            return render(request, 'parent-invite.html', {'kid': kid})
        else:
            raise PermissionDenied

    def post(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kid_set.filter(id=int(pk)).first()
        parent_email = request.POST.get('email')
        if kid:
            if parent_email:
                try:
                    test = User.objects.get(email=parent_email)
                except User.DoesNotExist:
                    test = None
                if test:
                    messages.error(request, 'Ten rodzic juz istnieje')
                    return redirect('invite_parent', pk=pk)
                try:
                    password = User.objects.make_random_password()
                    parent_user = User.objects.create_user(email=parent_email, password=password)
                    ContactModel.objects.get(director__user__email=parent_email).delete()
                    Director.objects.get(user__email=parent_email).delete()
                    content_type = ContentType.objects.get_for_model(ParentA)
                    permission = Permission.objects.get(content_type=content_type, codename='is_parent')
                    par_user = ParentA.objects.create(user=parent_user)
                    par_user.principal.add(user)
                    par_user.kids.add(kid)
                    par_user.user.user_permissions.clear()
                    par_user.user.user_permissions.add(permission)
                    parent_user.parenta.save()
                except Exception as e:
                    User.objects.filter(email=parent_email).first().delete()
                    messages.error(request, f'Wystąpił blad {e}')
                    return redirect('invite_parent', pk=pk)

                subject = f"Zaproszenie na konto przedszkola dla rodzica {kid.first_name}"
                from_email = EMAIL_HOST_USER
                text_content = "Marchewka zaprasza do korzystania z konto do ubslugi dzieci"
                html_content = render_to_string('email_to_parent.html', {'password': password, 'email': parent_email})
                msg = EmailMultiAlternatives(subject, text_content, from_email, [parent_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                messages.success(request, f"Udalo sie zaprosic rodzica o emailu {parent_email} ")
                return redirect('list_kids')

            else:
                messages.error(request, 'wypelnij formularz')
                return redirect('invite_parent', pk=pk)
        else:
            raise PermissionDenied


class AddParentToKidView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"
    PAGINATE_BY = 10 # Ilość dzieci na stronę

    def get(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        user_director = get_object_or_404(Director, user=request.user)
        search_query = request.GET.get('search', '').strip()
        page_number = request.GET.get('page')

        # 1. Walidacja uprawnień (czy dyrektor jest przełożonym rodzica)
        if parent.principal.filter(user=request.user).exists():

            # 2. Pobieramy dzieci aktywne, nieprzypisane jeszcze do tego rodzica
            kids_qs = user_director.kid_set.filter(is_active=True).exclude(parenta=parent)

            # 3. Filtrowanie (jeśli search_query jest obecne)
            if search_query:
                kids_qs = kids_qs.filter(
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query)
                ).distinct()

            # Sortowanie i paginacja
            kids_qs = kids_qs.order_by('last_name', 'first_name')
            paginator = Paginator(kids_qs, self.PAGINATE_BY)
            kids_list = paginator.get_page(page_number)

            # Wczytujemy z sesji/POST listę już zaznaczonych dzieci (jeśli użytkownik przeładował stronę)
            # Lista ID dzieci, które były zaznaczone w ostatnim POST/GET
            previously_selected_kids = request.session.get('selected_kids_for_parent_link', [])

            context = {
                'kids_list': kids_list,
                'parent': parent,
                'search_query': search_query,
                'previously_selected_kids': previously_selected_kids,
            }
            return render(request, 'parent-kid-add.html', context)

        raise PermissionDenied

    def post(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        user_director = get_object_or_404(Director, user=request.user)

        # 1. Sprawdzamy, czy formularz POST to wyszukiwanie, czy zapis
        if 'search_button' in request.POST:
            # Użyjemy tej logiki, jeśli musisz użyć POST do wyszukiwania
            search = request.POST.get('search', '').strip()

            # Zapisz aktualny stan checkboxów do sesji, zanim przeładujesz stronę GET
            selected_kids = request.POST.getlist('kids', [])
            request.session['selected_kids_for_parent_link'] = selected_kids

            if search:
                return redirect(f"{request.path}?search={search}")
            else:
                return redirect(request.path)


        # 2. Logika zapisu linków (główny submit)
        if parent.principal.filter(user=request.user).exists():

            # Lista ID dzieci wybranych przez użytkownika
            kids_ids_to_link = request.POST.getlist('kids', [])
            if not kids_ids_to_link:
                messages.warning(request, f'Wybierz conajmniej jedno dziecko do podpięcia')
                return redirect(request.path)
                # Sprawdzenie, czy dyrektor ma prawo do tych dzieci
            valid_kids_qs = user_director.kid_set.filter(is_active=True, id__in=kids_ids_to_link)

            count = 0
            for kid in valid_kids_qs:
                if kid not in parent.kids.all():
                    parent.kids.add(kid)
                    count += 1

            # Usuwamy stan sesji po pomyślnym zapisie
            if 'selected_kids_for_parent_link' in request.session:
                del request.session['selected_kids_for_parent_link']

            messages.success(request, f'Poprawnie dodano {count} dzieci do {parent.user.email}')
            return redirect('parent_profile', pk=parent.id)

        raise PermissionDenied


class ParentListView(LoginRequiredMixin, View):

    def get(self, request):
        user = request.user
        search_query = request.GET.get('search', '')
        if user.get_user_permissions() == {'director.is_director'}:
            director = get_object_or_404(Director, user=user.id)
            parents_qs = director.parenta_set.all().order_by('-id')
        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=user.id)
            parent_ids = teacher.group.kid_set.filter(is_active=True).values_list('parenta', flat=True).distinct()
            # Pobieramy obiekty rodziców na podstawie zebranych ID
            parents_qs = teacher.principal.first().parenta_set.filter(id__in=parent_ids)
        else:
            raise PermissionDenied
        if search_query:
            # Używamy Q dla złożonego, ale prostego wyszukiwania
            parents_qs = parents_qs.filter(
                Q(user__email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        parents_qs = parents_qs.annotate(num_children=Count('kids')).order_by('-id')
        paginator = Paginator(parents_qs, 15)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'parents-list.html', {'page_obj': page_obj, 'search_query': search_query, })

    def post(self, request):
        user = request.user
        search = request.POST.get('search', '').strip()
        if search:
            return redirect(f"{request.path}?search={search}")
        return redirect('list_parent')


class ParentProfileView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = request.user
        parent = get_object_or_404(ParentA, id=int(pk))
        context = {
            'parent': parent

        }
        if user.get_user_permissions() == {'parent.is_parent'}:
            if parent.user.email == user.email:
                return render(request, 'parent_profile.html', context)
        elif user.get_user_permissions() == {'director.is_director'}:
            director = get_object_or_404(Director, user=user.id)
            if parent in director.parenta_set.all():
                return render(request, 'parent_profile.html', context)
        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=user.id)
            if parent.kids.filter(group=teacher.group).filter(is_active=True):
                return render(request, 'parent_profile.html', context)

        raise PermissionDenied


class ParentUpdateView(PermissionRequiredMixin, View):
    permission_required = 'parent.is_parent'

    def check_permissions(self, user, parent):
        """Sprawdza, czy użytkownik ma prawo do edycji tego profilu rodzica."""
        # Własny rodzic:
        if user.get_user_permissions() == {'parent.is_parent'} and parent.user.email == user.email:
            return True

        # Dyrektor:
        if user.get_user_permissions() == {'director.is_director'}:
            try:
                director = Director.objects.get(user=user)
                if parent.principal.filter(id=director.id).exists():
                    return True
            except Director.DoesNotExist:
                pass

        return False

    def get(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))

        if self.check_permissions(request.user, parent):
            form = ParentUpdateForm(instance=parent)
            return render(request, 'parent-update.html', {'form': form, 'parent': parent})

        raise PermissionDenied

    def post(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))

        if self.check_permissions(request.user, parent):
            form = ParentUpdateForm(request.POST, instance=parent)
            if form.is_valid():
                form.save(commit=False) # Zapisz model, ale nie do bazy

                # Ręcznie zaktualizuj pola inne niż ManyToMany (kids)
                # Używamy form.instance, który ma już zaktualizowane dane z POST
                parent.first_name = form.cleaned_data.get('first_name')
                parent.last_name = form.cleaned_data.get('last_name')
                parent.gender = form.cleaned_data.get('gender')
                parent.phone = form.cleaned_data.get('phone')
                parent.city = form.cleaned_data.get('city')
                parent.address = form.cleaned_data.get('address')
                parent.zip_code = form.cleaned_data.get('zip_code')

                parent.save() # Zapisz zmiany do bazy
                messages.success(request, 'Poprawnie zmieniono dane.')
                return redirect('parent_profile', pk=parent.id)

            # W przypadku błędu, renderujemy formularz ponownie z błędami
            messages.error(request, 'Wystąpił błąd walidacji formularza. Sprawdź pola zaznaczone na czerwono.')
            return render(request, 'parent-update.html', {'form': form, 'parent': parent})

        raise PermissionDenied


class ParentDeleteView(PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        if parent.principal.first().user.email == request.user.email:
            user = User.objects.get(id=parent.user.id)
            user.delete()
            messages.success(request, f'Rodzic {user} został usniety')
            return redirect('list_parent')
        raise PermissionDenied


class ParentSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('list_parent')

    def post(self, request):
        search = request.POST.get('search')
        if search:
            parents = ParentA.objects.filter(principal=Director.objects.get(user=request.user.id)).filter(
                user__email__icontains=search
            ).order_by('-id')
            paginator = Paginator(parents, 5)
            page_number = request.POST.get('page')
            page_obj = paginator.get_page(page_number)
            parents = page_obj
            return render(request, 'parents-list.html', {'parents': parents, 'page_obj': page_obj})
        return redirect('list_parent')



class InviteAndAssignParentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "director.is_director"
    template_name = 'parent-invite-standalone.html' # Będziemy renderować ten szablon tylko w przypadku błędów GET
    PAGINATE_BY = 10

    def get(self, request):
        # Pobierz listę dzieci do wyświetlenia w modalnym oknie
        user_director = get_object_or_404(Director, user=request.user)
        search_query = request.GET.get('search', '').strip()
        page_number = request.GET.get('page')
        # Pobierz wszystkie aktywne dzieci dyrektora, które nie mają jeszcze rodzica (lub mają tylko jednego)
        # Zależnie od twojej logiki, może to być:
        # kids_list = user_director.kid_set.filter(parenta__isnull=True, is_active=True)
        # Dla uproszczenia (i możliwości wielokrotnego przypisania):
        kids_qs = user_director.kid_set.filter(is_active=True).order_by('last_name', 'first_name')

        if search_query:
            # Filtrujemy tylko, jeśli jest zapytanie
            kids_qs = kids_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        paginator = Paginator(kids_qs, self.PAGINATE_BY)
        page_obj = paginator.get_page(page_number)
        context = {
            'kids_list': page_obj, # Przekazujemy obiekt paginacji
            'search_query': search_query
        }
        # W widoku GET nie robimy nic, bo modal jest częścią innego szablonu (np. list_kids/list_parent)
        # Jeśli ten widok byłby wywoływany samodzielnie, używamy:
        return render(request, self.template_name, context)

    def post(self, request):
        if 'search_button' in request.POST:
            # Obsługa wyszukiwania z pola tekstowego (wymagane dla paginacji)
            search = request.POST.get('search', '').strip()

            if search:

                return redirect(f"{request.path}?search={search}")
            else:
                return redirect(request.path)
        user_director = get_object_or_404(Director, user=request.user)
        parent_email = request.POST.get('email', '').strip()
        # Odbieramy listę ID dzieci (z checkboxów)
        kid_ids = request.POST.getlist('kid_id')

        # --- Walidacja ---
        if not parent_email:
            messages.error(request, 'Pole Email Rodzica jest wymagane.')
            return redirect('invite_standalone_parent')

        if User.objects.filter(email=parent_email).exists():
            messages.error(request, 'Ten email jest już zajęty.')
            return redirect('invite_standalone_parent')


        # --- LOGIKA TWORZENIA KONTA Z TRANSAKCJĄ ---
        try:
            with transaction.atomic():

                # 1. Utwórz użytkownika
                password = User.objects.make_random_password()
                parent_user = User.objects.create_user(email=parent_email, password=password)

                # 2. Utwórz obiekt ParentA i przypisz Dyrektora
                par_user = ParentA.objects.create(user=parent_user)
                par_user.principal.add(user_director)

                # 3. Przypisz dzieci (jeśli istnieją)
                if kid_ids:
                    kids_to_assign = user_director.kid_set.filter(id__in=kid_ids)
                    par_user.kids.add(*kids_to_assign)

                # 4. Przypisz uprawnienie 'is_parent'
                content_type = ContentType.objects.get_for_model(ParentA)
                permission = Permission.objects.get(content_type=content_type, codename='is_parent')
                par_user.user.user_permissions.clear()
                par_user.user.user_permissions.add(permission)
                par_user.save()

                # 5. Wyślij zaproszenie
                subject = "Zaproszenie na konto przedszkola dla rodzica"
                from_email = EMAIL_HOST_USER
                text_content = "Zostałeś zaproszony do utworzenia konta rodzica w systemie przedszkola."
                html_content = render_to_string('email_to_parent.html', {'password': password, 'email': parent_email})

                msg = EmailMultiAlternatives(subject, text_content, from_email, [parent_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            messages.success(request, f"Pomyślnie utworzono konto i wysłano zaproszenie dla {parent_email}.")
            return redirect('list_parent')

        except Exception as e:
            messages.error(request, f'Wystąpił błąd podczas tworzenia konta: {e}')
            return redirect('invite_standalone_parent')


class RemoveKidFromParentView(PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def post(self, request, parent_pk, kid_pk):
        parent = get_object_or_404(ParentA, pk=parent_pk)
        kid = get_object_or_404(Kid, pk=kid_pk)

        # Sprawdzamy, czy relacja istnieje i usuwamy ją
        if kid in parent.kids.all():
            parent.kids.remove(kid) # Usuwamy relację ManyToMany
            messages.success(request, f"Pomyślnie odpięto dziecko {kid.first_name} od {parent.user.email}.")
        else:
            messages.warning(request, "To dziecko nie było przypisane do tego rodzica.")

        # Przekierowujemy z powrotem na profil rodzica
        return redirect('parent_profile', pk=parent_pk)
