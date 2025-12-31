from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from children.models import Groups
from django.views import View
from django.contrib import messages
from director.models import Director, ContactModel
from parent.models import ParentA
from children.models import Kid
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
from blog.views import get_active_context



class EmployeeProfileView(LoginRequiredMixin, View):

    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        # Pobieramy profil pracownika, upewniając się, że należy do TEJ placówki
        employee = get_object_or_404(Employee, id=pk, kindergarten_id=k_id)

        context = {
            'employee': employee,
            'active_role': role
        }

        # 1. LOGIKA DLA DYREKTORA
        if role == 'director':
            # Dyrektor widzi wszystkich pracowników swojej placówki
            # Przekazujemy listę grup TEJ placówki do ewentualnej zmiany przypisania
            context['groups_list'] = Groups.objects.filter(kindergarten_id=k_id, is_active=True)

            if employee.group:
                kids_queryset = Kid.objects.filter(group=employee.group, is_active=True).order_by('last_name')
                paginator = Paginator(kids_queryset, 6)
                context['kids'] = paginator.get_page(request.GET.get('kids_page'))

            return render(request, 'employee-profile.html', context)

        # 2. LOGIKA DLA NAUCZYCIELA
        elif role == 'teacher':
            # Nauczyciel może widzieć swój własny profil
            if employee.id == profile_id:
                if employee.group:
                    kids_queryset = Kid.objects.filter(group=employee.group, is_active=True).order_by('last_name')
                    paginator = Paginator(kids_queryset, 6)
                    context['kids'] = paginator.get_page(request.GET.get('kids_page'))
                return render(request, 'employee-profile.html', context)

            # Opcjonalnie: Nauczyciele mogą widzieć profile innych nauczycieli w tej samej placówce
            # return render(request, 'employee-profile.html', context)

        # 3. LOGIKA DLA RODZICA
        elif role == 'parent':
            # Rodzic widzi profil nauczyciela tylko, jeśli uczy on w grupie jego dziecka
            parent = get_object_or_404(ParentA, id=profile_id)

            # Sprawdzamy czy jakiekolwiek dziecko rodzica jest w grupie tego nauczyciela
            has_common_group = parent.kids.filter(
                kindergarten_id=k_id,
                is_active=True,
                group=employee.group
            ).exists()

            if has_common_group:
                return render(request, 'employee-profile.html', context)

        raise PermissionDenied


class EmployeesListView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy aktywny kontekst z sesji (rola, profil_id, id_placówki)
        role, profile_id, k_id = get_active_context(request)
        search_query = request.GET.get('search', '')

        # 1. LOGIKA FILTRACJI ZALEŻNA OD ROLI
        if role == 'director':
            # Dyrektor widzi wszystkich pracowników przypisanych do aktywnej placówki
            teachers = Employee.objects.filter(kindergarten_id=k_id)

        elif role == 'parent':
            # Rodzic widzi tylko nauczycieli grup, do których należą jego dzieci w tej placówce
            parent = get_object_or_404(ParentA, id=profile_id, kindergarten_id=k_id)
            child_groups = Groups.objects.filter(
                kid__parenta=parent,
                kindergarten_id=k_id
            ).distinct()

            teachers = Employee.objects.filter(
                group__in=child_groups,
                kindergarten_id=k_id
            ).distinct()

        else:
            # Nauczyciele zazwyczaj widzą listę współpracowników w tej samej placówce
            if role == 'teacher':
                teachers = Employee.objects.filter(kindergarten_id=k_id)
            else:
                raise PermissionDenied

        # 2. WSPÓLNA LOGIKA (Wyszukiwanie i Paginacja)
        if search_query:
            # Uwaga: first_name i last_name są teraz w modelu User (poprzednia poprawka)
            teachers = teachers.filter(
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        # Optymalizacja zapytań (zapobieganie N+1 dla danych użytkownika i grupy)
        teachers = teachers.select_related('user', 'group').order_by('last_name')

        paginator = Paginator(teachers, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'active_role': role,
        }

        return render(request, 'employees-list.html', context)

    def post(self, request):
        search = request.POST.get('search')
        base_url = reverse('list_teachers')
        if search:
            return redirect(f'{base_url}?search={search}')
        return redirect('list_teachers')


class EmployeeAddView(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        # Pobieramy grupy tylko dla aktywnej placówki
        groups = Groups.objects.filter(kindergarten_id=k_id, is_active=True)
        return render(request, 'employee-add.html', {'groups': groups, 'roles': roles})

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        # Wczytywanie danych
        role_pk = request.POST.get('role')
        salary_str = request.POST.get('salary')
        group_id = request.POST.get('group')
        teacher_email = request.POST.get('email').strip().lower()

        if not teacher_email or not role_pk or not salary_str:
            messages.error(request, 'Wypełnij wymagane pola (Email, Posada, Wynagrodzenie).')
            return redirect('add_teacher')

        try:
            salary = float(salary_str)
            target_role = int(role_pk)

            # Pobieramy lub ustawiamy None dla grupy w ramach placówki
            group = None
            if group_id:
                group = get_object_or_404(Groups, id=group_id, kindergarten_id=k_id)

            with transaction.atomic():
                # 1. Sprawdzamy czy użytkownik o tym mailu już istnieje
                target_user = User.objects.filter(email=teacher_email).first()
                created_new_user = False
                password = None

                if not target_user:
                    # Tworzymy nowego użytkownika
                    password = User.objects.make_random_password()
                    target_user = User.objects.create_user(email=teacher_email, password=password)
                    created_new_user = True
                else:
                    # Użytkownik istnieje - sprawdzamy czy nie ma już profilu pracownika W TEJ placówce
                    if Employee.objects.filter(user=target_user, kindergarten_id=k_id).exists():
                        messages.error(request, f'Ten użytkownik jest już pracownikiem w Twojej placówce.')
                        return redirect('add_teacher')

                # 2. Tworzymy nowy profil Employee przypisany do placówki (k_id)
                new_employee = Employee.objects.create(
                    user=target_user,
                    kindergarten_id=k_id, # Kluczowe dla systemu wieloprofilowego
                    role=target_role,
                    salary=salary,
                    group=group,
                    is_active=True
                )

                # 3. Nadajemy uprawnienie techniczne (jeśli jeszcze nie ma)
                content_type = ContentType.objects.get_for_model(Employee)
                permission = Permission.objects.get(content_type=content_type, codename='is_teacher')
                if not target_user.has_perm('teacher.is_teacher'):
                    target_user.user_permissions.add(permission)

                # 4. Wysyłka e-maila
                if created_new_user:
                    # E-mail powitalny z hasłem dla całkiem nowego konta
                    subject = "Zaproszenie do systemu przedszkola - Nowe konto"
                    template = 'email_to_parent.html' # Twoja nazwa szablonu
                else:
                    # Informacja o dodaniu nowego profilu do istniejącego konta
                    subject = "Dodano nowy profil pracownika"
                    template = 'email_to_parent.html'
                    password = "Twoje dotychczasowe hasło"

                html_content = render_to_string(template, {
                    'password': password,
                    'email': teacher_email,
                    'kindergarten': new_employee.kindergarten.name
                })
                msg = EmailMultiAlternatives(subject, "Zaproszenie", EMAIL_HOST_USER, [teacher_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            messages.success(request, f"Pomyślnie przypisano pracownika {teacher_email} do placówki.")
            return redirect('list_teachers')

        except Exception as e:
            messages.error(request, f'Błąd podczas dodawania: {e}')
            return redirect('add_teacher')


class EmployeeUpdateView(LoginRequiredMixin, View):

    def get(self, request, pk):
        # Pobieramy kontekst placówki
        role, profile_id, k_id = get_active_context(request)

        # Pobieramy profil pracownika w ramach tej samej placówki
        employee = get_object_or_404(Employee, id=pk, kindergarten_id=k_id)

        # --- LOGIKA NAUCZYCIEL (Edycja własnych danych kontaktowych) ---
        if role == 'teacher' and employee.id == profile_id:
            form = TeacherUpdateForm(instance=employee)
            return render(request, 'employee-update.html', {
                'form': form,
                'valid': True,
                'employee': employee
            })

        # --- LOGIKA DYREKTOR (Edycja danych kadrowych pracownika) ---
        elif role == 'director':
            # Pobieramy tylko grupy z TEJ placówki
            groups = Groups.objects.filter(kindergarten_id=k_id, is_active=True)

            return render(request, 'employee-update.html', {
                'employee': employee,
                'roles': roles,
                'groups': groups,
                'valid': False
            })

        raise PermissionDenied

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        employee = get_object_or_404(Employee, id=pk, kindergarten_id=k_id)

        # --- LOGIKA NAUCZYCIEL (POST: Dane Osobowe) ---
        if role == 'teacher' and employee.id == profile_id:
            form = TeacherUpdateForm(request.POST, instance=employee)
            if form.is_valid():
                form.save()
                messages.success(request, 'Zaktualizowano dane kontaktowe.')
                return redirect('teacher-profile', pk=pk)

            return render(request, 'employee-update.html', {
                'form': form, 'valid': True, 'employee': employee
            })

        # --- LOGIKA DYREKTOR (POST: Rola/Wynagrodzenie) ---
        elif role == 'director':
            role_pk = request.POST.get('role')
            salary_str = request.POST.get('salary')
            group_id = request.POST.get('group')

            try:
                if not role_pk or not salary_str:
                    messages.error(request, "Rola i Wynagrodzenie są wymagane.")
                    return redirect('teacher_update', pk=pk)

                new_role = int(role_pk)
                new_salary = float(salary_str)

                # Weryfikacja grupy (musi należeć do placówki)
                if new_role == 2: # Nauczyciel
                    if group_id:
                        group_obj = get_object_or_404(Groups, id=int(group_id), kindergarten_id=k_id)
                        employee.group = group_obj
                    else:
                        messages.error(request, "Nauczyciel musi być przypisany do grupy.")
                        return redirect('teacher_update', pk=pk)
                else:
                    employee.group = None

                employee.role = new_role
                employee.salary = new_salary
                employee.save()

                messages.success(request, 'Dane kadrowe zostały zaktualizowane.')
                return redirect('teacher-profile', pk=pk)

            except ValueError:
                messages.error(request, "Nieprawidłowy format ceny lub roli.")
                return redirect('teacher_update', pk=pk)

        raise PermissionDenied


class EmployeeDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy profil pracownika w ramach TEJ placówki
        employee = get_object_or_404(Employee, id=pk, kindergarten_id=k_id)

        # 1. Odłączamy pracownika od grupy (jeśli był przypisany)
        if employee.group:
            employee.group = None

        # 2. Logiczne usunięcie (Dezaktywacja profilu)
        # Nie usuwamy obiektu User! Tylko wyłączamy ten konkretny profil Employee.
        employee.is_active = False
        employee.save()

        # 3. Opcjonalnie: Usunięcie uprawnienia technicznego,
        # ALE tylko jeśli użytkownik nie ma innych aktywnych profili nauczyciela
        other_active_profiles = Employee.objects.filter(
            user=employee.user,
            is_active=True
        ).exclude(id=employee.id)

        if not other_active_profiles.exists():
            from django.contrib.auth.models import Permission
            permission = Permission.objects.get(codename='is_teacher')
            employee.user.user_permissions.remove(permission)

        messages.success(request, f'Pracownik {employee.user.get_full_name()} został dezaktywowany w tej placówce.')
        return redirect('list_teachers')



class AssignTeachersView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        # Tylko osoba z rolą dyrektora w danej placówce może zarządzać grupami
        if role != 'director':
            raise PermissionDenied

        # Pobieramy profil pracownika, upewniając się, że należy do TEJ placówki
        employee = get_object_or_404(Employee, id=pk, kindergarten_id=k_id)

        # Odbieramy wartość 'group_id' z formularza
        group_id = request.POST.get('group_id')

        try:
            if group_id:
                # KRYTYCZNE: Sprawdzamy, czy wybrana grupa należy do TEJ SAMEJ placówki co dyrektor i pracownik
                selected_group = get_object_or_404(Groups, pk=group_id, kindergarten_id=k_id)
                employee.group = selected_group
                # Używamy employee.user.first_name, bo usunęliśmy dublujące się pole z modelu Employee
                messages.success(request, f"Pomyślnie przypisano {employee.user.first_name} do grupy {selected_group.name}.")
            else:
                # Usunięcie przypisania
                employee.group = None
                messages.success(request, f"Pomyślnie usunięto przypisanie grupy dla {employee.user.first_name}.")

            employee.save()

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas przypisywania grupy: {e}")

        # Powrót na profil pracownika
        return redirect('teacher-profile', pk=employee.pk)



class ChangeEmployeeGroupView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # 1. Pobieramy kontekst sesji i rzutujemy ID na int dla poprawnego porównania
        role, profile_id_raw, k_id = get_active_context(request)

        # Weryfikacja roli
        if role != 'director':
            raise PermissionDenied

        # 2. Pobieramy profil pracownika w ramach aktywnej placówki
        # Zapobiega to edycji pracownika z innego przedszkola
        employee = get_object_or_404(Employee, id=pk, kindergarten_id=k_id)

        # 3. Pobieramy group_id z formularza
        group_id = request.POST.get('group_id')

        try:
            if group_id:
                # KRYTYCZNE: Sprawdzamy, czy wybrana grupa należy do TEJ SAMEJ placówki (k_id)
                # Zapobiega to wstrzyknięciu ID grupy z innej placówki
                selected_group = get_object_or_404(Groups, pk=group_id, kindergarten_id=k_id)
                employee.group = selected_group
                messages.success(request, f"Pomyślnie przypisano pracownika do grupy {selected_group.name}.")
            else:
                # Opcja "Brak grupy"
                employee.group = None
                messages.success(request, f"Pomyślnie usunięto przypisanie grupy.")

            employee.save()

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas przypisywania grupy: {e}")

        # 4. Przekierowanie do profilu pracownika
        return redirect('teacher-profile', pk=employee.id)