from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import CustomUser

# Register your models here.



class CustomUserAdmin(UserAdmin):
    list_display = ('username','first_name')

    # readonly_fields = ('zid')
    # filter_horizontal = ()
    # list_filter =  ()
    # fieldsets = ()
    list_per_page = 20
    ordering = ["-id"]
    # search_fields = ["foreign_key__related_zone"]

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': (('first_name', 'last_name', 'phone','profile_pic'),)}),
        ('Permissions',
         {
             "classes": ["collapse"],
            'fields': ('business_id','user_role','is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
         }),
        ('Important dates',
         {
             "classes": ["collapse"],
             'fields': ('last_login', 'date_joined', 'date_of_birth')
         }),
    )
admin.site.register(CustomUser, CustomUserAdmin)