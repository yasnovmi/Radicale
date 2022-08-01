import datetime
import json
import os

import ldap3

from dateutil.parser import parse
from radicale import logger
from dataclasses import dataclass
from typing import Optional, List
from radicale.redis import client as redis_client

LDAP_FIELD_NAMES = \
    ("uid", "ruSn", "ruGivenName", "mobile", "skype", "telegram", "birthdate", "mail", "title", "modifyTimestamp")

REDIS_CACHE_KEY = "ldap_users"


@dataclass
class LdapUser:
    uid: str
    ruSn: Optional[str]
    ruGivenName: Optional[str]
    mobile: Optional[str]
    skype: Optional[str]
    telegram: Optional[str]
    birthdate: Optional[str]
    mail: Optional[str]
    title: Optional[str]
    modifyTimestamp: datetime.datetime

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in LDAP_FIELD_NAMES:
                if isinstance(value, List) and len(value) > 0:
                    setattr(self, key, value[0])
                elif not value:
                    setattr(self, key, None)
                elif key == "modifyTimestamp":
                    setattr(self, key, parse(value))

                else:
                    setattr(self, key, value)


class LdapService:

    @staticmethod
    def _get_ldap_users() -> List:
        server = ldap3.Server(os.getenv("LDAP_URL"))
        conn = ldap3.Connection(server, os.getenv("LDAP_BINDDN"), password=os.getenv("LDAP_PASSWORD"))

        conn.bind()

        try:
            logger.debug("LDAP whoami: %s" % conn.extend.standard.who_am_i())
        except Exception as err:
            logger.debug("LDAP error: %s" % err)

        conn.search(search_base=os.getenv("LDAP_BASE"),
                    search_scope="LEVEL",
                    search_filter=os.getenv("LDAP_FILTER"),
                    attributes=LDAP_FIELD_NAMES)

        return conn.response

    def sync(self) -> List[LdapUser]:
        cached = redis_client.get(REDIS_CACHE_KEY)
        if cached:
            users = json.loads(cached)
        else:
            users = self._get_ldap_users()
            users = [dict(u["attributes"]) for u in users]
            json_objects = json.dumps(users, default=str)
            redis_client.setex(name=REDIS_CACHE_KEY, value=json_objects,
                               time=datetime.timedelta(seconds=int(os.getenv("REDIS_CACHE_LIVE_SECONDS", 7200))))

        return [LdapUser(**u) for u in users]
