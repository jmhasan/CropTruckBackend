from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics
from masterdata.models import CommonCodes, CompanyProfile, GeoLocation
from masterdata.serializers import CommonCodesSerializer, DivisionSerializer, CustomerProfileCreateSerializer, \
    CustomerProfileResponseSerializer, GeoLocationSerializer, CustomerProfileUpdateSerializer
from utils.customlist import CustomListAPIView
from utils.response import APIResponse
# views.py
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import CustomerProfile, CompanyProfile




class CommonCodesAdd(APIView):
    def post(self, request, format=None):
        """Create a new common code"""
        try:
            # Create serializer with request data
            serializer = CommonCodesSerializer(data=request.data)

            if serializer.is_valid():
                # Save with additional fields if needed
                instance = serializer.save(
                    created_by=request.user,
                    # Add business_id if your model has it
                    business_id=CompanyProfile.objects.get(pk=request.user.business_id)
                )
                return APIResponse.created(
                    data=serializer.data,
                    message="Common code created successfully"
                )
            else:
                return APIResponse.validation_error(
                    errors=serializer.errors,
                    message="Common code creation failed"
                )

        except Exception as e:
            return APIResponse.error(
                message="Failed to create common code",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CommonCodesList(CustomListAPIView):
    queryset = CommonCodes.objects.filter(zactive=True)
    serializer_class = CommonCodesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['xtype', ]


class DivisionListView(APIView):
    """Get all divisions for a business"""
    def get(self, request, format=None):
        try:
            # Get distinct divisions for the business
            divisions = GeoLocation.objects.filter(
                business_id=request.user.business_id
            ).values(
                'division_name', 'division_bn'
            ).distinct().order_by('division_name')

            if not divisions.exists():
                return APIResponse.success(
                    data=[],
                    message="No divisions found",
                    meta={'count': 0}
                )

            # Convert to list for serialization
            divisions_list = list(divisions)

            return APIResponse.success(
                data=divisions_list,
                message="Divisions retrieved successfully",
                meta={
                    'count': len(divisions_list),
                    'level': 'division'
                }
            )

        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve divisions",
                status_code=500
            )


class GeoLocationAll(generics.ListAPIView):
    queryset = GeoLocation.objects.all()
    serializer_class = GeoLocationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['division_name',]


class DistrictListView(APIView):
    """Get all districts for a given division"""

    def get(self, request, division_name, format=None):
        try:
            # Get districts for specific division
            districts = GeoLocation.objects.filter(
                business_id=request.user.business_id,
                division_name=division_name
            ).values(
                'division_name', 'division_bn', 'district_name', 'district_bn'
            ).distinct().order_by('district_name')

            if not districts.exists():
                return APIResponse.not_found(
                    f"No districts found for division: {division_name}"
                )

            districts_list = list(districts)

            return APIResponse.success(
                data=districts_list,
                message=f"Districts retrieved successfully for {division_name}",
                meta={
                    'count': len(districts_list),
                    'level': 'district',
                    'parent_division': division_name
                }
            )

        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve districts",
                status_code=500
            )


class UpazilaListView(APIView):
    """Get all upazilas for a given division and district"""

    def get(self, request, division_name, district_name, format=None):
        try:
            # Get upazilas for specific division and district
            upazilas = GeoLocation.objects.filter(
                business_id=request.user.business_id,
                division_name=division_name,
                district_name=district_name
            ).values(
                'division_name', 'division_bn', 'district_name', 'district_bn',
                'upazila_name', 'upazila_bn'
            ).distinct().order_by('upazila_name')

            if not upazilas.exists():
                return APIResponse.not_found(
                    f"No upazilas found for {district_name}, {division_name}"
                )

            upazilas_list = list(upazilas)

            return APIResponse.success(
                data=upazilas_list,
                message=f"Upazilas retrieved successfully for {district_name}, {division_name}",
                meta={
                    'count': len(upazilas_list),
                    'level': 'upazila',
                    'parent_division': division_name,
                    'parent_district': district_name
                }
            )

        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve upazilas",
                status_code=500
            )


class UnionListView(APIView):
    """Get all unions for a given division, district, and upazila"""

    def get(self, request, division_name, district_name, upazila_name, format=None):
        try:
            # Get unions for specific division, district, and upazila
            unions = GeoLocation.objects.filter(
                business_id=request.user.business_id,
                division_name=division_name,
                district_name=district_name,
                upazila_name=upazila_name
            ).values(
                'division_name', 'division_bn', 'district_name', 'district_bn',
                'upazila_name', 'upazila_bn', 'union_name', 'union_bn'
            ).distinct().order_by('union_name')

            if not unions.exists():
                return APIResponse.not_found(
                    f"No unions found for {upazila_name}, {district_name}, {division_name}"
                )

            unions_list = list(unions)

            return APIResponse.success(
                data=unions_list,
                message=f"Unions retrieved successfully for {upazila_name}, {district_name}, {division_name}",
                meta={
                    'count': len(unions_list),
                    'level': 'union',
                    'parent_division': division_name,
                    'parent_district': district_name,
                    'parent_upazila': upazila_name
                }
            )

        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve unions",
                status_code=500
            )


class CustomerProfileCreate(APIView):
    """
    POST API for creating customer profile with geo-location validation
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
                serializer = CustomerProfileCreateSerializer(
                    data=request.data,
                    context={'request': request}
                )

                if serializer.is_valid():
                    # Save customer with business_id and audit fields
                    customer = serializer.save(
                        business_id=business,
                        created_by=request.user,
                        updated_by=request.user
                    )

                    # Return response with full customer data
                    response_serializer = CustomerProfileResponseSerializer(customer)

                    return APIResponse.created(
                        data=response_serializer.data,
                        message="Customer created successfully"
                    )
                else:
                    return APIResponse.validation_error(
                        errors=serializer.errors,
                        message="Customer creation failed"
                    )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer creation failed: {str(e)}")

            return APIResponse.error(
                message="Customer creation failed. Please try again.",
                status_code=500
            )


class CustomerProfileUpdate(APIView):
    """
    PUT/PATCH API for updating customer profile
    """

    def get_object(self, customer_code, business_id):
        """Get customer object with business filtering"""
        try:
            return CustomerProfile.objects.get(
                business_id=business_id,
                customer_code=customer_code
            )
        except CustomerProfile.DoesNotExist:
            return None

    def put(self, request, customer_code, format=None):
        """Full update of customer profile"""
        return self._update_customer(request, customer_code, partial=False)

    def patch(self, request, customer_code, format=None):
        """Partial update of customer profile"""
        return self._update_customer(request, customer_code, partial=True)

    def _update_customer(self, request, customer_code, partial=False):
        """Common update logic for PUT and PATCH"""
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

                # Get customer object
                customer = self.get_object(customer_code, request.user.business_id)
                if not customer:
                    return APIResponse.not_found("Customer not found")

                # Create serializer with context
                serializer = CustomerProfileUpdateSerializer(
                    customer,
                    data=request.data,
                    partial=partial,
                    context={'request': request}
                )

                if serializer.is_valid():
                    # Save customer with audit fields
                    updated_customer = serializer.save(
                        updated_by=request.user
                    )

                    # Return response with full customer data
                    response_serializer = CustomerProfileResponseSerializer(updated_customer)

                    return APIResponse.updated(
                        data=response_serializer.data,
                        message="Customer updated successfully"
                    )
                else:
                    return APIResponse.validation_error(
                        errors=serializer.errors,
                        message="Customer update failed"
                    )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Customer update failed: {str(e)}")

            return APIResponse.error(
                message="Customer update failed. Please try again.",
                status_code=500
            )


class CustomerProfileList(APIView):
    """
    GET: List customers with filtering and search
    """

    def get(self, request, format=None):
        """Get customers with filtering and pagination"""
        try:
            # Base queryset
            queryset = CustomerProfile.objects.filter(
                business_id=request.user.business_id).select_related('business_id')
            # Apply filters
            customer_type = request.GET.get('customer_type')
            if customer_type:
                queryset = queryset.filter(customer_type=customer_type)

            division = request.GET.get('division')
            if division:
                queryset = queryset.filter(division_name=division)

            district = request.GET.get('district')
            if district:
                queryset = queryset.filter(district_name=district)

            group_name = request.GET.get('group_name')
            if group_name:
                queryset = queryset.filter(group_name=group_name)

            # Include inactive customers if requested
            include_inactive = request.GET.get('include_inactive', 'false').lower() == 'true'
            if include_inactive:
                queryset = CustomerProfile.objects.filter(business_id=request.user.business_id)

            # Search functionality
            search = request.GET.get('search')
            if search:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(customer_name__icontains=search) |
                    Q(customer_code__icontains=search) |
                    Q(xmobile__icontains=search) |
                    Q(contact_person__icontains=search) |
                    Q(xemail__icontains=search)
                )

            # Pagination
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

            page = request.GET.get('page', 1)
            per_page = min(int(request.GET.get('per_page', 20)), 100)

            paginator = Paginator(queryset.order_by('-created_at'), per_page)

            try:
                customers = paginator.page(page)
            except PageNotAnInteger:
                customers = paginator.page(1)
            except EmptyPage:
                customers = paginator.page(paginator.num_pages)

            # Serialize data
            serializer = CustomerProfileResponseSerializer(customers, many=True)

            return APIResponse.success(
                data=serializer.data,
                message="Customers retrieved successfully",
                meta={
                    'pagination': {
                        'current_page': customers.number,
                        'total_pages': paginator.num_pages,
                        'per_page': per_page,
                        'total_count': paginator.count,
                        'has_next': customers.has_next(),
                        'has_previous': customers.has_previous(),
                    },
                    'filters_applied': {
                        'customer_type': customer_type,
                        'division': division,
                        'district': district,
                        'group_name': group_name,
                        'include_inactive': include_inactive,
                        'search': search
                    }
                }
            )

        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve customers",
                status_code=500
            )