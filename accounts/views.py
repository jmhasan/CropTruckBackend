from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from accounts.models import Glmst, Glsub
from accounts.serializers import ChartofAccountsSerializer, SubAccountSerializer
from rest_framework.exceptions import NotFound, PermissionDenied
from masterdata.models import CompanyProfile
from utils.response import APIResponse


class ChartofAccountsViewSet(viewsets.ModelViewSet):
    queryset = Glmst.objects.all()
    serializer_class = ChartofAccountsSerializer

    def get_object(self):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            # Retrieve the individual key components from the URL kwargs
            xacc_str = self.kwargs.get('xacc')

            # Validate user's business
            try:
                business = CompanyProfile.objects.get(pk=self.request.user.business_id)
            except (CompanyProfile.DoesNotExist, AttributeError):
                return None, "User business profile not found"

            try:
                # Perform the database query using the individual key components
                obj = queryset.get(business_id=business, xacc=xacc_str)
            except Glmst.DoesNotExist:
                raise NotFound("Chart of Accounts entry with the specified composite key does not exist.")

            self.check_object_permissions(self.request, obj)
            return obj
        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve Account Code. Please try again.",
                status_code=500
            )

    def list(self, request, *args, **kwargs):
        # Default list implementation (with filtering, pagination if enabled)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return APIResponse.success(
            data=serializer.data,
            message="Chart of Account retrieved successfully"
        )

    def perform_create(self, serializer):
        # Validate user's business
        try:
            business = CompanyProfile.objects.get(pk=self.request.user.business_id)
        except (CompanyProfile.DoesNotExist, AttributeError):
            return None, "User business profile not found"

        serializer.save(
            business_id=business,
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


    def create(self, request, *args, **kwargs):
        # Default create implementation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return APIResponse.created(
            data=serializer.data,
            message="Account created successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        # Default retrieve implementation
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(
            data=serializer.data,
            message="Chart of Account retrieved successfully"
        )

    def update(self, request, *args, **kwargs):
        # Default update implementation
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return APIResponse.updated(
            data=serializer.data,
            message="Account Updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        # Default destroy implementation
        instance = self.get_object()
        self.perform_destroy(instance)
        # return Response(status=status.HTTP_204_NO_CONTENT)
        # return APIResponse.deleted("Account deleted successfully")
        return APIResponse.deleted(
            message="Account deleted successfully"
        )


class SubAccountViewSet(viewsets.ModelViewSet):
    queryset = Glsub.objects.all()
    serializer_class = SubAccountSerializer

    def get_queryset(self):
        """
        Dynamically filters the queryset based on the authenticated user's business.
        This ensures users can only see objects belonging to their company.
        """
        print("call this url")
        try:
            account_code = self.kwargs.get('xacc')
            user = self.request.user
            if not user.is_authenticated or not hasattr(user, 'business_id'):
                raise PermissionDenied("Authentication credentials were not provided or are invalid.")

            try:
                business = CompanyProfile.objects.get(pk=user.business_id)
            except CompanyProfile.DoesNotExist:
                raise NotFound("User's business profile not found.")
            except Exception as e:
                raise NotFound(f"Error retrieving user's business: {e}")

            return Glsub.objects.filter(business_id=business,xacc=account_code)
        except Exception as e:
            raise NotFound(f"Error retrieving user's business: {e}")


    def get_object(self):
        """
        Custom method to retrieve a single object using the composite key
        from the URL kwargs: `/glsub/<xacc>,<xsub>/`.
        """
        queryset = self.get_queryset()
        xacc_str = self.kwargs.get('xacc')
        xsub_str = self.kwargs.get('xsub')

        if not xacc_str or not xsub_str:
            raise NotFound("Account code (xacc) or sub-account code (xsub) not specified in the URL.")

        try:
            obj = queryset.get(xacc=xacc_str, xsub=xsub_str)
            self.check_object_permissions(self.request, obj)
            return obj
        except Glsub.DoesNotExist:
            raise NotFound("Sub-account entry not found for this account code, sub-account code, and business.")
        except Exception as e:
            # Use APIResponse.error() if available, otherwise raise DRF exception
            # For this example, we'll raise an exception for consistency with DRF's flow
            raise status.HTTP_500_INTERNAL_SERVER_ERROR(f"Failed to retrieve sub-account: {e}")

    def perform_create(self, serializer):
        """
        Save the new Glsub instance, setting the business and created_by fields.
        """
        print("call this")
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'business_id'):
            raise PermissionDenied("User is not properly authenticated.")

        try:
            business = CompanyProfile.objects.get(pk=user.business_id)
        except CompanyProfile.DoesNotExist:
            raise NotFound("User's business profile not found.")

        # Save the instance with the business_id and created_by fields automatically set.
        serializer.save(business_id=business, created_by=user, updated_by=user)

    def perform_update(self, serializer):
        """
        Update the Glsub instance, setting the updated_by field.
        """
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("User is not properly authenticated.")

        serializer.save(updated_by=user)

    def list(self, request, *args, **kwargs):
        print("call this list")
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            data=serializer.data,
            message="Sub-accounts retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse.created(
            data=serializer.data,
            message="Sub-account created successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(
            data=serializer.data,
            message="Sub-account retrieved successfully"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse.updated(
            data=serializer.data,
            message="Sub-account updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.deleted(
            message="Sub-account deleted successfully"
        )

