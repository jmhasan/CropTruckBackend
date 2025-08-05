from django.contrib import admin
from django.urls import path, include
from ops import views
from ops.views import PendingToken, CountedToken

urlpatterns = [
    path('token/generate/', views.token_generate),
    path('token/pending/', PendingToken.as_view(), name='api-pending-token'),
    path('token/counted/', CountedToken.as_view(), name='api-pending-token'),
    path('token/sack_input/<str:token_no>/', views.sack_number_input),
    # Search customer by mobile
    path('customers/search/', views.CustomerSearch.as_view(), name='customer_search'),
    # Get customer profile by customer code
    path('customers/<str:customer_code>/', views.CustomerProfileDetail.as_view(), name='customer_detail'),
    # Create booking (automatically handles customer)
    path('bookings/create/', views.BookingCreate.as_view(), name='booking_create'),
    path('bookings/list/', views.BookingList.as_view(), name='booking -list'),
    # Certificate API List
    path('certificates/create/', views.CertificateCreateAPIView.as_view(), name='certificate-create'),
    path('certificates/list/', views.CertificateListAPIView.as_view(), name='certificate-list'),
    path('certificates/<str:token_no>/', views.CertificateDetailAPIView.as_view(), name='certificate-detail'),
    path('certificate-details/create/<str:token_no>/', views.BulkCreateCertificateDetailsView.as_view(), name='bulk-create-certificate-details'),



]

