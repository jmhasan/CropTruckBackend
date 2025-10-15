from rest_framework.views import exception_handler
from rest_framework import status
from .response import APIResponse

def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses"""
    response = exception_handler(exc, context)

    if response is not None:
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return APIResponse.not_found()
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            return APIResponse.unauthorized()
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            return APIResponse.forbidden()
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            return APIResponse.validation_error(
                errors=response.data,
                message="Bad request"
            )
        else:
            return APIResponse.error(
                message="An error occurred",
                status_code=response.status_code
            )

    return response