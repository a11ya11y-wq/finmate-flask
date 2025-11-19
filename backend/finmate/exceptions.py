

class ServiceError(Exception): # Base class
    status_code = 500

class ThrottlingError(ServiceError): # Too-many requests
    status_code = 429