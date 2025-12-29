from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('club/<int:pk>/', views.ClubDetailView.as_view(), name='club_detail'),
    path('export/', views.export_rankings_csv, name='export_rankings'),
]
