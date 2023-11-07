"""
URL configuration for compeng_gg project.

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
from django.urls import include, path
from django.views.generic import TemplateView

from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", TemplateView.as_view(template_name="homepage.html"),
         name="homepage"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt",
                                            content_type="text/plain")),
    path("queue/", include("queue_webhook.urls")),
    path("docs/", include("docs.urls")),
    path("lab5/", include("lab5.urls")),
    path('auth/', include('social_django.urls', namespace='auth')),

    path('@<str:username>/', views.profile, name='profile'),
    path("login/", auth_views.LoginView.as_view(), name='login'),
    path("login-redirect/", views.login_redirect, name='login_redirect'),

    path("admin/", admin.site.urls),
]
