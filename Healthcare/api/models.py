from django.db import models
from django.contrib.auth.models import User

class Health(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    no = models.IntegerField(null=True,blank=True)
    Email = models.CharField(null=True,blank=True)

    def __str__(self):
        return self.name