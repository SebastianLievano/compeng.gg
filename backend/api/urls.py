from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

from django.urls import include, path

app_name = 'api'

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='jwt_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='jwt_verify'),

    path('auth/discord/', views.discord),

    path('auth/session/', views.session),
]
