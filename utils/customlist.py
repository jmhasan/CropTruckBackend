from rest_framework import generics

from utils.response import APIResponse


class CustomListAPIView(generics.ListAPIView):
    """Base class with custom response format"""
    def get_success_message(self):
        """Override this method to provide custom success message"""
        return "Data retrieved successfully"

    def filter_by_business(self, queryset):
        """Filter queryset by business_id if user is authenticated"""
        if hasattr(self.request.user, 'business_id') and self.request.user.is_authenticated:
            return queryset.filter(business_id=self.request.user.business_id)
        return queryset

    def list(self, request, *args, **kwargs):
        try:
            # Get the filtered queryset
            queryset = self.filter_queryset(self.get_queryset())

            # Apply business filter
            queryset = self.filter_by_business(queryset)

            # Handle pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)

                return APIResponse.success(
                    data=paginated_response.data.get('results'),
                    message=self.get_success_message(),
                    meta={
                        'pagination': {
                            'count': paginated_response.data.get('count'),
                            'next': paginated_response.data.get('next'),
                            'previous': paginated_response.data.get('previous'),
                        }
                    }
                )

            # Non-paginated response
            serializer = self.get_serializer(queryset, many=True)
            return APIResponse.success(
                data=serializer.data,
                message=self.get_success_message(),
                meta={'count': queryset.count()}
            )

        except Exception as e:
            return APIResponse.error(
                message="Failed to retrieve data",
                status_code=500
            )
