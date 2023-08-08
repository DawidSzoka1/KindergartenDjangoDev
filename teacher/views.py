from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from children.models import Groups
from django.views import View
from django.contrib import messages
from director.models import Director
from .models import Employee, roles
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.views.generic import DetailView, UpdateView


class TeachersListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        teachers = user.teacher_set.all()
        return render(request, 'director-list-teachers.html', {'teachers': teachers})


class AddTeacherView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups_set.all()

        return render(request, 'director-add-teacher.html', {'groups': groups, 'roles': roles})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)
        group = None
        role = request.POST.get('role')
        salary = request.POST.get('salary')
        if role == 2:
            group_id = request.POST.get('group')
            group = user.groups.get(id=int(group_id))
        teacher_email = request.POST.get('email')
        if teacher_email:
            try:
                test = User.objects.get(email=teacher_email)
            except User.DoesNotExist:
                test = None
            if test:
                messages.error(request, 'Ten nauczyciel juz istnieje')
                return redirect('add_teacher')
            try:
                password = User.objects.make_random_password()
                teacher_user = User.objects.create_user(email=teacher_email, password=password)
                content_type = ContentType.objects.get_for_model(Employee)
                permission = Permission.objects.get(content_type=content_type, codename='is_teacher')
                teacher_object = Employee.objects.create(user=teacher_user, role=role, salary=float(salary))
                user.teacher_set.add(teacher_object)
                if group:
                    group.teachers.add(teacher_object)
                teacher_object.user.user_permissions.clear()
                teacher_object.user.user_permissions.add(permission)
                teacher_user.teacher.save()
            except Exception as e:
                User.objects.filter(email=teacher_email).first().delete()

                messages.error(request, f'Wystąpił blad {e}')
                return redirect('add_teacher')
            subject = f"Zaproszenie na konto przedszkola dla nauczyciela"
            from_email = EMAIL_HOST_USER
            text_content = "Marchewka zaprasza do korzystania z konto jako nauczyciel"
            html_content = render_to_string('email_to_parent.html', {'password': password, 'email': teacher_email})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [teacher_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return redirect('list_teachers')

        else:
            messages.error(request, 'wypelnij wszystkie pola')
            return redirect('add_teacher')


class TeacherDetailsView(PermissionRequiredMixin, UserPassesTestMixin, DetailView):
    permission_required = "director.is_director"
    model = Employee
    template_name = 'director-details-teacher.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["teacher"] = get_object_or_404(Director, user=self.request.user.id).teacher_set.get(
            id=context['teacher'].id)
        return context

    def test_func(self):
        teacher = self.get_object()
        if self.request.user == teacher.principal.first().user:
            return True
        return False


class TeacherUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        form = Employee.objects.get(id=pk)
        user = Director.objects.get(user=request.user.id)
        groups = user.groups_set.all()
        if form.principal.all().first() == user:

            return render(request, 'director-update-teacher.html', {'form': form, 'roles': roles, 'groups': groups})
        else:
            messages.error(request, 'Nie masz na to zgody')
            return redirect('home_page')

    def post(self, request, pk):
        role = int(request.POST.get('role'))
        salary = request.POST.get('salary')
        group = request.POST.get('group')
        teacher = Employee.objects.get(id=pk)
        teacher.group.clear()
        if role == 2:
            if group and salary:
                teacher.salary = float(salary)
                group_obj = Groups.objects.get(id=int(group))
                teacher.group.add(group_obj)
                teacher.role = role
                teacher.save()
                messages.success(request, 'Udalo sie zmienic informacje')
                return redirect('teacher_details', pk=pk)
        else:
            if salary and role:

                teacher.salary = float(salary)
                teacher.role = role
                teacher.save()
                messages.success(request, 'Udalo sie zmienic informacje')
                return redirect('teacher_details', pk=pk)
        messages.error(request, "Wypełnij poprawnie wszytkie pola")
        return redirect('teacher_update', args=(pk,))



