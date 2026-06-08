from functools import wraps
from flask_jwt_extended import get_jwt
from core_service.exceptions import ForbiddenError

def prevent_demo_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        claims = get_jwt()
        
        if claims.get("email") == "demo@test.com":
            raise ForbiddenError("This action is prohibited for the demo account.")
            
        return f(*args, **kwargs)
    return decorated_function