from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("", views.ClinicaLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("recepcao/", views.painel_recepcionista_view, name="painel_recepcionista"),
    path("medico/", views.painel_medico_view, name="painel_medico"),
    path("ti/", views.painel_admin_ti_view, name="painel_admin_ti"),
]