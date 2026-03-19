from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user,created= User.objects.get_or_create(username = "darshit")
user.set_password('1234')
user.save()
token,created = Token.objects.get_or_create(user=user)

print(token.key)    