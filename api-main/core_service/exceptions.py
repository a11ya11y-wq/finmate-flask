

class FinMateError(Exception): # Base class
    code = 500

class ThrottlingError(FinMateError): # Too-many requests
    code = 429

class ConflictError(FinMateError):# Except Duplicate
    code = 409

class AuthenticationError(FinMateError): # Authentication failure
    code = 401

class ResourceNotFound(FinMateError): # Resource not found
    code = 404

class BusinessLogicError(FinMateError): # Business logic violation
    code = 400

class ForbiddenError(FinMateError): # Forbidden access
    code = 403