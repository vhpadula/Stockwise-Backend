from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict):
        # Flatten the first error to a "message" field
        errors = []
        for field, messages in response.data.items():
            if isinstance(messages, list):
                errors.extend(messages)
            else:
                errors.append(str(messages))
        if errors:
            response.data = {"message": errors[0]}
    return response
