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

import json
import os
from typing import Mapping, Optional, TextIO, Union, cast, overload

import radicale.item as radicale_item
from radicale.storage import multifilesystem
from radicale.storage.multifilesystem.base import CollectionBase


class CollectionPartMeta(CollectionBase):

    _meta_cache: Optional[Mapping[str, str]]
    _props_path: str

    def __init__(self, storage_: "multifilesystem.Storage", path: str,
                 filesystem_path: Optional[str] = None) -> None:
        super().__init__(storage_, path, filesystem_path)
        self._meta_cache = {}
        self._props_path = os.path.join(
            self._filesystem_path, ".Radicale.props")

    @overload
    def get_meta(self, key: None = None) -> Mapping[str, str]: ...

    @overload
    def get_meta(self, key: str) -> Optional[str]: ...

    def get_meta(self, key: Optional[str] = None) -> Union[Mapping[str, str],
                                                           Optional[str]]:
        return self._meta_cache if key is None else self._meta_cache.get(key)

    def set_meta(self, props: Mapping[str, str]) -> None:
        self._meta_cache = dict(self._meta_cache, **props)

