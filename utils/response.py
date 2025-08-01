# utils/response.py
from rest_framework.response import Response
from rest_framework import status
from typing import Any, Optional, Dict


class APIResponse:
    """Standardized API Response utility"""

    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = status.HTTP_200_OK,
                meta: Optional[Dict] = None):
        """Success response structure"""
        response_data = {
            "success": True,
            "status_code": status_code,
            "message": message,
            "data": data,
        }
        if meta:
            response_data["meta"] = meta
        return Response(response_data, status=status_code)

    @staticmethod
    def error(message: str = "Error occurred", status_code: int = status.HTTP_400_BAD_REQUEST,
              errors: Optional[Dict] = None, data: Any = None):
        """Error response structure"""
        response_data = {
            "success": False,
            "status_code": status_code,
            "message": message,
            "data": data,
        }
        if errors:
            response_data["errors"] = errors
        return Response(response_data, status=status_code)

    @staticmethod
    def created(data: Any = None, message: str = "Resource created successfully"):
        """Created response"""
        return APIResponse.success(data, message, status.HTTP_201_CREATED)

    @staticmethod
    def updated(data: Any = None, message: str = "Resource updated successfully"):
        """Updated response"""
        return APIResponse.success(data, message, status.HTTP_200_OK)

    @staticmethod
    def deleted(message: str = "Resource deleted successfully"):
        """Deleted response"""
        return APIResponse.success(None, message, status.HTTP_200_OK)

    @staticmethod
    def not_found(message: str = "Resource not found"):
        """Not found response"""
        return APIResponse.error(message, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def validation_error(errors: Dict, message: str = "Validation failed"):
        """Validation error response"""
        return APIResponse.error(message, status.HTTP_400_BAD_REQUEST, errors)

    @staticmethod
    def unauthorized(message: str = "Authentication required"):
        """Unauthorized response"""
        return APIResponse.error(message, status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def forbidden(message: str = "Permission denied"):
        """Forbidden response"""
        return APIResponse.error(message, status.HTTP_403_FORBIDDEN)
