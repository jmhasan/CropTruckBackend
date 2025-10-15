from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import LoginSerializer, UserSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserInfo(request):
    user_serializer = UserSerializer(request.user)
    return Response({
        "user": user_serializer.data,
        "message": "User info fetched successfully."
    })
User = get_user_model()

class LoginAPI(TokenObtainPairView):
    serializer_class = LoginSerializer
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Valid user, get token pair using parent method
        try:
            response = super().post(request, *args, **kwargs)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # Add user data to the response
        user_serializer = UserSerializer(user)
        response.data['user'] = user_serializer.data
        response.data['message'] = "Login successful."
        response.data['status'] = "OK"
        return response
