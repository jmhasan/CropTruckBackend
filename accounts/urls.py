from .views import ChartofAccountsViewSet, SubAccountViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts import views


# Create a router and register our ViewSets with it.
# router = DefaultRouter()
# router.register(r'chartofaccounts', views.ChartofAccountsViewSet, basename='chartofaccounts')
#
# # The API URLs are now determined automatically by the router.
# urlpatterns = [
#     path('', include(router.urls)),
# ]

chartof_accounts_list = ChartofAccountsViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
chartof_accounts_detail = ChartofAccountsViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

subaccount_list = SubAccountViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

subaccount_detail = SubAccountViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('chartofaccounts/', chartof_accounts_list, name='chartofaccounts-list'),
    path('chartofaccounts/<str:xacc>/', chartof_accounts_detail, name='chartofaccounts-detail'),
    path('subaccounts/<str:xacc>/', subaccount_list, name='subaccount-list'),
    path('subaccounts/<str:xacc>/<str:xsub>/', subaccount_detail, name='subaccount-detail'),
]








