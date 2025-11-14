from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError

from .utils.on_board_token import VendorStepToken


class VendorOnboardingUser:
    """A placeholder user for onboarding steps."""
    is_authenticated = False


class VendorStepAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return None  # No credentials sent

        token_str = auth_header.split(' ')[1]

        try:
            token = VendorStepToken(token_str)
            token.check_exp()

            # Token is valid → return a dummy user & token
            return (VendorOnboardingUser(), token)

        except TokenError:
            raise AuthenticationFailed('Invalid or expired vendor onboarding token')

    def authenticate_header(self, request):
        return 'Bearer'
