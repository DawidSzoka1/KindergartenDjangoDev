from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import UpdateView, DetailView
from django.utils import timezone
from children.models import PresenceModel
from groups.models import Groups
from parent.models import ParentA
from teacher.models import Employee
from django.db.models import Count, Q, F
from .forms import PostAddForm
from datetime import timedelta
from .models import Post
from director.models import Director, ContactModel, Kindergarten
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from children.models import Kid


def get_active_context(request):
    """Zwraca aktywną rolę i ID placówki/profilu z sesji"""
    role = request.session.get('active_role')
    profile_id = request.session.get('active_profile_id')
    kindergarten_id = request.session.get('active_kindergarten_id')

    # Fallback, jeśli sesja jest pusta
    if not role:
        perms = request.user.get_all_permissions()
        if 'director.is_director' in perms: role = 'director'
        elif 'teacher.is_teacher' in perms: role = 'teacher'
        elif 'parent.is_parent' in perms: role = 'parent'

    return role, int(profile_id), int(kindergarten_id)

class Home(View):
    def get(self, request):
        now = timezone.now()
        last_week = now - timedelta(days=7)
        user = request.user
        role, profile_id, k_id = get_active_context(request)
        if role == 'parent':
            parent = get_object_or_404(ParentA, id=profile_id, user=user) if profile_id else get_object_or_404(ParentA, user=user)

            # 1. Dzieci z paginacją (4 na stronę)
            kids_list = parent.kids.filter(is_active=True, kindergarten_id=k_id).select_related('group').order_by('last_name')
            kids_page = Paginator(kids_list, 4).get_page(request.GET.get('kids_page'))

            group_ids = kids_list.values_list('group__id', flat=True)

            # 2. Najnowsze ogłoszenia (dowolny typ, z ostatniego tygodnia)
            announcements_list = Post.objects.for_kindergarten(k_id).filter(
                group__id__in=group_ids, is_active=True, date_posted__gte=last_week
            ).distinct().order_by('-date_posted')
            ann_page = Paginator(announcements_list, 3).get_page(request.GET.get('ann_page'))

            # 3. Nadchodzące wydarzenia (przyszłe daty)
            upcoming_events = Post.objects.for_kindergarten(k_id).filter(
                group__id__in=group_ids,
                is_active=True,
                event_date__gte=now.date()
            ).distinct().order_by('event_date')[:2]

            # 4. Kadra Nauczycielska z paginacją (np. 3 na stronę w bocznym pasku)
            teachers_list = Employee.objects.for_kindergarten(k_id).filter(group__id__in=group_ids, is_active=True).distinct().order_by(
                'last_name')
            teachers_page = Paginator(teachers_list, 3).get_page(request.GET.get('t_page'))

            # 5. Dyrektorzy z paginacją
            principals_list = Director.objects.for_kindergarten(k_id).order_by('last_name')
            principals_page = Paginator(principals_list, 2).get_page(request.GET.get('p_page'))

            context = {
                'kids': kids_page,
                'announcements': ann_page,
                'upcoming_events': upcoming_events,
                'upcoming_events_count': upcoming_events.count(),
                'teachers': teachers_page,
                'principals': principals_page,
                'month_current': now.month,
                'year_current': now.year,
            }
            return render(request, 'home.html', context)
        # --- LOGIKA DLA NAUCZYCIELA ---
        elif role == 'teacher':
            teacher = get_object_or_404(Employee, id=profile_id, user=user) if profile_id else get_object_or_404(Employee, user=user)
            group = teacher.group

            # Pobieramy dzieci i dzisiejsze obecności
            kids_in_group = Kid.objects.for_kindergarten(k_id).filter(group=group, is_active=True).order_by('last_name')
            today_presences = PresenceModel.objects.filter(day=now.date(), kid__group=group)

            # Tworzymy mapę dla szybkiego wyszukiwania
            presence_map = {p.kid_id: p.presenceType for p in today_presences}

            # PRZYPISANIE STATUSU DO KAŻDEGO DZIECKA (Rozwiązanie bez filtra)
            for kid in kids_in_group:
                # Pobieramy status ze słownika, jeśli nie ma - None
                kid.today_status = presence_map.get(kid.id)

            # Statystyki (bez zmian)
            stats = {
                'total': kids_in_group.count(),
                'present': today_presences.filter(presenceType=2).count(),
                'boys': kids_in_group.filter(gender=1).count(),
                'girls': kids_in_group.filter(gender=2).count(),
            }

            context = {
                'teacher': teacher,
                'group': group,
                'kids': kids_in_group,  # Obiekty mają teraz atrybut .today_status
                'stats': stats,
                'today': now,
            }
            return render(request, 'home.html', context)
        elif role == 'director':

            # Podstawowe liczniki
            kids_count = Kid.objects.for_kindergarten(k_id).filter(is_active=True).count()
            groups_count = Groups.objects.for_kindergarten(k_id).filter(is_active=True).count()
            teachers_count = Employee.objects.for_kindergarten(k_id).filter(is_active=True).count()

            # Statystyki obecności na dzisiaj
            kids_presence_count = PresenceModel.objects.filter(
                kid__kindergarten_id=k_id,
                day=now.date(),
                presenceType=2  # Zakładamy 2 = Obecny
            ).count()

            # Ostatnia aktywność (ogłoszenia dyrektora i jego grup)
            recent_announcements = Post.objects.for_kindergarten(k_id).filter(
                is_active=True,
            ).order_by('-date_posted')[:4]

            # Podsumowanie grup (zajętość)
            groups_summary = Groups.objects.for_kindergarten(k_id).filter(is_active=True).annotate(
                kid_count=Count('kid', filter=Q(kid__is_active=True))
            )

            # Obliczanie procentowej zajętości dla każdej grupy w Pythonie
            for group in groups_summary:
                if group.capacity and group.capacity > 0:
                    group.capacity_percent = (group.kid_count / group.capacity) * 100
                else:
                    group.capacity_percent = 0

            # Ogólna zajętość placówki
            total_capacity = sum(g.capacity for g in groups_summary if g.capacity)
            occupancy_rate = (kids_count / total_capacity * 100) if total_capacity > 0 else 0

            context = {
                'kids_count': kids_count,
                'groups_count': groups_count,
                'teachers_count': teachers_count,
                'kids_presence_count': kids_presence_count,
                'recent_announcements': recent_announcements,
                'groups_summary': groups_summary,
                'total_capacity': total_capacity,
                'occupancy_rate': occupancy_rate,
                'today': now,
            }
            return render(request, 'home.html', context)
        return render(request, 'home.html')


def available_profiles(request):
    """Automatycznie dostarcza profile do przełącznika kont w base.html"""
    if not request.user.is_authenticated:
        return {}

    teacher_profiles = Employee.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('kindergarten') # Używamy relacji do nowej placówki

    # Pobieramy profile rodzica (obsługa wielu placówek)
    parent_profiles = ParentA.objects.filter(
        user=request.user
    ).prefetch_related('kids__kindergarten') # Rodzic może mieć dzieci w różnych placówkach

    # Pobieramy profile dyrektora
    # Teraz jeden użytkownik może mieć wiele profilów Director w różnych Kindergarten
    director_profiles = Director.objects.filter(
        user=request.user
    ).select_related('kindergarten')
    k_id = request.session.get('active_kindergarten_id')
    active_kindergarten = None
    active_role = request.session.get('active_role')
    active_profile_id = request.session.get('active_profile_id')
    profile = None
    if not active_profile_id:
        if active_role == 'director':
            profile = Director.objects.filter(user=request.user).first()
            active_profile_id = profile.id if profile else None
        elif active_role == 'teacher':
            profile = Employee.objects.filter(user=request.user).first()
            active_profile_id = profile.id if profile else None
    if k_id:
        active_kindergarten = Kindergarten.objects.filter(id=k_id).first()
    active_profile_obj = None
    if active_profile_id and active_role:
        if active_role == 'teacher':
            # Pobieramy konkretny profil nauczyciela wraz z grupą
            active_profile_obj = Employee.objects.for_kindergarten(k_id).filter(id=active_profile_id, user=request.user).select_related('group').first()
        elif active_role == 'director':
            active_profile_obj = Director.objects.for_kindergarten(k_id).filter(id=active_profile_id, user=request.user).first()
        elif active_role == 'parent':
            active_profile_obj = ParentA.objects.for_kindergarten(k_id).filter(id=active_profile_id, user=request.user).first()
    return {
        'my_director_profiles': director_profiles,
        'my_teacher_profiles': teacher_profiles,
        'my_parent_profiles': parent_profiles,
        # Przekazujemy pełny komplet danych sesji do bazy
        'active_role': active_role,
        'active_profile_id': active_profile_id,
        'active_kindergarten_id': k_id, # To jest ID Kindergarten
        'active_kindergarten': active_kindergarten,
        'profile': active_profile_obj,
    }


class PostListView(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        # Pobieranie parametrów filtra
        selected_groups = request.GET.getlist('filter_group')
        timeframe = request.GET.get('timeframe', 'upcoming')

        # Podstawowy QuerySet
        posts = Post.objects.for_kindergarten(k_id).filter(is_active=True)
        groups = Groups.objects.for_kindergarten(k_id).filter(is_active=True)

        if role == "parent":  # Parent
            parent = get_object_or_404(ParentA, id=profile_id, user=request.user)
            user_groups = parent.kids.filter(kindergarten_id=k_id, is_active=True).values_list('group', flat=True)
            posts = posts.filter(Q(group__id__in=user_groups) | Q(group__isnull=True)).distinct()


        # Aplikowanie filtrów z bocznego paska
        if selected_groups:
            posts = posts.filter(group__id__in=selected_groups).distinct()

        # Sortowanie po dacie wydarzenia
        posts = posts.order_by('event_date', '-date_posted')

        paginator = Paginator(posts, 10)
        page_obj = paginator.get_page(request.GET.get("page"))

        return render(request, 'post_list.html', {
            'page_obj': page_obj,
            'groups_list': groups,
            'selected_groups': list(map(int, selected_groups))
        })


class PostSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('post_list_view')

    def post(self, request):
        search = request.POST.get('search')
        user = request.user
        role, profile_id, principal_id = get_active_context(request)
        form = None
        if role == 'director':
            director = get_object_or_404(Director, id=principal_id, user=user) if principal_id else get_object_or_404(Director, user=user)
            posts = Post.objects.filter(director=user.director).filter(is_active=True).filter(
                content__icontains=search).order_by(
                '-date_posted')
            form = PostAddForm(director=Director.objects.get(user=request.user.id),
                               initial={'author': director.user, 'director': director})
            groups = director.groups_set.filter(is_active=True)
        elif role == 'teacher':
            employee = get_object_or_404(Employee, id=profile_id, user=user) if profile_id else get_object_or_404(Employee, user=user)
            form = PostAddForm(employee=employee, initial={'author': employee, 'director': employee.principal.first()})
            groups = employee.group
            posts = Post.objects.filter(director=user.employee.principal.first().id).filter(is_active=True).filter(
                content__icontains=search).order_by(
                '-date_posted')
        else:
            parent = get_object_or_404(ParentA, id=profile_id, user=request.user)
            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group__id', flat=True)
            posts = Post.objects.filter(director=user.parenta.principal.first().id).filter(is_active=True).filter(
                group__id__in=groups).filter(
                content__icontains=search).order_by(
                '-date_posted')

            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group', flat=True)

        paginator = Paginator(posts, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'post_list.html', {'page_obj': page_obj, 'groups': groups, 'form': form})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Post
    template_name = 'post_update.html'
    form_class = PostAddForm
    success_message = "Poprawnie zmieniono informacje"

    def get_success_url(self):
        return reverse_lazy('post_list_view')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        role, profile_id, k_id = get_active_context(self.request)
        kwargs.update({
            'active_principal_id': k_id,
            'current_user': self.request.user
        })
        if role == 'teacher':
            kwargs.update({'employee': get_object_or_404(Employee, id=profile_id)})
        return kwargs

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        role, profile_id, k_id = get_active_context(self.request)

        # 1. Autor zawsze może edytować
        if post.author == self.request.user:
            return True

        # 2. Dyrektor może edytować każdy post w swojej placówce
        if role == 'director' and post.kindergarten_id == int(k_id):
            return True

        return False


class PostDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        # Sprawdzamy, czy post istnieje i należy do tej placówki
        post = get_object_or_404(Post, id=pk, kindergarten_id=k_id)
        if post.author == request.user or role == 'director':
            post.is_active = False
            post.save()
            messages.success(request, 'Usunięto ogłoszenie.')
        return redirect('post_list_view')


class PostAddView(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role not in ['director', 'teacher']:
            raise PermissionDenied

        # Dodajemy dane początkowe dla pól ukrytych
        form = PostAddForm(
            active_principal_id=k_id,
            current_user=request.user,
            initial={
                'author': request.user.id,
                'is_active': True
            },
        )
        return render(request, 'post_add.html', {'form': form})

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)

        form = PostAddForm(
            request.POST,
            active_principal_id=k_id,
            current_user=request.user
        )
        if form.is_valid():
            # Formularz ma już author i director z pól ukrytych, więc save() zadziała
            post = form.save()
            # save_m2m() jest wywoływane automatycznie przez form.save(),
            # chyba że użyjesz commit=False
            messages.success(request, "Wydarzenie zostało pomyślnie opublikowane.")
            return redirect('post_list_view')

        # Jeśli nie przeszło walidacji, renderuj z błędami
        return render(request, 'post_add.html', {'form': form})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        user = self.request.user
        role, profile_id, k_id = get_active_context(self.request)
        if not k_id:
            return Post.objects.none()
        # Dyrektor i Nauczyciel widzą wszystkie posty
        if role == 'director':
            return Post.objects.for_kindergarten(k_id).filter(is_active=True)

        # Nauczyciel widzi posty placówki, w której aktualnie pracuje (wg sesji)
        if role == 'teacher':
            return Post.objects.for_kindergarten(k_id).filter(is_active=True)
        # Rodzic widzi posty bez grupy (ogólne) LUB posty swoich dzieci
        if role == 'parent':
            try:
                parent = ParentA.objects.get(id=profile_id, user=user) if profile_id else ParentA.objects.get(user=user)
                child_groups = parent.kids.filter(
                    kindergarten_id=k_id,
                    is_active=True
                ).values_list('group_id', flat=True)
                return Post.objects.for_kindergarten(k_id).filter(
                    Q(group__isnull=True) | Q(group__id__in=child_groups)
                ).distinct()
            except ParentA.DoesNotExist:
                return Post.objects.none()

        return Post.objects.none()


class SwitchAccountView(LoginRequiredMixin, View):
    def post(self, request):
        role = request.POST.get('role')
        profile_id = request.POST.get('profile_id')
        kindergarten_id = request.POST.get('kindergarten_id')
        kindergarten = get_object_or_404(Kindergarten, id=kindergarten_id)
        request.session['active_role'] = role
        request.session['active_profile_id'] = profile_id
        request.session['active_kindergarten_id'] = kindergarten_id

        messages.success(request, f"Przełączono na placówkę: {kindergarten.name} (Rola: {role})")
        return redirect('home_page')
