from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from director.models import Director, GroupPhotos
from children.models import Kid
from groups.forms import GroupsForm, AssignKidToGroupForm, AssignTeachersForm
from blog.views import get_active_context
from groups.models import Groups
from parent.models import ParentA
from teacher.models import Employee
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse_lazy


class GroupAddView(LoginRequiredMixin, View):

    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied
        photos = GroupPhotos.objects.for_kindergarten(k_id).filter(is_active=True)
        if photos:
            return render(request, 'group-add.html', {'photos': photos})
        messages.info(request, 'Najpierwsz musisz dodac jakas iconke')
        return redirect('photo_add')

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied
        photo_id = request.POST.get('photo')
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        yearbook = request.POST.get('yearbook')
        if photo_id and name and capacity and yearbook:
            if '-' in capacity:
                messages.error(request, 'pojemnosc nie moze byc ujemna')
                return redirect('add_group')
            else:
                image = get_object_or_404(GroupPhotos, id=int(photo_id), kindergarten_id=k_id)
                new_group = Groups.objects.create(
                    name=name,
                    capacity=capacity,
                    kindergarten_id=k_id,
                    photo=image,
                    yearbook=yearbook,
                )

                messages.success(request, f'poprawnie dodano grupe o nazwie {new_group.name}')
                return redirect('list_groups')
        messages.error(request, 'Wszystkie pola musza byc wypelnione')
        return redirect('add_group')


# Create your views here.
class GroupsListView(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        search_query = request.GET.get('q', '')  # 1. Pobieramy frazę wyszukiwania
        base_groups = Groups.objects.for_kindergarten(k_id).filter(is_active=True)
        # Utworzenie filtru bazowego (zależnego od roli)
        if role == 'director':
            # Dyrektor widzi wszystkie grupy w swojej placówce
            groups_qs = base_groups

        elif role == 'teacher':
            # Nauczyciel widzi tylko swoją grupę w tej placówce
            teacher = get_object_or_404(Employee, id=profile_id)
            if teacher.group:
                groups_qs = base_groups.filter(id=teacher.group.id)
            else:
                groups_qs = Groups.objects.none()

        elif role == 'parent':
            # Rodzic widzi grupy, do których należą jego dzieci w tej placówce
            parent = get_object_or_404(ParentA, id=profile_id)
            group_ids = parent.kids.filter(
                kindergarten_id=k_id,
                is_active=True
            ).values_list('group_id', flat=True).distinct()
            groups_qs = base_groups.filter(id__in=group_ids)

        else:
            raise PermissionDenied

        # 2. Aplikacja wyszukiwania (jeśli fraza nie jest pusta)
        if search_query:
            groups_qs = groups_qs.filter(name__icontains=search_query)

        # 3. Dodanie adnotacji z licznikiem dzieci
        groups_qs = groups_qs.annotate(
            child_count=Count('kid', filter=Q(kid__is_active=True)),
            teachers_count=Count('employee', filter=Q(employee__is_active=True), distinct=True),
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
        role, profile_id, k_id = get_active_context(request)

        # Pobieramy grupę upewniając się, że należy do aktywnej placówki
        group = get_object_or_404(Groups, id=pk, kindergarten_id=k_id)
        teachers = group.employee_set.all()
        kids_qs = group.kid_set.filter(is_active=True)

        # Pobieranie frazy wyszukiwania z URL
        search_query = request.GET.get('q', '').strip()

        # Pobieranie wszystkich aktywnych dzieci z grupy

        # --- APLIKACJA WYSZUKIWANIA ---
        if search_query:
            kids_qs = kids_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        # -------------------------------

        # Finalna lista dzieci do przekazania
        kids = kids_qs
        print(kids)

        month = int(timezone.now().month)
        year = int(timezone.now().year)
        can_view = False
        # Sprawdzenie uprawnień i renderowanie
        if role == 'director':
            # Każdy dyrektor przypisany do tej placówki ma dostęp
            can_view = True

        elif role == 'teacher':
            # Sprawdzamy czy aktywny profil nauczyciela jest przypisany do tej grupy
            teacher = get_object_or_404(Employee, id=profile_id)
            if teacher.group == group:
                can_view = True

        elif role == 'parent':
            # Sprawdzamy czy aktywny profil rodzica ma dziecko w tej konkretnej grupie
            parent = get_object_or_404(ParentA, id=profile_id)
            if parent.kids.filter(group=group, is_active=True).exists():
                can_view = True

        if can_view:
            return render(request, 'group-details.html', {
                'group': group,
                'teachers': teachers,
                'kids': kids_qs,
                'month': month,
                'year': year,
                'search_query': search_query
            })

        raise PermissionDenied


class GroupUpdateView(LoginRequiredMixin, View):

    def get(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        # Weryfikacja roli dyrektora
        if role != 'director':
            raise PermissionDenied
        group = get_object_or_404(Groups, id=pk, kindergarten_id=k_id)
        photos = GroupPhotos.objects.for_kindergarten(k_id).filter(is_active=True)
        form = GroupsForm(instance=group)

        return render(request, 'group-update.html', {
            'form': form,
            'photos': photos,
            'group_photo': group.photo,
            'group': group
        })

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied
        group = get_object_or_404(Groups, id=pk, kindergarten_id=k_id)
        form = GroupsForm(request.POST, instance=group)
        if form.is_valid():
            # photo_id z POST (jeśli zmieniono ikonę w szablonie)
            photo_id = request.POST.get('photo')
            if photo_id:
                # Sprawdzamy czy nowa ikona też należy do tej placówki
                group.photo = get_object_or_404(GroupPhotos, id=photo_id, kindergarten_id=k_id)

            form.save()
            messages.success(request, f'Zaktualizowano grupę {group.name}')
            return redirect('group_details', pk=group.id)

        raise PermissionDenied


class GroupDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        # Weryfikacja roli dyrektora dla aktywnego profilu
        if role != 'director':
            raise PermissionDenied

        # Pobieramy grupę upewniając się, że należy do aktywnej placówki
        group = get_object_or_404(Groups, id=pk, kindergarten_id=k_id)

        # Bezpieczne rozłączenie dzieci z usuwanej grupy
        # Filtrujemy dzieci w ramach tej samej placówki dla pewności
        active_kids = group.kid_set.filter(is_active=True, kindergarten_id=k_id)
        for kid in active_kids:
            kid.group = None
            kid.save()

        # Logiczne usunięcie grupy
        group.is_active = False
        group.save()

        messages.success(request, f'Poprawnie usunięto grupę: {group.name}')
        return redirect('list_groups')


class AssignExistingKidToGroupView(LoginRequiredMixin, View):
    template_name = 'kid_assign_to_group.html'

    def get_success_url(self, group_pk):
        return reverse_lazy('group_details', kwargs={'pk': group_pk})

    def get(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied
        group = get_object_or_404(Groups, pk=pk, kindergarten_id=k_id)

        search_query = request.GET.get('q', '')
        available_kids_qs = Kid.objects.for_kindergarten(k_id).filter(
            is_active=True
        ).filter(
            Q(group__isnull=True) | ~Q(group__pk=pk)
        )

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
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Weryfikacja grupy w ramach placówki
        group = get_object_or_404(Groups, pk=pk, kindergarten_id=k_id)

        kid_ids = request.POST.getlist('kid_ids')

        if not kid_ids:
            messages.warning(request, "Nie wybrano żadnego dziecka do przypisania.")
            return redirect(self.get_success_url(pk))

        # Filtrujemy wybrane dzieci upewniając się, że należą do TEJ placówki
        kids_to_assign = Kid.objects.for_kindergarten(k_id).filter(
            pk__in=kid_ids,
            is_active=True
        )

        # Masowa aktualizacja pola 'group'
        count = kids_to_assign.update(group=group)

        if count > 0:
            messages.success(request, f"Pomyślnie przypisano {count} dzieci do grupy {group.name}.")
        else:
            messages.error(request, "Błąd przypisywania dzieci.")

        return redirect(self.get_success_url(pk))


class AssignTeachersView(LoginRequiredMixin, View):
    template_name = 'teacher_assign_to_group.html'

    def get_success_url(self, group_pk):
        return reverse('group_details', kwargs={'pk': group_pk})

    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy grupę upewniając się, że należy do aktywnej placówki
        group = get_object_or_404(Groups, pk=pk, kindergarten_id=k_id)

        # Przekazujemy active_principal_id do formularza zamiast user
        form = AssignTeachersForm(
            group_pk=pk,
            active_principal_id=k_id
        )

        return render(request, self.template_name, {
            'form': form,
            'group': group,
        })

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Weryfikacja grupy w ramach placówki przed zapisem
        group = get_object_or_404(Groups, pk=pk, kindergarten_id=k_id)

        form = AssignTeachersForm(
            request.POST,
            group_pk=pk,
            active_principal_id=k_id
        )

        if form.is_valid():
            # Formularz powinien zwracać nauczycieli przefiltrowanych po placówce
            teachers_qs = form.cleaned_data['teachers_to_assign']

            # Aktualizujemy grupę dla nauczycieli
            count = teachers_qs.update(group=group)

            messages.success(request, f"Pomyślnie przypisano {count} nauczycieli do grupy {group.name}.")
            return redirect(self.get_success_url(pk))

        return render(request, self.template_name, {
            'form': form,
            'group': group,
        })


class RemoveKidFromGroupView(LoginRequiredMixin, View):
    def post(self, request, kid_pk):
        # Pobieramy k_id (placówkę) z aktywnego kontekstu
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Weryfikujemy dziecko w ramach aktywnej placówki
        kid = get_object_or_404(Kid, pk=kid_pk, kindergarten_id=k_id)

        group_pk = kid.group.pk if kid.group else None

        if group_pk:
            # Usuwamy przypisanie do grupy
            kid.group = None
            kid.save()

            messages.success(request, f"Dziecko {kid.first_name} zostało pomyślnie usunięte z grupy.")
            return redirect(reverse('group_details', kwargs={'pk': group_pk}))

        messages.warning(request, "Dziecko nie było przypisane do żadnej grupy.")
        return redirect(reverse('list_groups'))


class RemoveTeacherFromGroupView(LoginRequiredMixin, View):
    def post(self, request, teacher_pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Weryfikujemy nauczyciela w ramach aktywnej placówki
        teacher = get_object_or_404(Employee, pk=teacher_pk, kindergarten_id=k_id)

        group_pk = teacher.group.pk if teacher.group else None

        if group_pk:
            # Usuwamy przypisanie nauczyciela do grupy
            teacher.group = None
            teacher.save()

            messages.success(request, f"Nauczyciel {teacher.user.email} został usunięty z grupy.")
            return redirect(reverse('group_details', kwargs={'pk': group_pk}))

        messages.warning(request, "Nauczyciel nie był przypisany do żadnej grupy.")
        return redirect(reverse('list_groups'))