from django.contrib import admin
from .models import CompanyProfile, CommonCodes, CustomerProfile


# Register your models here.
@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('business_id', 'business_name', 'xphone', 'is_active')
    search_fields = ('business_id', 'business_name', 'xphone', 'bin_number')


