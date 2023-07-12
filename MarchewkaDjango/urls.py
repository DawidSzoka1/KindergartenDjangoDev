"""
URL configuration for MarchewkaDjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from director.views import AddKid, Kids, GroupsView, DirectorProfile, AddGroup, \
    PaymentPlans, AddPaymentsPlan, ChangeInfo, InviteParent, AddMeals, AllMeals, \
    DetailsKid
from accounts.views import Register
from blog.views import Home, PostListView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", Home.as_view(), name="home_page"),
    path("wydarzenia/", PostListView.as_view(), name='post_list_view'),
    path("wydarzenie/szczegoly/<int:pk>/", PostDetailView.as_view(), name='post_detail_view'),
    path("wydarzenie/update/<int:pk>/", PostUpdateView.as_view(), name='post_update'),
    path("wydarzenie/nowe/", PostCreateView.as_view(), name='post_create_view'),
    path("wydarzenie/delete/<int:pk>/", PostDeleteView.as_view(), name='post_delete'),
    path('addKid/', AddKid.as_view(), name='addKid'),
    path("login/", auth_views.LoginView.as_view(template_name='login.html'), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name='logout.html'), name="logout"),
    path("settings/", DirectorProfile.as_view(), name="director_profile"),
    path("kids/", Kids.as_view(), name="kids"),
    path("groups/", GroupsView.as_view(), name="groups"),
    path('addGroup/', AddGroup.as_view(), name='addGroup'),
    path('paymentsPlans/', PaymentPlans.as_view(), name='payments_plans'),
    path('add/payments/plans/', AddPaymentsPlan.as_view(), name='add_payment_plans'),
    path('change/info/', ChangeInfo.as_view(), name='change_info'),
    path('invite/parent/', InviteParent.as_view(), name='invite_parent'),
    path('add/meal/', AddMeals.as_view(), name='add_meals'),
    path('all/meals/', AllMeals.as_view(), name='all_meals'),
    path('register/', Register.as_view(), name='register'),
    path('kid/details/', DetailsKid.as_view(), name='kid_details'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ),
         name='password_reset_complete'),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
