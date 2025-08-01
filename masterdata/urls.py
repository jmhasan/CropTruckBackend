from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('common-codes/add/', views.CommonCodesAdd.as_view(), name='common-code-add'),
    path('common-codes/list/', views.CommonCodesList.as_view(), name='common-code-list'),
    path('geo/divisions/', views.DivisionListView.as_view(), name='divisions-list'),
    path('geo/locations-all/', views.GeoLocationAll.as_view(), name='geolocation-all-list'),
    path('geo/districts/<str:division_name>/', views.DistrictListView.as_view(), name='districts-list'),
    path('geo/upazilas/<str:division_name>/<str:district_name>/', views.UpazilaListView.as_view(),name='upazilas-list'),
    path('geo/unions/<str:division_name>/<str:district_name>/<str:upazila_name>/',views. UnionListView.as_view(),
         name='unions-list'),
    # Customer CRUD operations
    path('customers/create/', views.CustomerProfileCreate.as_view(), name='customer-create'),
    path('customers/list/', views.CustomerProfileList.as_view(), name='customer-list'),
    path('customers/update/<str:customer_code>/', views.CustomerProfileUpdate.as_view(), name='customer-update'),


]

