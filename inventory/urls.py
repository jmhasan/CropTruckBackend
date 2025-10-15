from django.urls import path
from inventory import views

urlpatterns=[
    path('certificate-post/<str:token_no>/',views.CertificatePost.as_view(), name='certificate-post'),
    path('current-stock/', views.CurrentStock.as_view(), name='current-stock-status'),
    path('transfer-order-entry/', views.TransferEntry.as_view(), name='transfer-order-entry'),

]