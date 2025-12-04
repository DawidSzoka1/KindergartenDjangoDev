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

    def get(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        if parent.principal.first().user.email == request.user.email:
            kids = Director.objects.get(user=request.user.id).kid_set.filter(is_active=True).exclude(parenta=parent)
            return render(request, 'parent-kid-add.html', {'kids': kids, 'parent': parent})
        raise PermissionDenied

    def post(self, request, pk):
        director = Director.objects.get(user=request.user.id)
        parent = get_object_or_404(ParentA, id=int(pk))
        if parent.principal.first().user.email == director.user.email:
            kids = request.POST.getlist('kids')
            for kid in kids:
                kid = get_object_or_404(Kid, id=int(kid))
                if kid.id in director.kid_set.filter(is_active=True).values_list('id', flat=True):
                    parent.kids.add(kid)
                    parent.save()
            messages.success(request, f'Poprawnie dodano wybrane dzieci do {parent.user.email}')
            return redirect('list_parent')


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

    def get(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        form = ParentUpdateForm(instance=parent)
        if parent.user.email == request.user.email:
            return render(request, 'parent-update.html', {'form': form, 'parent': parent})
        raise PermissionDenied

    def post(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        form = ParentUpdateForm(request.POST, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Poprawnie zmieniona dane')
            return redirect('parent_profile', pk=parent.id)
        messages.error(request, f'{form.errors}')
        return redirect('parent_update', pk=parent.id)


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

        if not kid_ids:
            messages.warning(request, 'Utworzono konto rodzica, ale nie przypisano dziecka. Przypisz dziecko później.')

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
