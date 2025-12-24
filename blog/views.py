from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import UpdateView
from django.utils import timezone
from children.models import PresenceModel
from groups.models import Groups
from parent.models import ParentA
from teacher.models import Employee
from .forms import PostAddForm
from datetime import timedelta
from .models import Post
from director.models import Director
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from children.models import Kid


class Home(View):
    def get(self, request):
        now = timezone.now()
        last_week = now - timedelta(days=7)
        if request.user.get_user_permissions() == {'parent.is_parent'}:
            parent = get_object_or_404(ParentA, user=request.user.id)

            # 1. Dzieci z paginacją (4 na stronę)
            kids_list = parent.kids.filter(is_active=True).select_related('group').order_by('last_name')
            kids_page = Paginator(kids_list, 4).get_page(request.GET.get('kids_page'))

            group_ids = kids_list.values_list('group__id', flat=True)

            # 2. Najnowsze ogłoszenia (dowolny typ, z ostatniego tygodnia)
            announcements_list = Post.objects.filter(
                group__id__in=group_ids,
                is_active=True,
                date_posted__gte=last_week
            ).distinct().order_by('-date_posted')
            ann_page = Paginator(announcements_list, 3).get_page(request.GET.get('ann_page'))

            # 3. Nadchodzące wydarzenia (przyszłe daty)
            upcoming_events = Post.objects.filter(
                group__id__in=group_ids,
                is_active=True,
                event_date__gte=now.date()
            ).distinct().order_by('event_date')[:2]

            # 4. Kadra Nauczycielska z paginacją (np. 3 na stronę w bocznym pasku)
            teachers_list = Employee.objects.filter(group__id__in=group_ids, is_active=True).distinct().order_by('last_name')
            teachers_page = Paginator(teachers_list, 3).get_page(request.GET.get('t_page'))

            # 5. Dyrektorzy z paginacją
            principals_list = parent.principal.all().order_by('last_name')
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
        elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=request.user.id)
            return render(request, 'home.html', {'teacher': teacher})
        elif request.user.get_user_permissions() == {'director.is_director'}:
            kids = Kid.objects.filter(principal=request.user.id, is_active=True).count()
            groups = Groups.objects.filter(principal=request.user.id, is_active=True).count()
            teachers = Employee.objects.filter(principal=request.user.id, is_active=True).count()
            return render(request, 'home.html', {'teachers_count': teachers, 'groups_count': groups, 'kids_count': kids})
        return render(request, 'home.html')


class PostListView(LoginRequiredMixin, View):
    def get(self, request):
        user_perm = request.user.get_user_permissions()

        # Pobieranie parametrów filtra
        selected_groups = request.GET.getlist('filter_group')
        timeframe = request.GET.get('timeframe', 'upcoming')

        # Podstawowy QuerySet
        posts = Post.objects.filter(is_active=True)

        if user_perm == {'director.is_director'}:
            director = request.user.director
            posts = posts.filter(director=director)
            groups = Groups.objects.filter(principal=director, is_active=True)
        elif user_perm == {'teacher.is_teacher'}:
            employee = request.user.employee
            posts = posts.filter(director=employee.principal.first())
            groups = Groups.objects.filter(principal=employee.principal.first(), is_active=True)
        else: # Parent
            parent = request.user.parenta
            user_groups = parent.kids.filter(is_active=True).values_list('group', flat=True)
            posts = posts.filter(group__id__in=user_groups)
            groups = Groups.objects.filter(id__in=user_groups)

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
        user_perm = user.get_user_permissions()
        form = None
        if user_perm == {'director.is_director'}:
            director = Director.objects.get(user=request.user.id)
            posts = Post.objects.filter(director=user.director).filter(is_active=True).filter(
                content__icontains=search).order_by(
                '-date_posted')
            form = PostAddForm(director=Director.objects.get(user=request.user.id),
                               initial={'author': director.user, 'director': director})
            groups = director.groups_set.filter(is_active=True)
        elif user_perm == {'teacher.is_teacher'}:
            employee = Employee.objects.get(user=request.user.id)
            form = PostAddForm(employee=employee, initial={'author': employee, 'director': employee.principal.first()})
            groups = employee.group
            posts = Post.objects.filter(director=user.employee.principal.first().id).filter(is_active=True).filter(
                content__icontains=search).order_by(
                '-date_posted')
        elif user_perm == {'parent.is_parent'}:
            parent = ParentA.objects.get(user=request.user.id)
            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group__id', flat=True)
            posts = Post.objects.filter(director=user.parenta.principal.first().id).filter(is_active=True).filter(
                group__id__in=groups).filter(
                content__icontains=search).order_by(
                '-date_posted')

            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group', flat=True)

        else:
            raise PermissionDenied
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
        user = self.request.user
        # Dopasowujemy do nowej logiki formularza
        if hasattr(user, 'director'):
            kwargs.update({'director': user.director})
        elif hasattr(user, 'employee'):
            kwargs.update({'employee': user.employee})
        return kwargs

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        try:
            if self.request.user == post.author:
                if post.is_active:
                    return True
        except Exception:
            return False
        return False


class PostDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        return redirect('post_list_view')

    def post(self, request, pk):
        post = get_object_or_404(Post, id=int(pk))
        if post.author == request.user:
            post.is_active = False
            post.save()
            messages.success(request, 'Poprawnie usunięto wydarzenie')
            return redirect('post_list_view')
        raise PermissionDenied


class PostAddView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # Wyznaczamy dyrektora placówki dla autora
        if hasattr(user, 'director'):
            director_obj = user.director
            form_kwargs = {'director': director_obj}
        elif hasattr(user, 'employee'):
            director_obj = user.employee.principal.first()
            form_kwargs = {'employee': user.employee}
        else:
            raise PermissionDenied

        # Dodajemy dane początkowe dla pól ukrytych
        form = PostAddForm(
            initial={
                'author': user.id,
                'director': director_obj.id,
                'is_active': True
            },
            **form_kwargs
        )
        return render(request, 'post_add.html', {'form': form})

    def post(self, request):
        user = request.user
        # Inicjalizacja z POST i odpowiednimi kwargami filtracji grup
        if hasattr(user, 'director'):
            form = PostAddForm(request.POST, director=user.director)
        elif hasattr(user, 'employee'):
            form = PostAddForm(request.POST, employee=user.employee)

        if form.is_valid():
            # Formularz ma już author i director z pól ukrytych, więc save() zadziała
            post = form.save()
            # save_m2m() jest wywoływane automatycznie przez form.save(),
            # chyba że użyjesz commit=False
            messages.success(request, "Wydarzenie zostało pomyślnie opublikowane.")
            return redirect('post_list_view')

        # Jeśli nie przeszło walidacji, renderuj z błędami
        return render(request, 'post_add.html', {'form': form})
