from django.shortcuts import render
from django.views import View
from accounts.models import User
from director.models import Director
# Create your views here.


class Home(View):
    def get(self, request):

        users = User.objects.get(email=f"{request.user.email}"
)
        return render(request, 'home.html', {'users': users})
