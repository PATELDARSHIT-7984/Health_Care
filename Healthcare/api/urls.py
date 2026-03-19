from django.urls import path
from .views import HealthcenterView

#this is for Sessionbased Authentication
from rest_framework.authtoken.views import obtain_auth_token

#this for JWTAuthentication
# from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

# this for adding swagger in path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Healthcare API",
        default_version='v1',
        description="API documentation for Healthcare project"
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('Health/<str:Email>/',HealthcenterView.as_view()),
    path('Health/',HealthcenterView.as_view()),

    #this path for Sessionbased Authentication
    path('login/',obtain_auth_token),

    #this path for JWTAuthentication
    # path('login/',TokenObtainPairView.as_view(),name='login'),
    # path('refresh/',TokenRefreshView.as_view(),name='refresh'),

    path('swagger/',schema_view.with_ui('swagger',cache_timeout=0),name='swagger-ui')
]