from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from director.models import Director, GroupPhotos
from groups.forms import GroupsForm
from groups.models import Groups
from parent.models import ParentA
from teacher.models import Employee
from django.utils import timezone


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
        if user.get_user_permissions() == {'director.is_director'}:
            groups = Director.objects.get(user=user.id).groups_set.filter(is_active=True).order_by('-id')
        elif user.get_user_permissions() == {'parent.is_parent'}:
            kids = ParentA.objects.get(user=user.id).kids.filter(is_active=True).order_by('-id')
            groups = []
            for kid in kids:
                groups.append(kid.group)
        else:
            raise PermissionDenied
        paginator = Paginator(groups, 3)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        return render(request, 'groups-list.html', {'page_obj': page_obj})


class GroupDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        group = get_object_or_404(Groups, id=int(pk))
        teachers_test = list(group.employee_set.values_list("user__email", flat=True))
        teachers = group.employee_set.all()
        kids = group.kid_set.filter(is_active=True)
        month = int(timezone.now().month)
        year = int(timezone.now().year)
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher_email = Employee.objects.get(user=request.user.id).user.email
            if teacher_email in teachers_test:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids, 'month': month, 'year': year})
        elif request.user.get_user_permissions() == {'director.is_director'}:
            director = Director.objects.get(user=request.user.id)
            if director == group.principal:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids, 'month': month, 'year': year})
        elif request.user.get_user_permissions() == {'parent.is_parent'}:
            parent = ParentA.objects.get(user=request.user.id)
            parent_kids = parent.kids.filter(is_active=True)
            allow = False
            for kid in parent_kids:
                if kid in kids:
                    allow = True
                    break
            if allow:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids, 'month': month, 'year': year})

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
