from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Customize the UserAdmin to modify how the User model appears in the admin panel
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

# Register the customized admin for the User model
admin.site.unregister(User)  # Unregister the default registration
admin.site.register(User, CustomUserAdmin)