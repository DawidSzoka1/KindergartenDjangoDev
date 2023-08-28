from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from parent.models import ParentA
from teacher.models import Employee
from .forms import PostAddForm
from .models import Post
from director.models import Director
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class Home(View):
    def get(self, request):
        if request.user.get_user_permissions() == {'parent.is_parent'}:

            kids = get_object_or_404(ParentA, user=request.user.id).kids.filter(is_active=True)
            return render(request, 'home.html', {'kids': kids})
        elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=request.user.id)
            return render(request, 'home.html', {'teacher': teacher})
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
            form = PostAddForm(employee=employee, initial={'author': employee, 'director': employee.principal})
            groups = employee.group
        elif user == {'parent.is_parent'}:
            parent = ParentA.objects.get(user=request.user.id)
            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group__name', flat=True)
            posts = Post.objects.filter(director=parent.principal).filter(group__name__in=groups).order_by(
                '-date_posted')
        else:
            raise PermissionDenied

        paginator = Paginator(posts, 4)
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
                               initial={'author': employee, 'director': employee.principal})
        if form.is_valid():
            form.save()
            messages.success(request, f'Dodano')
            return redirect('post_list_view')


class PostSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('post_list_view')

    def post(self, request):
        search = request.POST.get('search')
        user = request.user
        form = None
        if user.director:
            director = Director.objects.get(user=request.user.id)
            posts = Post.objects.filter(director=user.director).filter(content__icontains=search).order_by(
                '-date_posted')
            form = PostAddForm(director=Director.objects.get(user=request.user.id),
                               initial={'author': director.user, 'director': director})
            groups = director.groups_set.filter(is_active=True)
        elif user.employee:
            employee = Employee.objects.get(user=request.user.id)
            form = PostAddForm(employee=employee, initial={'author': employee, 'director': employee.principal})
            groups = employee.group
            posts = Post.objects.filter(director=user.employee.principal).filter(content__icontains=search).order_by(
                '-date_posted')
        elif user.parenta:
            posts = Post.objects.filter(director=user.parenta.principal).filter(content__icontains=search).order_by(
                '-date_posted')
            parent = ParentA.objects.get(user=request.user.id)
            kids = parent.kids.filter(is_active=True)
            groups = kids.values_list('group__name', flat=True)

        else:
            raise PermissionDenied
        paginator = Paginator(posts, 4)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'post_list.html', {'page_obj': page_obj, 'groups': groups, 'form': form})
