from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from children.models import Groups
from django.views import View
from django.contrib import messages
from director.models import Director
from .models import Employee, roles
from .forms import TeacherUpdateForm
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class EmployeeProfileView(LoginRequiredMixin, View):

    def get(self, request, pk):
        employee = Employee.objects.get(id=int(pk))
        user = self.request.user
        if user.director:
            if employee.principal.first() == user.director:
                return render(request, 'employee-details.html',
                              {'employee': employee})
            messages.error(request, f"Nie masz na to pozwolenia")
            return redirect('list_teachers')
        if user.employee:
            if user.employee == employee:
                return render(request, 'employee-profile.html',
                              {'employee': employee})
        messages.error(request, f"{user.director}")
        return redirect('home_page')


class EmployeesListView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        teachers = user.employee_set.all()
        return render(request, 'employees-list.html', {'teachers': teachers})


class EmployeeAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups_set.all()
        return render(request, 'employee-add.html', {'groups': groups, 'roles': roles})

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
                user.employee_set.add(teacher_object)
                if group:
                    teacher_object.group.add(group)
                teacher_object.user.user_permissions.clear()
                teacher_object.user.user_permissions.add(permission)
                teacher_user.employee.save()
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
            messages.success(request, f"Udalo sie zaprosic nauczyciela o emailu {teacher_email}")
            return redirect('list_teachers')

        else:
            messages.error(request, 'wypelnij wszystkie pola')
            return redirect('add_teacher')


class EmployeeUpdateView(LoginRequiredMixin, View):

    def get(self, request, pk):
        form = Employee.objects.get(id=pk)
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            valid = Employee.objects.get(user=request.user.id)
            if form == valid:
                form = TeacherUpdateForm(instance=form)
                return render(request, 'employee-update.html',
                              {'form': form, 'valid': valid})

        elif request.user.get_user_permissions() == {'director.is_director'}:
            user = Director.objects.get(user=request.user.id)
            groups = user.groups_set.all()
            if form.principal.first() == user:
                return render(request, 'employee-update.html', {'form': form, 'roles': roles, 'groups': groups})

        messages.error(request, 'Nie masz na to zgody')
        return redirect('home_page')

    def post(self, request, pk):
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            employee = Employee.objects.get(id=int(pk))
            if Employee.objects.get(user=self.request.user.id) == employee:
                form = TeacherUpdateForm(request.POST, instance=employee)
                if form.is_valid():
                    form.save()
                    messages.success(request, f'Udalo sie zmienic dane')
                    return redirect('teacher-profile', pk=pk)
                messages.success(request, f'{form.errors}')
                return redirect('teacher_update', pk=pk)
        elif request.user.get_user_permissions() == {'director.is_director'}:
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
                    return redirect('teacher-profile', pk=pk)
            elif role != 2:
                if salary and role:
                    teacher.salary = float(salary)
                    teacher.role = role
                    teacher.save()
                    messages.success(request, 'Udalo sie zmienic informacje')
                    return redirect('teacher-profile', pk=pk)
            messages.error(request, "cos poszlo nie tak")
            return redirect('list_teachers')
        messages.error(request, 'Nie masz na to zezwolenia')
        return redirect('home_page')


class TeacherSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('list_teachers')

    def post(self, request):
        search = request.POST.get('search')
        if search:
            teachers = Employee.objects.filter(principal=Director.objects.get(user=request.user.id)).filter(
                user__email__icontains=search
            )
            return render(request, 'employees-list.html', {'teachers': teachers})
        return redirect('list_teachers')
