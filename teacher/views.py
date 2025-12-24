from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from children.models import Groups
from django.views import View
from django.contrib import messages
from director.models import Director, ContactModel
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
from django.urls import reverse
from django.db import transaction

class EmployeeProfileView(LoginRequiredMixin, View):

    def get(self, request, pk):
        employee = get_object_or_404(Employee, id=int(pk))
        user = self.request.user
        if user.get_user_permissions() == {'director.is_director'}:
            if employee.principal.first() == user.director:
                groups = Groups.objects.filter(principal=user.director, is_active=True )
                return render(request, 'employee-profile.html',
                              {'employee': employee, 'groups_list': groups})
            messages.error(request, f"Nie ma takiego nauczyciela")
            return redirect('list_teachers')
        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            if user.employee == employee:
                return render(request, 'employee-profile.html',
                              {'employee': employee})
        elif user.get_user_permissions() == {'parent.is_parent'}:
            parent = get_object_or_404(ParentA, user=user)
            parent_kids_in_teacher_groups = parent.kids.filter(
                is_active=True,
                group=employee.group
            ).select_related('group')
            if parent_kids_in_teacher_groups.exists():
                # Wyciągamy unikalne grupy tych dzieci
                assigned_groups = set(kid.group for kid in parent_kids_in_teacher_groups)
                return render(request, 'employee-profile.html', {
                    'employee': employee,
                    'groups_list': assigned_groups
                })
        raise PermissionDenied


class EmployeesListView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        # 1. Pobieranie danych i filtry
        user_director = Director.objects.get(user=request.user.id)

        # Pobieranie parametru wyszukiwania z GET
        search_query = request.GET.get('search', '')

        # Używamy startowego QuerySetu
        teachers = Employee.objects.filter(principal=user_director)

        # 2. Logika filtrowania (jeśli jest zapytanie)
        if search_query:
            # Wyszukujemy po emailu (z icontains)
            teachers = teachers.filter(
                user__email__icontains=search_query
            )

        # Sortowanie
        teachers = teachers.order_by('-id')

        # 3. Paginacja
        paginator = Paginator(teachers, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Dodajemy 'search_query' do kontekstu, aby móc go użyć w szablonie (np. do zachowania wartości w polu wyszukiwania)
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
        }

        return render(request, 'employees-list.html', context)

    def post(self, request):
        # W metodzie POST tylko pobieramy wartość z formularza i przekierowujemy do GET
        search = request.POST.get('search')

        base_url = reverse('list_teachers')

        if search:
            # 2. Dodaj parametr zapytania (?search=...) do podstawowego URL
            full_url = f'{base_url}?search={search}'
            return redirect(full_url)

        # Jeśli pole było puste, nadal wracamy do czystej listy
        return redirect('list_teachers')


class EmployeeAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        # Pobieramy tylko aktywne grupy przypisane do tego dyrektora
        groups = user.groups_set.filter(is_active=True)
        return render(request, 'employee-add.html', {'groups': groups, 'roles': roles})

    def post(self, request):
        user_director = Director.objects.get(user=request.user.id)

        # Wczytywanie danych
        role_pk = request.POST.get('role')
        salary_str = request.POST.get('salary')
        group_id = request.POST.get('group') # Może być puste
        teacher_email = request.POST.get('email')

        # Wczesna walidacja wymaganych pól
        if not teacher_email or not role_pk or not salary_str:
            messages.error(request, 'Wypełnij wszystkie wymagane pola (Email, Posada, Wynagrodzenie).')
            return redirect('add_teacher')

        try:
            role = int(role_pk)
            salary = float(salary_str)

            # Walidacja, czy email nie jest zajęty
            if User.objects.filter(email=teacher_email).exists():
                messages.error(request, f'Ten email jest już zajęty.')
                return redirect('add_teacher')

        except ValueError:
            messages.error(request, "Nieprawidłowy format wynagrodzenia lub roli.")
            return redirect('add_teacher')

        # Logika przypisania grupy:
        group = None
        if group_id:
            # Sprawdzamy, czy wybrana grupa faktycznie należy do tego dyrektora
            group = user_director.groups_set.filter(id=int(group_id)).first()
            if not group:
                # Jeśli grupa została wybrana, ale nie należy do dyrektora, to jest błąd.
                messages.error(request, "Wybrana grupa jest nieprawidłowa.")
                return redirect('add_teacher')

        # Dodatkowa walidacja dla roli 'nauczyciel' (role=2)
        if role == 2 and not group:
            messages.error(request, "Dla roli 'nauczyciel' wymagane jest przypisanie grupy.")
            return redirect('add_teacher')


        # --- LOGIKA TWÓRCZA I TRANSKAJNA ---
        try:
            with transaction.atomic():
                # 1. Utwórz użytkownika
                password = User.objects.make_random_password()
                teacher_user = User.objects.create_user(email=teacher_email, password=password)

                # Wyczyść stare rekordy (jeśli istnieją)
                # Zostawiam ten fragment, ale jest BARDZO ryzykowne:
                from director.models import ContactModel # Dodaj import
                ContactModel.objects.filter(director__user__email=teacher_email).delete()
                Director.objects.filter(user__email=teacher_email).delete()

                # 2. Utwórz obiekt Pracownika
                teacher_object = Employee.objects.create(
                    user=teacher_user,
                    role=role,
                    salary=salary,
                    group=group # Przypisujemy grupę (może być None)
                )

                # 3. Przypisz Dyrektora jako principal
                user_director.employee_set.add(teacher_object)

                # 4. Przypisz uprawnienie 'is_teacher'
                from django.contrib.contenttypes.models import ContentType
                from django.contrib.auth.models import Permission

                content_type = ContentType.objects.get_for_model(Employee)
                permission = Permission.objects.get(content_type=content_type, codename='is_teacher')
                teacher_object.user.user_permissions.clear()
                teacher_object.user.user_permissions.add(permission)

                teacher_user.employee.save() # To jest zbędne, obiekt został zapisany wyżej

            subject = f"Zaproszenie na konto przedszkola dla nauczyciela"
            from_email = EMAIL_HOST_USER # Zmień na faktyczną zmienną z settings.py
            text_content = "Marchewka zaprasza do korzystania z konto jako nauczyciel"

            html_content = render_to_string('email_to_parent.html', {'password': password, 'email': teacher_email})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [teacher_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, f"Udalo sie zaprosic nauczyciela o emailu {teacher_email}")
            return redirect('list_teachers')

        except Exception as e:
            messages.error(request, f'Wystąpił nieoczekiwany błąd: {e}')
            return redirect('add_teacher')


class EmployeeUpdateView(LoginRequiredMixin, View):

    def get(self, request, pk):
        employee = get_object_or_404(Employee, id=int(pk))

        # --- LOGIKA NAUCZYCIEL (Edycja Danych Osobowych) ---
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            # Sprawdzamy, czy edytuje swój własny profil
            try:
                if request.user.employee == employee:
                    form = TeacherUpdateForm(instance=employee)
                    # Zmienna 'valid' działa jako flaga dla szablonu
                    return render(request, 'employee-update.html',
                                  {'form': form, 'valid': True, 'employee': employee})
            except Employee.DoesNotExist:
                pass # Kontynuuj do PermissionDenied

        # --- LOGIKA DYREKTOR (Edycja Roli/Wynagrodzenia) ---
        elif request.user.get_user_permissions() == {'director.is_director'}:
            user_director = get_object_or_404(Director, user=request.user)

            # Sprawdzamy, czy pracownik jest przypisany do tego dyrektora
            if employee.principal.filter(id=user_director.id).exists():

                # DYREKTOR widzi formularz edycji roli/wynagrodzenia
                # Tutaj MUSISZ przekazać: roles i groups, oraz instancję 'employee'

                # Pobieramy grupy aktywne przypisane do tego dyrektora
                groups = user_director.groups_set.filter(is_active=True)

                # Używamy form = employee, bo nie używamy tu TeacherUpdateForm
                return render(request, 'employee-update.html',
                              {'employee': employee, 'roles': roles, 'groups': groups, 'valid': False})

        raise PermissionDenied

    def post(self, request, pk):
        employee = get_object_or_404(Employee, id=int(pk))

        # --- LOGIKA NAUCZYCIEL (POST: Dane Osobowe) ---
        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            # Sprawdzamy uprawnienia ponownie
            try:
                if Employee.objects.get(user=self.request.user) == employee:
                    form = TeacherUpdateForm(request.POST, instance=employee)
                    if form.is_valid():
                        form.save()
                        messages.success(request, 'Udalo sie zmienic dane.')
                        return redirect('teacher-profile', pk=pk)

                    # W przypadku błędu, wracamy do formularza z błędami i flagą 'valid'
                    messages.error(request, 'Wystąpił błąd walidacji w formularzu.')
                    return render(request, 'employee-update.html',
                                  {'form': form, 'valid': True, 'employee': employee})
            except Employee.DoesNotExist:
                pass

        # --- LOGIKA DYREKTOR (POST: Rola/Wynagrodzenie) ---
        elif request.user.get_user_permissions() == {'director.is_director'}:

            # Dyrektor musi być przełożonym tego pracownika
            user_director = get_object_or_404(Director, user=request.user)
            if not employee.principal.filter(id=user_director.id).exists():
                messages.error(request, "Brak uprawnień do edycji tego pracownika.")
                return redirect('list_teachers')

            # Wczytywanie surowych danych
            role_pk = request.POST.get('role')
            salary_str = request.POST.get('salary')
            group_id = request.POST.get('group') # group_id może być pusty (None)

            try:
                # Walidacja danych
                if not role_pk or not salary_str:
                    messages.error(request, "Rola i Wynagrodzenie są wymagane.")
                    return redirect('teacher_update', pk=pk)

                role = int(role_pk)
                salary = float(salary_str)

                # Aktualizacja Roli i Wynagrodzenia
                employee.salary = salary
                employee.role = role

                # Logika przypisania Grupy (tylko jeśli rola to 2 'nauczyciel')
                if role == 2:
                    if group_id:
                        group_obj = get_object_or_404(Groups, id=int(group_id))
                        employee.group = group_obj
                    else:
                        # Nauczyciel musi mieć grupę (jeśli chcesz to wymusić)
                        messages.error(request, "Dla roli 'nauczyciel' wymagane jest przypisanie grupy.")
                        return redirect('teacher_update', pk=pk)
                else:
                    # Dla innych ról, ustawiamy grupę na None
                    employee.group = None

                employee.save()
                messages.success(request, 'Udalo sie zmienic informacje.')
                return redirect('teacher-profile', pk=pk)

            except ValueError:
                messages.error(request, "Nieprawidłowy format danych (np. wynagrodzenia).")
                return redirect('teacher_update', pk=pk)
            except Exception as e:
                messages.error(request, f"Wystąpił nieoczekiwany błąd: {e}")
                return redirect('teacher_update', pk=pk)

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



class AssignTeachersView(PermissionRequiredMixin, View):
    permission_required = "director.is_director" # Tylko dyrektor może przypisywać

    def post(self, request, pk):
        # pk to ID pracownika, który jest modyfikowany
        director = Director.objects.get(user=request.user.id)
        employee = get_object_or_404(Employee, pk=pk)
        if employee.principal.first() != director:
            return redirect('list_teachers')

        # Odbieramy wartość 'group_id' z formularza
        group_id = request.POST.get('group_id')

        try:
            if group_id:
                # Jeśli wybrano grupę, pobierz obiekt grupy
                selected_group = get_object_or_404(Groups, pk=group_id)
                employee.group = selected_group
                messages.success(request, f"Pomyślnie przypisano {employee.first_name} do grupy {selected_group.name}.")
            else:
                # Jeśli wybrano opcję "Brak grupy" (group_id jest puste)
                employee.group = None
                messages.success(request, f"Pomyślnie usunięto przypisanie grupy dla {employee.first_name}.")

            employee.save()

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas przypisywania grupy: {e}")

        # Przekieruj z powrotem na stronę profilu nauczyciela
        return redirect('teacher-profile', pk=employee.pk)



class ChangeEmployeeGroupView(LoginRequiredMixin, PermissionRequiredMixin, View):
    # Nazwa tego widoku powinna być użyta w URL-ach, np. 'change_employee_group'
    permission_required = 'director.is_director'

    def post(self, request, pk):
        # 1. Pobierz obiekt Pracownika (pk to ID pracownika)
        director = Director.objects.get(user=request.user.id)
        employee = get_object_or_404(Employee, pk=pk)
        if employee.principal.first() != director:
            return redirect('list_teachers')
        # 2. Pobierz wartość 'group_id' z Modala (name="group_id" w radio buttonach)
        group_id = request.POST.get('group_id')

        try:
            if group_id:
                # Wybrano grupę: Znajdź obiekt grupy
                selected_group = get_object_or_404(Groups, pk=group_id)
                employee.group = selected_group
                messages.success(request, f"Pomyślnie przypisano {employee.user.email} do grupy {selected_group.name}.")
            else:
                # Wybrano opcję "Brak grupy" (group_id jest puste)
                employee.group = None
                messages.success(request, f"Pomyślnie usunięto przypisanie grupy dla {employee.user.email}.")

            employee.save()

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas przypisywania grupy: {e}")

        # 3. PRZEKIEROWANIE DO PROFILU PRACOWNIKA
        return redirect('teacher-profile', pk=employee.pk)