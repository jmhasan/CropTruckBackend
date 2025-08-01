from django.db import models
from django.contrib.auth.models import AbstractUser

# from masterdata.models import CompanyProfile

user_role = (
    ('Admin', 'Admin'),
    ('Staff', 'Staff')
)


#  Custom User Model
class CustomUser(AbstractUser):
    business_id = models.IntegerField(null=True,blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    user_role = models.CharField(max_length=100, choices= user_role)
    profile_pic = models.ImageField(upload_to='profile_pic', blank=True, null=True)