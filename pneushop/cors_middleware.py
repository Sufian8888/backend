class CorsAlwaysAllowMiddleware:
    """
    Safety-net middleware: ensures CORS headers are present on EVERY response,
    including unhandled 500 errors where django-cors-headers may not run.
    Must be placed FIRST in MIDDLEWARE (before CorsMiddleware).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception:
            from django.http import JsonResponse
            import traceback
            response = JsonResponse(
                {"error": "Internal server error", "detail": traceback.format_exc()},
                status=500,
            )

        origin = request.META.get("HTTP_ORIGIN")
        if origin and "Access-Control-Allow-Origin" not in response:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        # Handle preflight
        if request.method == "OPTIONS" and origin:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Max-Age"] = "86400"

        return response
