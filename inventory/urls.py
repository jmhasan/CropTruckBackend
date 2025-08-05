from django.urls import path
from inventory import views

urlpatterns=[
    path('certificate-post/<str:token_no>/',views.CertificatePost.as_view(), name='certificate-post')

]