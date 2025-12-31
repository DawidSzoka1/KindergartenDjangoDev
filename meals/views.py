from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import Meals
from django.core.exceptions import PermissionDenied
from director.models import Director, MealPhotos
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import (
    ListView,
)
from blog.views import get_active_context


# Create your views here.


class MealAddView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy k_id (ID placówki) z aktywnego kontekstu sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy ikony posiłków przypisane do tej placówki
        photos = MealPhotos.objects.filter(kindergarten_id=k_id, is_active=True)

        if photos.exists():
            return render(request, 'meal-add.html', {'photos': photos})

        messages.info(request, 'Najpierw musisz dodać ikonę dla posiłków w tej placówce.')
        return redirect('photo_add')

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        photo_id = request.POST.get('photo')
        per_day = request.POST.get('per_day')
        name = request.POST.get('name')
        description = request.POST.get('description')

        # Weryfikujemy, czy wybrana ikona należy do tej placówki
        image = get_object_or_404(MealPhotos, id=int(photo_id), kindergarten_id=k_id)

        if image and name and per_day:
            try:
                # Tworzymy posiłek przypisany do placówki (kindergarten_id)
                new_meal = Meals.objects.create(
                    name=name,
                    description=description if description else "",
                    kindergarten_id=k_id, # Przypisanie do przedszkola
                    per_day=float(per_day),
                    photo=image
                )

                messages.success(request, f'Poprawnie dodano posiłek: {new_meal.name}')
                return redirect('list_meals')

            except ValueError:
                messages.error(request, 'Cena za dzień musi być liczbą.')
                return redirect('add_meal')

        messages.error(request, 'Wszystkie wymagane pola muszą być wypełnione.')
        return redirect('add_meal')


class MealsListView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy aktywny kontekst sesji
        role, profile_id, k_id = get_active_context(request)

        # Filtrujemy posiłki w ramach aktywnej placówki
        meals_qs = Meals.objects.for_kindergarten(k_id).filter(is_active=True)

        # Logika widoczności zależna od roli (opcjonalnie)
        if role == 'director':
            # Dyrektor widzi wszystko w swojej placówce
            meals = meals_qs.order_by('-id')
        elif role == 'parent':
            # Rodzic widzi posiłki przypisane do jego dzieci w tej placówce
            parent = get_object_or_404(ParentA, id=profile_id)
            # Pobieramy unikalne ID posiłków dzieci rodzica
            meal_ids = parent.kids.filter(kindergarten_id=k_id, is_active=True).values_list('kid_meals', flat=True).distinct()
            meals = meals_qs.filter(id__in=meal_ids).order_by('name')
        elif role == 'teacher':
            # Nauczyciel widzi posiłki, które są aktualnie wybrane dla dzieci w jego grupie
            teacher = get_object_or_404(Employee, id=profile_id)
            if teacher.group:
                meal_ids = Kid.objects.filter(group=teacher.group, is_active=True).values_list('kid_meals', flat=True).distinct()
                meals = meals_qs.filter(id__in=meal_ids).order_by('name')
            else:
                meals = Meals.objects.none()
        else:
            raise PermissionDenied

        # Paginacja
        paginator = Paginator(meals, 8)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'meals-list.html', {
            'page_obj': page_obj,
            'active_role': role
        })


class MealsUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy posiłek, upewniając się, że należy do TEJ placówki
        meal = get_object_or_404(Meals, id=pk, kindergarten_id=k_id, is_active=True)

        # Pobieramy ikony posiłków dostępne w tej placówce
        photos = MealPhotos.objects.filter(kindergarten_id=k_id, is_active=True)

        return render(request, 'meal-update.html', {
            'meal': meal,
            'current_photo': meal.photo,
            'photos': photos
        })

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Weryfikujemy istnienie posiłku w ramach placówki przed edycją
        meal = get_object_or_404(Meals, id=pk, kindergarten_id=k_id, is_active=True)

        name = request.POST.get("name")
        description = request.POST.get("description")
        per_day = request.POST.get("per_day")
        photo_id = request.POST.get("photo")

        if name and per_day and photo_id:
            try:
                # Weryfikujemy, czy nowo wybrana ikona również należy do tej placówki
                new_photo = get_object_or_404(MealPhotos, id=int(photo_id), kindergarten_id=k_id)

                meal.name = name
                meal.description = description if description else ""
                meal.per_day = float(per_day)
                meal.photo = new_photo
                meal.save()

                messages.success(request, f"Zaktualizowano posiłek: {meal.name}")
                return redirect('list_meals')

            except (ValueError, TypeError):
                messages.error(request, "Cena musi być liczbą.")
                return redirect('meals_update', pk=pk)

        messages.error(request, "Wypełnij wymagane pola.")
        return redirect('meals_update', pk=pk)


class MealDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        # Pobieramy posiłek, upewniając się, że należy do aktywnej placówki
        #
        meal = get_object_or_404(Meals, id=pk, kindergarten_id=k_id, is_active=True)

        # Logika uprawnień oparta na rolach
        if role == 'director':
            # Dyrektor zawsze widzi szczegóły posiłków w swojej placówce
            return render(request, 'meal-details.html', {'meal': meal})

        elif role == 'teacher':
            # Nauczyciel może widzieć szczegóły, jeśli posiłek jest przypisany
            # do jakiegokolwiek dziecka w jego grupie
            teacher = get_object_or_404(Employee, id=profile_id)
            if teacher.group and Kid.objects.filter(group=teacher.group, kid_meals=meal).exists():
                return render(request, 'meal-details.html', {'meal': meal})

        elif role == 'parent':
            # Rodzic widzi szczegóły tylko tych posiłków, które jedzą jego dzieci
            parent = get_object_or_404(ParentA, id=profile_id)
            if parent.kids.filter(kid_meals=meal, kindergarten_id=k_id).exists():
                return render(request, 'meal-details.html', {'meal': meal})

        raise PermissionDenied


class MealDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        # Weryfikacja roli dyrektora dla aktywnej sesji
        if role != 'director':
            raise PermissionDenied

        # Pobieramy posiłek upewniając się, że należy do tej placówki
        meal = get_object_or_404(Meals, id=pk, kindergarten_id=k_id, is_active=True)

        # 1. Odłączamy posiłek od aktywnych dzieci w ramach tej placówki
        # Robimy to tylko dla dzieci z tej samej placówki
        kids_with_this_meal = meal.kid_set.filter(is_active=True, kindergarten_id=k_id)

        # Masowa aktualizacja dla wydajności
        kids_with_this_meal.update(kid_meals=None)

        # 2. Usuwanie logiczne (Soft Delete)
        # Zamiast meal.delete(), ustawiamy is_active na False
        meal.is_active = False
        meal.save()

        messages.success(request, f'Pomyślnie usunięto posiłek: {meal.name}')
        return redirect('list_meals')
