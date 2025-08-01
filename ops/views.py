from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from masterdata.serializers import CustomerProfileResponseSerializer
from ops.models import TokenNumber
from ops.serializers import TokenSerializer, BookingSerializer, BookingCreateSerializer, CustomerProfileSerializer
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from masterdata.models import CompanyProfile, CustomerProfile  # Make sure import is correct
# Create your views here.

from datetime import datetime

from utils.customlist import CustomListAPIView
from utils.response import APIResponse


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def token_generate(request):
    try:
        count = int(request.data.get('number_of_tokens', 1))
        if count <= 0:
            return Response({"detail": "number_of_tokens must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({"detail": "Invalid number_of_tokens."}, status=status.HTTP_400_BAD_REQUEST)

    # Get current year suffix
    year_suffix = datetime.now().strftime('%y')  # '25' for 2025

    # Get last token number for this year
    last_token = TokenNumber.objects.filter(token_no__startswith=year_suffix).order_by('-token_no').first()
    if last_token:
        last_seq = int(last_token.token_no.split('-')[1])
    else:
        last_seq = 0

    business = CompanyProfile.objects.get(pk=request.user.business_id)

    new_tokens = []
    for i in range(count):
        sequence_number = last_seq + i + 1
        token_str = f"{year_suffix}-{sequence_number:05d}"

        token = TokenNumber.objects.create(
            token_no=token_str,
            created_by=request.user,
            updated_by=request.user,
            business_id=business,
            xstatus='Pending'
        )
        new_tokens.append(token)

    serializer = TokenSerializer(new_tokens, many=True)
    return Response({
        "message": f"{count} tokens generated successfully.",
        "tokens": serializer.data
    }, status=status.HTTP_201_CREATED)


# class PendingToken(generics.ListAPIView):
#     queryset = TokenNumber.objects.filter(xstatus='Pending').order_by('token_no')
#     serializer_class = TokenSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['token_no',]

@permission_classes([IsAuthenticated])
class PendingToken(CustomListAPIView):
    queryset = TokenNumber.objects.filter(xstatus='Pending').order_by('token_no')
    serializer_class = TokenSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['token_no',]

    def get_success_message(self):
        return "Pending tokens retrieved successfully"


@permission_classes([IsAuthenticated])
class CountedToken(CustomListAPIView):
    queryset = TokenNumber.objects.filter(xstatus='Counted').order_by('token_no')
    serializer_class = TokenSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['token_no',]

    def get_success_message(self):
        return "Counted tokens retrieved successfully"

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def sack_number_input(request, token_no):
    business_id = request.user.business_id
    try:
        snippet = TokenNumber.objects.get(business_id=business_id, token_no=token_no)
    except TokenNumber.DoesNotExist:
        return APIResponse.not_found("Token not found")

    if request.method == 'GET':
        print(request.business_id)  # call middleware
        serializer = TokenSerializer(snippet)
        return APIResponse.success(
            data=serializer.data,
            message="Token retrieved successfully"
        )

    elif request.method == 'PUT':
        serializer = TokenSerializer(snippet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.validated_data['xstatus'] = 'Counted'
            updated_token = serializer.save(updated_by=request.user)
            return APIResponse.updated(
                data=serializer.data,
                message="Token updated successfully"
            )
        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Token update failed"
        )

    elif request.method == 'DELETE':
        snippet.delete()
        return APIResponse.deleted("Token deleted successfully")


@permission_classes([IsAuthenticated])
class CustomerSearch(APIView):
    """
    Search for existing customer by mobile number
    """

    def get(self, request, format=None):
        try:
            mobile = request.query_params.get('xmobile')
            if not mobile:
                return APIResponse.error(
                    message="Mobile number is required",
                    status_code=400
                )

            # Validate mobile number format
            mobile_validator = RegexValidator(
                regex=r'^01[3-9]\d{8}$',
                message='Enter a valid Bangladeshi mobile number (e.g. 017XXXXXXXX).'
            )

            try:
                mobile_validator(mobile)
            except ValidationError as e:
                return APIResponse.error(
                    message=str(e.message),
                    status_code=400
                )

            # Validate user's business
            try:
                business = CompanyProfile.objects.get(pk=request.user.business_id)
            except CompanyProfile.DoesNotExist:
                return APIResponse.error(
                    message="Business profile not found",
                    status_code=404
                )

            # Search for customer
            try:
                customer = CustomerProfile.objects.get(
                    business_id=business,
                    xmobile=mobile
                )

                serializer = CustomerProfileResponseSerializer(customer)

                return APIResponse.success(
                    data=serializer.data,
                    message="Customer profile found"
                )

            except CustomerProfile.DoesNotExist:
                return APIResponse.success(
                    data=None,
                    message="No customer found with this mobile number. You can create a new customer."
                )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer search failed: {str(e)}")
            return APIResponse.error(
                message="Failed to search customer. Please try again.",
                status_code=500
            )


@permission_classes([IsAuthenticated])
class BookingCreate(APIView):
    """
    Create booking and automatically handle customer creation/update
    """

    def post(self, request, format=None):
        try:
            with transaction.atomic():
                # Validate user's business
                try:
                    business = CompanyProfile.objects.get(pk=request.user.business_id)
                except CompanyProfile.DoesNotExist:
                    return APIResponse.error(
                        message="Business profile not found",
                        status_code=404
                    )

                # Create serializer with context
                serializer = BookingCreateSerializer(
                    data=request.data,
                    context={'request': request}
                )

                if serializer.is_valid():
                    # Save booking (this will automatically handle customer creation/update)
                    booking = serializer.save(business_id=business)

                    # Get the customer profile for response
                    customer_profile = None
                    if booking.customer_code:
                        try:
                            customer_profile = CustomerProfile.objects.get(
                                business_id=business,
                                customer_code=booking.customer_code
                            )
                        except CustomerProfile.DoesNotExist:
                            pass

                    # Prepare response data
                    response_data = {
                        'booking_no': booking.booking_no,
                        'customer_code': booking.customer_code,
                        'xmobile': booking.xmobile,
                        'xname': booking.xname,
                        'father_name': booking.father_name,
                        'district_name': booking.district_name,
                        'division_name': booking.division_name,
                        'upazila_name': booking.upazila_name,
                        'union_name': booking.union_name,
                        'village': booking.village,
                        'post_office': booking.post_office,
                        'xadvance': str(booking.xadvance),
                        'xsack': booking.xsack,
                        'created_at': booking.created_at,
                        'updated_at': booking.updated_at,
                        'customer_profile': CustomerProfileSerializer(
                            customer_profile).data if customer_profile else None
                    }

                    return APIResponse.created(
                        data=response_data,
                        message="Booking created successfully"
                    )
                else:
                    return APIResponse.validation_error(
                        errors=serializer.errors,
                        message="Booking creation failed"
                    )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Booking creation failed: {str(e)}")
            return APIResponse.error(
                message="Booking creation failed. Please try again.",
                status_code=500
            )

# views.py - Additional utility view for customer profile management
@permission_classes([IsAuthenticated])
class CustomerProfileDetail(APIView):
    """
    Get customer profile by customer code
    """

    def get(self, request, customer_code, format=None):
        try:
            # Validate user's business
            try:
                business = CompanyProfile.objects.get(pk=request.user.business_id)
            except CompanyProfile.DoesNotExist:
                return APIResponse.error(
                    message="Business profile not found",
                    status_code=404
                )

            # Get customer profile
            try:
                customer = CustomerProfile.objects.get(
                    business_id=business,
                    customer_code=customer_code,
                    is_active=True
                )

                serializer = CustomerProfileSerializer(customer)

                return APIResponse.success(
                    data=serializer.data,
                    message="Customer profile retrieved successfully"
                )

            except CustomerProfile.DoesNotExist:
                return APIResponse.error(
                    message="Customer profile not found",
                    status_code=404
                )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer profile retrieval failed: {str(e)}")
            return APIResponse.error(
                message="Failed to retrieve customer profile. Please try again.",
                status_code=500
            )