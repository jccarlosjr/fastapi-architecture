from fastapi import Request

def get_client_ip(request: Request) -> str:
    """
    Get the client IP address from the request.

    It checks the following headers in order:
    1. X-Forwarded-For
    2. X-Real-IP
    3. Request client host
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"

