from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from director.models import Director, GroupPhotos
from children.models import Kid
from groups.forms import GroupsForm, AssignKidToGroupForm, AssignTeachersForm
from groups.models import Groups
from parent.models import ParentA
from teacher.models import Employee
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse_lazy


class GroupAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = Director.objects.get(user=request.user.id)
        photos = director.groupphotos_set.filter(is_active=True)
        if photos:
            return render(request, 'group-add.html', {'photos': photos})
        messages.info(request, 'Najpierwsz musisz dodac jakas iconke')
        return redirect('photo_add')

    def post(self, request):
        director = Director.objects.get(user=request.user.id)
        photo_id = request.POST.get('photo')
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        yearbook = request.POST.get('yearbook')
        if photo_id and name and capacity and yearbook:
            if '-' in capacity:
                messages.error(request, 'pojemnosc nie moze byc ujemna')
                return redirect('add_group')
            else:
                image = get_object_or_404(GroupPhotos, id=int(photo_id))
                new_group = Groups.objects.create(name=name, capacity=int(capacity), principal=director, photo=image,
                                                  yearbook=yearbook)

                messages.success(request, f'poprawnie dodano grupe o nazwie {new_group.name}')
                return redirect('list_groups')
        messages.error(request, 'Wszystkie pola musza byc wypelnione')
        return redirect('add_group')


# Create your views here.
class GroupsListView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        groups_qs = Groups.objects.none()  # Inicjalizacja pustym QuerySetem
        search_query = request.GET.get('q', '')  # 1. Pobieramy frazę wyszukiwania

        # Utworzenie filtru bazowego (zależnego od roli)
        if user.get_user_permissions() == {'director.is_director'}:
            try:
                # Pobieramy ID grup należących do dyrektora
                group_ids = Director.objects.get(user=user).groups_set.filter(is_active=True).values_list('id',
                                                                                                          flat=True)
                groups_qs = Groups.objects.filter(id__in=group_ids)
            except Director.DoesNotExist:
                pass

        elif user.get_user_permissions() == {'parent.is_parent'}:
            try:
                # Pobieramy ID grup, do których należą dzieci rodzica
                group_ids = ParentA.objects.get(user=user).kids.filter(is_active=True).values_list('group_id',
                                                                                                   flat=True).distinct()
                groups_qs = Groups.objects.filter(id__in=group_ids)
            except ParentA.DoesNotExist:
                pass

        else:
            raise PermissionDenied

        # 2. Aplikacja wyszukiwania (jeśli fraza nie jest pusta)
        if search_query:
            # Filtrowanie po nazwie grupy (case-insensitive contains)
            groups_qs = groups_qs.filter(
                name__icontains=search_query
            )

        # 3. Dodanie adnotacji z licznikiem dzieci
        groups_qs = groups_qs.annotate(
            child_count=Count('kid', filter=Q(kid__is_active=True))
        ).order_by('-id')

        groups = groups_qs  # Zmieniamy nazwę zmiennej dla czytelności

        # Paginacja
        paginator = Paginator(groups, 3)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)

        return render(request, 'groups-list.html', {
            'page_obj': page_obj,
            'search_query': search_query  # Przekazujemy frazę wyszukiwania do szablonu
        })


class GroupDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        group = get_object_or_404(Groups, id=int(pk))
        teachers_test = list(group.employee_set.values_list("user__email", flat=True))
        teachers = group.employee_set.all()

        # Pobieranie frazy wyszukiwania z URL
        search_query = request.GET.get('q', '').strip()

        # Pobieranie wszystkich aktywnych dzieci z grupy
        kids_qs = group.kid_set.filter(is_active=True)

        # --- APLIKACJA WYSZUKIWANIA ---
        if search_query:
            kids_qs = kids_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
            print(kids_qs)
        # -------------------------------

        # Finalna lista dzieci do przekazania
        kids = kids_qs
        print(kids)

        month = int(timezone.now().month)
        year = int(timezone.now().year)

        # Sprawdzenie uprawnień i renderowanie
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            # ... (Logika nauczyciela) ...
            teacher_email = Employee.objects.get(user=request.user.id).user.email
            if teacher_email in teachers_test:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids, 'month': month, 'year': year,
                               'search_query': search_query})

        elif request.user.get_user_permissions() == {'director.is_director'}:
            # ... (Logika dyrektora) ...
            director = Director.objects.get(user=request.user.id)
            if director == group.principal:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids, 'month': month, 'year': year,
                               'search_query': search_query})

        elif request.user.get_user_permissions() == {'parent.is_parent'}:
            # ... (Logika rodzica) ...
            parent = ParentA.objects.get(user=request.user.id)
            parent_kids = parent.kids.filter(is_active=True)
            allow = False
            for kid in parent_kids:
                # Sprawdzenie, czy przefiltrowana lista dzieci zawiera któreś z dzieci rodzica
                # Ważne: Sprawdzenie 'if kid in kids:' jest nieoptymalne, ale zgodne z Twoją logiką.
                # W praktyce lepiej sprawdzić, czy rodzic ma dzieci w danej grupie.
                if kid in kids:
                    allow = True
                    break
            if allow:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids, 'month': month, 'year': year,
                               'search_query': search_query})

        raise PermissionDenied


class GroupUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        group = get_object_or_404(Groups, id=int(pk))
        director = Director.objects.get(user=request.user.id)

        if director == group.principal:
            form = GroupsForm(instance=group)
            photos = director.groupphotos_set.filter(is_active=True)
            return render(request, 'group-update.html',
                          {'form': form, 'photos': photos, 'group_photo': group.photo, 'group': group})
        raise PermissionDenied

    def post(self, request, pk):
        group = get_object_or_404(Groups, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if director == group.principal:
            form = GroupsForm(request.POST, instance=group)
            if form.is_valid():
                form.save()
                return redirect('group_details', pk=group.id)

            messages.error(request, f'{form.errors}')
            return redirect('group_update', pk=pk)

        raise PermissionDenied


class GroupDeleteView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        group = get_object_or_404(Groups, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if group.principal == director:
            for kid in group.kid_set.filter(is_active=True):
                kid.group = None
                kid.save()
            group.is_active = False
            group.save()
            messages.success(request,
                             f'Poprawnie usunieto grupe')
            return redirect('list_groups')
        raise PermissionDenied


class AssignExistingKidToGroupView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'director.is_director'
    template_name = 'kid_assign_to_group.html'

    def get_success_url(self, group_pk):
        return reverse_lazy('group_details', kwargs={'pk': group_pk})

    def get(self, request, pk):
        group = get_object_or_404(Groups, pk=pk)
        director = get_object_or_404(Director, user=request.user)

        # Logika wyszukiwania (opcjonalnie, jeśli dodasz pole 'q' do URL)
        search_query = request.GET.get('q', '')

        # Dzieci, które można przypisać: należą do dyrektora, są aktywne i NIE mają obecnie ustawionej grupy LUB są w innej grupie.
        # Najprostszy filtr to: nie mają przypisanej grupy LUB mają inną grupę
        available_kids_qs = Kid.objects.filter(
            principal=director,
            is_active=True,
            # Dzieci, które albo mają grupę null, albo mają grupę inną niż obecna
        ).filter(
            Q(group__isnull=True) | ~Q(group__pk=pk)
        )

        # Zastosowanie wyszukiwania
        if search_query:
            available_kids_qs = available_kids_qs.filter(
                Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query)
            )

        return render(request, self.template_name, {
            'group': group,
            'available_kids': available_kids_qs.order_by('last_name'),
            'search_query': search_query,
        })

    def post(self, request, pk):
        group = get_object_or_404(Groups, pk=pk)
        director = get_object_or_404(Director, user=request.user)

        # POBIERAMY LISTĘ ID DZIECI Z CHECKBOXÓW (np. ['1', '5', '9'])
        kid_ids = request.POST.getlist('kid_ids')

        if not kid_ids:
            messages.warning(request, "Nie wybrano żadnego dziecka do przypisania.")
            return redirect(self.get_success_url(pk))

        # Filtrujemy wybrane dzieci, upewniając się, że należą do tego dyrektora
        kids_to_assign = Kid.objects.filter(
            pk__in=kid_ids,
            principal=director
        )

        # Aktualizujemy pole 'group' dla wszystkich wybranych dzieci
        count = kids_to_assign.update(group=group)

        if count > 0:
            messages.success(request, f"Pomyślnie przypisano {count} dzieci do grupy {group.name}.")
        else:
            messages.error(request, "Nie udało się przypisać dzieci lub zostały one już usunięte/przypisane.")

        return redirect(self.get_success_url(pk))


class AssignTeachersView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'director.is_director'
    template_name = 'teacher_assign_to_group.html'  # Utwórz ten szablon

    def get_success_url(self, group_pk):
        return reverse_lazy('group_details', kwargs={'pk': group_pk})

    def get(self, request, pk):
        group = get_object_or_404(Groups, pk=pk)

        # Tworzymy formularz, przekazując ID grupy i dyrektora do __init__
        form = AssignTeachersForm(
            group_pk=pk,
            current_user=request.user
        )

        return render(request, self.template_name, {
            'form': form,
            'group': group,
        })

    def post(self, request, pk):
        group = get_object_or_404(Groups, pk=pk)

        # Przekazujemy dane POST i te same argumenty do formularza
        form = AssignTeachersForm(
            request.POST,
            group_pk=pk,
            current_user=request.user
        )

        if form.is_valid():
            # Zbieramy QuerySet wybranych nauczycieli
            teachers_qs = form.cleaned_data['teachers_to_assign']

            # 1. Aktualizujemy pole 'group' dla wszystkich wybranych nauczycieli
            # Używamy .update() dla efektywności
            count = teachers_qs.update(group=group)

            messages.success(request, f"Pomyślnie przypisano {count} nauczycieli do grupy {group.name}.")
            return redirect(self.get_success_url(pk))

        # Jeśli formularz jest niepoprawny, renderujemy go ponownie z błędami
        return render(request, self.template_name, {
            'form': form,
            'group': group,
        })


class RemoveKidFromGroupView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def post(self, request, kid_pk):
        # 1. Sprawdź, czy dyrektor ma uprawnienia do tego dziecka
        director = get_object_or_404(Director, user=request.user)
        kid = get_object_or_404(Kid, pk=kid_pk, principal=director)

        # Zapamiętaj ID grupy, do której należało dziecko, dla przekierowania
        group_pk = kid.group.pk if kid.group else None

        if group_pk:
            # 2. Ustaw grupę dziecka na NULL (usuń z grupy)
            kid.group = None
            kid.save()

            messages.success(request, f"Dziecko {kid.first_name} zostało pomyślnie usunięte z grupy.")

            # 3. Przekierowanie z powrotem na stronę szczegółów grupy
            return redirect(reverse_lazy('group_details', kwargs={'pk': group_pk}))

        # Jeśli dziecko nie miało grupy, po prostu wróć do głównej strony list grup
        messages.warning(request, "Dziecko nie było przypisane do żadnej grupy.")
        return redirect(reverse_lazy('list_groups'))


class RemoveTeacherFromGroupView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def post(self, request, teacher_pk):
        director = get_object_or_404(Director, user=request.user)
        teacher = get_object_or_404(Employee, pk=teacher_pk, principal=director)

        group_pk = teacher.group.pk if teacher.group else None

        if group_pk:
            # Ustawienie grupy nauczyciela na NULL
            teacher.group = None
            teacher.save()

            messages.success(request, f"Nauczyciel {teacher.user.email} został usunięty z grupy.")
            return redirect(reverse_lazy('group_details', kwargs={'pk': group_pk}))

        messages.warning(request, "Nauczyciel nie był przypisany do żadnej grupy.")
        return redirect(reverse_lazy('list_groups'))
