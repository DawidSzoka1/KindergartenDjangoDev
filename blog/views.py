from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from .models import Post
from parent.models import ParentA
from director.models import Kid
from django.contrib.auth.models import Permission
import calendar
from django.utils import timezone
from calendar import HTMLCalendar
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)


class CalendarKid(LoginRequiredMixin, View):
    def get(self, request, pk):
        permissions = Permission.objects.filter(user=request.user.id)
        month_number = int(timezone.now().month)
        year = int(timezone.now().year)
        cal = HTMLCalendar().formatyear(year, month_number)
        if permissions[0].name == 'director permission':
            kid = Kid.objects.get(id=pk)
            return render(request, 'calendar.html', {'kid': kid})
        elif permissions[0].name == 'parent permission':
            parent = ParentA.objects.get(user=request.user.id)
            kids = parent.kid_set.all()
            return render(request, 'calendar.html', {'kids': kids, 'cal': cal})


class Home(View):
    def get(self, request):

        # users = User.objects.get(email=f"{request.user.email}"
        return render(request, 'home.html')


class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'


class PostCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = Post
    fields = ['title', 'content', 'image']
    template_name = 'post_form.html'

    def get_form(self, form_class=None):
        form = super(PostCreateView, self).get_form(form_class)
        form.fields['image'].required = False
        return form

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = "director.is_director"
    model = Post
    fields = ['title', 'content', 'image']
    template_name = 'post_form.html'

    def get_form(self, form_class=None):
        form = super(PostUpdateView, self).get_form(form_class)
        form.fields['image'].required = False
        return form

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    permission_required = "director.is_director"
    model = Post
    template_name = 'post_delete_confirm.html'
    context_object_name = 'post'
    success_url = '/wydarzenia/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False
