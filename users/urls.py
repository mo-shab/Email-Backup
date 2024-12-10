from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetView, folder_emails_view, email_detail_view

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    # Password Reset URLs

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), 
         name='password_reset_complete'),
    #path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('users/', views.admin_user_list, name='admin_user_list'),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('email-configuration/', views.email_configuration, name='email_configuration'),
    path('fetch-folders/', views.fetch_folders_view, name='fetch_folders'),
    path('fetch-emails/', views.fetch_emails_view, name='fetch-emails'),
    path('emails/', folder_emails_view, name='folder_emails'),
    path('emails/<str:folder>/<int:email_id>/', email_detail_view, name='email_detail'),
]