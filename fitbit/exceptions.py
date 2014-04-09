import json

class BadResponse(Exception):
    """
    Currently used if the response can't be json encoded, despite a .json extension
    """
    pass

class DeleteError(Exception):
    """
    Used when a delete request did not return a 204
    """
    pass

class HTTPException(Exception):
    def __init__(self, response, *args, **kwargs):
        try:
            errors = json.loads(response.content.decode('utf8'))['errors']
            message = '\n'.join([error['message'] for error in errors])
        except Exception:
            if response.status_code == 401:
                message = response.content.decode('utf8')
            else:
                message = response
        super(HTTPException, self).__init__(message, *args, **kwargs)

class HTTPBadRequest(HTTPException):
    pass


class HTTPUnauthorized(HTTPException):
    pass


class HTTPForbidden(HTTPException):
    pass


class HTTPServerError(HTTPException):
    pass


class HTTPConflict(HTTPException):
    """
    Used by Fitbit as rate limiter
    """
    pass


class HTTPNotFound(HTTPException):
    pass
