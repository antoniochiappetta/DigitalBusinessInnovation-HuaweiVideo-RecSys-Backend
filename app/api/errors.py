from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES


class ApiResponse(object):
    @staticmethod
    def to_dict(code, _type, message=None):
        payload = {
            'code': code,
            'type': _type,
            'message': message
        }
        if message:
            payload['message'] = message
        return payload


def error_response(status_code, status='', message=None):
    status = status if status != '' else HTTP_STATUS_CODES.get(status_code, 'Unknown error')
    payload = ApiResponse.to_dict(status_code, status, message)
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message):
    return error_response(400, message)


def bad_input(message):
    return error_response(405, status='Invalid input', message=message)
