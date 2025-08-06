from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.utils import timezone
from masterdata.serializers import CustomerProfileResponseSerializer
from ops.models import TokenNumber, Booking, Certificate, CertificateDetails
from ops.serializers import TokenSerializer, BookingSerializer, BookingCreateSerializer, CustomerProfileSerializer, \
    CertificateSerializer, CertificateCreateSerializer, CertificateDetailsBulkCreateSerializer, \
    CertificateDetailsResponseSerializer, CertificateReadyListSerializer
from masterdata.models import CompanyProfile, CustomerProfile  # Make sure import is correct
from datetime import datetime
from ops.services import CertificateService
from utils.customlist import CustomListAPIView
from utils.response import APIResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated



@api_view(['POST'])
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


class PendingToken(CustomListAPIView):
    queryset = TokenNumber.objects.filter(xstatus='Pending').order_by('token_no')
    serializer_class = TokenSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['token_no',]

    def get_success_message(self):
        return "Pending tokens retrieved successfully"


class CountedToken(CustomListAPIView):
    queryset = TokenNumber.objects.filter(xstatus='Counted').order_by('token_no')
    serializer_class = TokenSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['token_no',]

    def get_success_message(self):
        return "Counted tokens retrieved successfully"

@api_view(['GET', 'PUT', 'DELETE'])
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


class BookingCreate(APIView):

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


class BookingList(CustomListAPIView):
    queryset = Booking.objects.filter(xstatus='Pending').order_by('-booking_no')
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking_no','xstatus','xmobile',]

    def get_success_message(self):
        return "Pending tokens retrieved successfully"



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


class CertificateCreateAPIView(APIView):
    def post(self, request):
        # 1️⃣ Get business from user profile
        try:
            business = CompanyProfile.objects.get(pk=request.user.business_id)
        except CompanyProfile.DoesNotExist:
            return APIResponse.error(
                message="User business profile not found",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except AttributeError:
            return APIResponse.error(
                message="User does not have business_id attribute",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 2️⃣ Validate request data
        serializer = CertificateCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Validation failed"
            )

        token_no = serializer.validated_data.get('token_no')

        # 3️⃣ Check token availability
        if not TokenNumber.objects.filter(
            business_id=business,
            token_no=token_no,
            xstatus='Counted'  # Ensure token is available
        ).exists():
            return APIResponse.error(
                message=f"Token {token_no} is not Counted or already used for your business",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 4️⃣ Create certificate and handle exceptions
        try:
            result = CertificateService.create_certificate(
                validated_data=serializer.validated_data,
                user=request.user
            )

            certificate = result['certificate']
            customer = result['customer']
            is_new_customer = result['is_new_customer']
            business = result['business']

            # Prepare response payload
            response_data = {
                'certificate': CertificateSerializer(certificate).data,
                'customer': CustomerProfileSerializer(customer).data,
                'business_name': getattr(business, 'name', str(business)),
                'is_new_customer': is_new_customer,
            }

            return APIResponse.created(
                data=response_data,
                message="Certificate created successfully"
            )

        except Exception as e:
            return APIResponse.error(
                message=f"Failed to create certificate: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CertificateListAPIView(CustomListAPIView):
    queryset = Certificate.objects.all().order_by('-token_no')
    serializer_class = CertificateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['xmobile','xstatus','token_no',]

    def get_success_message(self):
        return "Certificates retrieved successfully"


class CertificateReadyList(CustomListAPIView):
    queryset = Certificate.objects.all().order_by('-token_no')
    serializer_class = CertificateReadyListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['xmobile', 'xstatus', 'token_no']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        token_numbers = list(queryset.values_list('token_no', flat=True))
        count = len(token_numbers)

        return Response({
            "success": True,
            "status_code": 200,
            "message": self.get_success_message(),
            "data": token_numbers,
            "meta": {
                "count": count
            }
        })


class CertificateDetailAPIView(APIView):
    def get_object(self, token_no, user):
        # 1️⃣ Validate user's business
        try:
            business = CompanyProfile.objects.get(pk=user.business_id)
        except (CompanyProfile.DoesNotExist, AttributeError):
            return None, "User business profile not found"

        # 2️⃣ Retrieve certificate for this business
        try:
            certificate = Certificate.objects.get(business_id=business, token_no=token_no)
            return certificate, None
        except Certificate.DoesNotExist:
            return None, "Certificate not found for your business"

    # --------------- GET (Retrieve) ----------------
    def get(self, request, token_no):
        certificate, error = self.get_object(token_no, request.user)

        if error:
            return APIResponse.not_found(message=error)

        serializer = CertificateSerializer(certificate)
        return APIResponse.success(
            data=serializer.data,
            message="Certificate retrieved successfully"
        )

    # --------------- PUT (Update) ----------------
    def put(self, request, token_no):
        certificate, error = self.get_object(token_no, request.user)

        if error:
            return APIResponse.not_found(message=error)

        serializer = CertificateSerializer(certificate, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save(updated_by=request.user, updated_at=timezone.now())
            return APIResponse.updated(
                data=serializer.data,
                message="Certificate updated successfully"
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Validation failed"
        )

    # --------------- DELETE ----------------
    def delete(self, request, token_no):
        certificate, error = self.get_object(token_no, request.user)

        if error:
            return APIResponse.not_found(message=error)

        certificate.delete()
        return APIResponse.deleted(
            message="Certificate deleted successfully"
        )


class BulkCreateCertificateDetailsView(APIView):
    def post(self, request, token_no):
        serializer = CertificateDetailsBulkCreateSerializer(
            data=request.data,
            context={'request': request, 'token_no': token_no}
        )

        if serializer.is_valid():
            try:
                created_details = serializer.save()

                response_serializer = CertificateDetailsResponseSerializer(
                    created_details,
                    many=True
                )

                return APIResponse.created(
                    data=response_serializer.data,
                    message=f'Successfully created {len(created_details)} certificate details'
                )
            except Exception as e:
                return APIResponse.error(
                    message=f'Failed to create certificate details{str(e)}',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return APIResponse.validation_error(
            message =  'Validation failed',
            errors = serializer.errors
        )


class CertificateManage(APIView):
    def get_object(self, token_no, user):
        # 1️⃣ Validate user's business
        try:
            business = CompanyProfile.objects.get(pk=user.business_id)
        except (CompanyProfile.DoesNotExist, AttributeError):
            return None, "User business profile not found"

        # 2️⃣ Retrieve certificate for this business
        try:
            certificate = Certificate.objects.get(business_id=business, token_no=token_no)
            return certificate, None
        except Certificate.DoesNotExist:
            return None, "Certificate not found for your business"

    # --------------- GET (Retrieve) ----------------
    def get(self, request, token_no):
        certificate, error = self.get_object(token_no, request.user)

        if error:
            return APIResponse.not_found(message=error)

        serializer = CertificateSerializer(certificate)
        return APIResponse.success(
            data=serializer.data,
            message="Certificate retrieved successfully"
        )

    # --------------- PUT (Update) ----------------
    def put(self, request, token_no):
        certificate, error = self.get_object(token_no, request.user)

        if error:
            return APIResponse.not_found(message=error)

        serializer = CertificateSerializer(certificate, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save(updated_by=request.user, updated_at=timezone.now())
            return APIResponse.updated(
                data=serializer.data,
                message="Certificate updated successfully"
            )

        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Validation failed"
        )

    # --------------- DELETE ----------------
    def delete(self, request, token_no):
        certificate, error = self.get_object(token_no, request.user)

        if error:
            return APIResponse.not_found(message=error)

        certificate.delete()
        return APIResponse.deleted(
            message="Certificate deleted successfully"
        )


class CertificateDetailManage(generics.ListAPIView):
    serializer_class = CertificateDetailsResponseSerializer

    def get_queryset(self):
        token_no = self.kwargs.get('token_no')
        return CertificateDetails.objects.filter(token_no=token_no)
