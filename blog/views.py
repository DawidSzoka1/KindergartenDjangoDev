from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import UpdateView

from groups.models import Groups
from parent.models import ParentA
from teacher.models import Employee
from .forms import PostAddForm
from .models import Post
from director.models import Director
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from children.models import Kid


class Home(View):
    def get(self, request):
        if request.user.get_user_permissions() == {'parent.is_parent'}:
            kids = get_object_or_404(ParentA, user=request.user.id).kids.filter(is_active=True)
            return render(request, 'home.html', {'kids': kids})
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
        user = request.user.get_user_permissions()
        form = None
        if user == {'director.is_director'}:
            director = Director.objects.get(user=request.user.id)
            posts = director.post_set.filter(is_active=True).order_by('-date_posted')
            groups = director.groups_set.filter(is_active=True)
            form = PostAddForm(director=Director.objects.get(user=request.user.id),
                               initial={'author': director.user, 'director': director})

        elif user == {'teacher.is_teacher'}:
            employee = Employee.objects.get(user=request.user.id)
            posts = employee.principal.first().post_set.filter(is_active=True).order_by('-date_posted')
            form = PostAddForm(employee=employee,
                               initial={'author': employee.user, 'director': employee.principal.first()})
            groups = employee.group
        elif user == {'parent.is_parent'}:
            parent = ParentA.objects.get(user=request.user.id)
            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group__id', flat=True)
            posts = Post.objects.filter(director=parent.principal.first().id).filter(group__id__in=groups).filter(
                is_active=True).order_by(
                '-date_posted')
        else:
            raise PermissionDenied

        paginator = Paginator(posts, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'post_list.html', {'page_obj': page_obj, 'groups': groups, 'form': form})

    def post(self, request):
        user = request.user.get_user_permissions()
        form = None
        if user == {'director.is_director'}:
            user = Director.objects.get(user=request.user.id)
            form = PostAddForm(request.POST, director=Director.objects.get(user=request.user.id),
                               initial={'author': user.user, 'director': user})

        elif user == {'teacher.is_teacher'}:
            employee = Employee.objects.get(user=request.user.id)
            form = PostAddForm(request.POST, employee=employee,
                               initial={'author': employee.user, 'director': employee.principal.first()})
        if form.is_valid():
            form.save()
            messages.success(request, f'Dodano')
            return redirect('post_list_view')
        messages.error(request, f'{form.errors}')
        return redirect('post_list_view')


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

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(PostUpdateView, self).get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
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
