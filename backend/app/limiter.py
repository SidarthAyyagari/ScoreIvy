from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import RATE_LIMIT_ENABLED

# Keys on the client IP; behind a load balancer run uvicorn with --proxy-headers so this is the real client.
limiter = Limiter(key_func=get_remote_address, enabled=RATE_LIMIT_ENABLED)
