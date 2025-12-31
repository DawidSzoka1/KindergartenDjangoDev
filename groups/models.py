from django.db import models
from director.models import Director, GroupPhotos, MealPhotos, KindergartenOwnedModel
from django.core.validators import MinValueValidator


# Create your models here.
class Groups(KindergartenOwnedModel):
    name = models.CharField(max_length=128)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    capacity = models.IntegerField(null=True, validators=[MinValueValidator(limit_value=1)])
    photo = models.ForeignKey(GroupPhotos, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)
    yearbook = models.IntegerField(null=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'
    @property
    def current_students_count(self):
        """
        Zwraca aktualną liczbę aktywnych dzieci w grupie.

        Uwaga: Ta metoda jest szybka, ale nie powinna być używana w pętlach w szablonie,
        jeśli QuerySet nie został wcześniej wzbogacony przez .annotate() (jak robisz w GroupsListView).
        """
        return self.kid_set.filter(is_active=True).count()

    @property
    def capacity_fill_percent(self):
        """
        Oblicza procent wypełnienia grupy. Zwraca 0, jeśli pojemność nie jest ustawiona lub jest równa 0.
        """
        if self.capacity and self.capacity > 0:
            count = self.current_students_count
            # Użyj atrybutu child_count jeśli QuerySet był annotowany
            if hasattr(self, 'child_count'):
                count = self.child_count

            return min(100, (count / self.capacity) * 100)
        return 0

    @property
    def is_full(self):
        """
        Sprawdza, czy grupa osiągnęła maksymalną pojemność.
        """
        return self.current_students_count >= self.capacity

    def get_active_kids(self):
        """
        Zwraca QuerySet aktywnych dzieci przypisanych do tej grupy.
        """
        # Zakładam, że model dziecka ma ForeignKey do modelu Groups i nazywa się 'kid_set' (domyślna nazwa).
        return self.kid_set.filter(is_active=True).order_by('last_name', 'first_name')

    # Przykładowa metoda, jeśli potrzebujesz statusu wizualnego
    def get_status_tag(self):
        """
        Zwraca status grupy na podstawie jej aktywności.
        """
        if self.is_active:
            return 'Aktywna'
        return 'Archiwalna'