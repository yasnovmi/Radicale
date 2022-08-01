import os
import sys
from datetime import timedelta

import redis

from radicale import logger


def redis_connect() -> redis.client.Redis:
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            db=0,
            socket_timeout=5,
            decode_responses=True,
        )
        ping = redis_client.ping()
        if ping is True:
            return redis_client
    except redis.AuthenticationError as e:
        logger.debug("Redis auth error:\n%s", e)
        sys.exit(1)


client = redis_connect()

