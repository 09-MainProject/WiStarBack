from rest_framework.exceptions import APIException


class CustomAPIException(APIException):
    def __init__(self, error_dict):
        self.status_code = error_dict.get("code", 400)
        self.detail = error_dict
