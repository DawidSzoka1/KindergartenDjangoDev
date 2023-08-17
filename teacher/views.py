from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from children.models import Groups
from django.views import View
from django.contrib import messages
from director.models import Director
from parent.models import ParentA
from .models import Employee, roles
from .forms import TeacherUpdateForm
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class EmployeeProfileView(LoginRequiredMixin, View):

    def get(self, request, pk):
        employee = Employee.objects.get(id=int(pk))
        user = self.request.user
        if user.get_user_permissions() == {'director.is_director'}:
            if employee.principal.first() == user.director:
                return render(request, 'employee-details.html',
                              {'employee': employee})
            messages.error(request, f"Nie masz na to pozwolenia")
            return redirect('list_teachers')
        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            if user.employee == employee:
                return render(request, 'employee-profile.html',
                              {'employee': employee})
        elif user.get_user_permissions() == {'parent.is_parent'}:
            group = employee.group.filter(is_active=True).first()
            kids = group.kid_set.filter(is_active=True)
            parent = ParentA.objects.get(user=user.id)
            allow = False
            for kid in kids:
                if kid in parent.kids.filter(is_active=True):
                    allow = True
                    break
            if allow:
                return render(request, 'employee-profile.html',
                              {'employee': employee})
        raise PermissionDenied


class EmployeesListView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        teachers = user.employee_set.all()
        paginator = Paginator(teachers, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'employees-list.html', {'page_obj': page_obj})

    def post(self, request):
        search = request.POST.get('search')
        if search:
            teachers = Employee.objects.filter(principal=Director.objects.get(user=request.user.id)).filter(
                user__email__icontains=search
            )
            paginator = Paginator(teachers, 10)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            return render(request, 'employees-list.html', {'page_obj': page_obj})
        return redirect('list_teachers')


class EmployeeAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups_set.filter(is_active=True)
        return render(request, 'employee-add.html', {'groups': groups, 'roles': roles})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)
        role = request.POST.get('role')
        salary = request.POST.get('salary')
        group_id = request.POST.get('group')
        group = None
        if group_id:
            group = user.groups_set.get(id=int(group_id))
        teacher_email = request.POST.get('email')
        if teacher_email:
            try:
                test = User.objects.get(email=teacher_email)
            except User.DoesNotExist:
                test = None
            if test:
                messages.error(request, f'Ten email jest zajety')
                return redirect('add_teacher')
            try:
                password = User.objects.make_random_password()
                teacher_user = User.objects.create_user(email=teacher_email, password=password)
                content_type = ContentType.objects.get_for_model(Employee)
                permission = Permission.objects.get(content_type=content_type, codename='is_teacher')
                teacher_object = Employee.objects.create(user=teacher_user, role=role, salary=float(salary))
                user.employee_set.add(teacher_object)
                if group:
                    teacher_object.group = group
                    teacher_object.save()
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
        employee = Employee.objects.get(id=pk)
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            valid = Employee.objects.get(user=request.user.id)
            if employee == valid:
                form = TeacherUpdateForm(instance=employee)
                return render(request, 'employee-update.html',
                              {'form': form, 'valid': valid, 'employee': employee})

        elif request.user.get_user_permissions() == {'director.is_director'}:
            user = Director.objects.get(user=request.user.id)
            groups = user.groups_set.filter(is_active=True)
            if employee.principal.first() == user:
                return render(request, 'employee-update.html',
                              {'form': employee, 'roles': roles, 'groups': groups, 'employee': employee})

        raise PermissionDenied

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
                    teacher.group = group_obj
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
        raise PermissionDenied


class EmployeeDeleteView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        employee = get_object_or_404(Employee, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if employee.principal.first() == director:
            user = User.objects.get(employee=employee.id)
            user.delete()

            messages.success(request, f'Udało sie usunąc {user}')
            return redirect('list_teachers')
        raise PermissionDenied
