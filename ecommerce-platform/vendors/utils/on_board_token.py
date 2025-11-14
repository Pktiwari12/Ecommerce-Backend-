from datetime import timedelta
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

class VendorStepToken(Token):
    token_type = "vendor_step"
    lifetime = timedelta(minutes=5)

def create_vendor_step_token(field,minutes: int=5):
    token = VendorStepToken()
    token['field'] = field
    token.set_exp(lifetime=timedelta(minutes=minutes))
    # print(str(token))
    return str(token)

def verify_vendor_step_token(token_str: str, field: str):
    try:
        token = VendorStepToken(token_str)
        token.check_exp()
        if token.get('field') != field:
            raise InvalidToken("Token does not match related field.")
        return True
    except TokenError as e:
        return False



