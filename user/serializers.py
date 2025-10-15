from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from user.models import CustomUser


class UserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','user_role', 'username', 'first_name', 'last_name', 'email', 'profile_pic','business_id']


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, CustomUser):
        token = super().get_token(CustomUser)
        # Add custom claims
        token['username'] = CustomUser.username
        token['user_role'] = CustomUser.user_role
        token['business_id'] = CustomUser.business_id
        return token
