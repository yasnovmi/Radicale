# This file is part of Radicale - CalDAV and CardDAV server
# Copyright © 2014 Jean-Marc Martins
# Copyright © 2012-2017 Guillaume Ayoub
# Copyright © 2017-2018 Unrud <unrud@outlook.com>
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Radicale.  If not, see <http://www.gnu.org/licenses/>.

import os
import posixpath
from typing import Callable, ContextManager, Iterator, Optional, cast

from radicale import pathutils, types
from radicale.log import logger
from radicale.storage import multifilesystem
from radicale.storage.multifilesystem.base import StorageBase


@types.contextmanager
def _null_child_context_manager(path: str,
                                href: Optional[str]) -> Iterator[None]:
    yield


class StoragePartDiscover(StorageBase):

    def discover(
            self, path: str, depth: str = "0", child_context_manager: Optional[
                Callable[[str, Optional[str]], ContextManager[None]]] = None
            ) -> Iterator[types.CollectionOrItem]:
        # assert isinstance(self, multifilesystem.Storage)

        collection = multifilesystem.Collection(
            storage_=cast(multifilesystem.Storage, self),
            path="/default/",
        )

        yield collection

        if depth == "0":
            return

        address_book = multifilesystem.Collection(
            storage_=cast(multifilesystem.Storage, self),
            path="/default/address_book.vcf",
        )
        address_book.set_meta(
            {
                "D:displayname": os.getenv("ADDRESS_BOOK_NAME", "default"),
                "tag": "VADDRESSBOOK"
             }
        )

        yield address_book
