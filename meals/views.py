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


# Create your views here.


class MealAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = Director.objects.get(user=request.user.id)
        photos = director.mealphotos_set.filter(is_active=True)
        if photos:
            return render(request, 'meal-add.html', {'photos': photos})
        messages.info(request, 'Najpierwsz musisz dodac jakas iconke')
        return redirect('photo_add')

    def post(self, request):
        director = request.user.director
        photo_id = request.POST.get('photo')
        per_day = request.POST.get('per_day')
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = get_object_or_404(MealPhotos, id=int(photo_id))
        if image and name and description and per_day:
            new_meal = Meals.objects.create(name=name, description=description, principal=director,
                                            per_day=float(per_day), photo=image)

        elif image and name and per_day:
            new_meal = Meals.objects.create(name=name, principal=director, per_day=float(per_day), photo=image)

        else:
            messages.error(request, 'Wszystkie pola musza byc wypelnione')
            return redirect('add_meal')

        messages.success(request, f'poprawnie dodano posilek o nazwie {new_meal.name}')
        return redirect('list_meals')


class MealsListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        meals = Meals.objects.filter(principal__user=request.user).filter(is_active=True).order_by('-id')
        paginator = Paginator(meals, 8)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        return render(request, 'meals-list.html', {'page_obj': page_obj})


class MealsUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        director = Director.objects.get(user=request.user.id)
        meal = Meals.objects.filter(is_active=True).filter(id=int(pk)).filter(principal=director).first()
        if meal:
            current_photo = meal.photo
            photos = director.mealphotos_set.filter(is_active=True)
            return render(request, 'meal-update.html',
                          {
                              'meal': meal,
                              'current_photo': current_photo,
                              'photos': photos
                          })
        raise PermissionDenied

    def post(self, request, pk):
        name = request.POST.get("name")
        description = request.POST.get("description")
        per_day = request.POST.get("per_day")
        photo = request.POST.get("photo")
        photo = get_object_or_404(MealPhotos, id=int(photo))
        meal = Meals.objects.filter(is_active=True).filter(id=int(pk)).first()
        if meal:
            if name and description and per_day and photo:
                meal.name = name
                meal.description = description
                meal.per_day = per_day
                meal.photo = photo
                meal.save()

                return redirect('list_meals')
            messages.error(request, "Wypelnij wszystkie pola")
            return redirect('meals_update', pk=pk)
        raise PermissionDenied


class MealDeleteView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        meal = get_object_or_404(Meals, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if meal.principal == director:
            for kid in meal.kid_set.filter(is_active=True):
                kid.kid_meals = None
                kid.save()
            meal.delete()
            messages.success(request,
                             f'Popprawnie usunieto posilek {meal}')
            return redirect('list_meals')
        raise PermissionDenied
