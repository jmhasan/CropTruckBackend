from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser


class AttachBusinessIDMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if this is an API request
        if request.path.startswith('/api/'):  # Adjust path as needed
            jwt_authenticator = JWTAuthentication()
            try:
                # Try to authenticate with JWT
                auth_result = jwt_authenticator.authenticate(request)
                if auth_result is not None:
                    user, token = auth_result
                    request.user = user  # Set the authenticated user
                    # print(f"✅ JWT User authenticated: {user}")
                else:
                    # print("❌ No JWT token found")
                    request.business_id = None
                    return
            except (InvalidToken, TokenError) as e:
                # print(f"❌ JWT authentication failed: {e}")
                request.business_id = None
                return

        # Now check for business_id
        user = getattr(request, 'user', None)
        # print(f"=== AttachBusinessIDMiddleware Debug ===")
        # print(f"User: {user}")
        # print(f"Is authenticated: {getattr(user, 'is_authenticated', False)}")

        if user and user.is_authenticated and hasattr(user, 'business_id'):
            request.business_id = user.business_id
            # print(f"✅ Business ID attached: {request.business_id}")
        else:
            request.business_id = None
            # print("❌ No business ID attached")