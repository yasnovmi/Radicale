# This file is part of Radicale - CalDAV and CardDAV server
# Copyright © 2008 Nicolas Kandel
# Copyright © 2008 Pascal Halter
# Copyright © 2008-2017 Guillaume Ayoub
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

import contextlib
import posixpath
import socket
import xml.etree.ElementTree as ET
from http import client
from typing import Callable, Iterable, Iterator, Optional, Sequence, Tuple
from urllib.parse import unquote, urlparse

import radicale.item as radicale_item
from radicale import httputils, pathutils, storage, types, xmlutils
from radicale.app.base import Access, ApplicationBase
from radicale.item import filter as radicale_filter
from radicale.log import logger


def xml_report(base_prefix: str, path: str, xml_request: Optional[ET.Element],
               collection: storage.BaseCollection, encoding: str,
               unlock_storage_fn: Callable[[], None]
               ) -> Tuple[int, ET.Element]:
    """Read and answer REPORT requests.

    Read rfc3253-3.6 for info.

    """
    multistatus = ET.Element(xmlutils.make_clark("D:multistatus"))
    if xml_request is None:
        return client.MULTI_STATUS, multistatus
    root = xml_request

    prop_element = root.find(xmlutils.make_clark("D:prop"))
    props = ([prop.tag for prop in prop_element]
             if prop_element is not None else [])

    hreferences: Iterable[str]
    if root.tag == xmlutils.make_clark("D:sync-collection"):
        # Append current sync token to response
        sync_token_element = ET.Element(xmlutils.make_clark("D:sync-token"))
        sync_token_element.text = "sync_token"
        multistatus.append(sync_token_element)

    # Retrieve everything required for finishing the request.
    retrieved_items = list(retrieve_items(collection))
    collection_tag = collection.tag
    # !!! Don't access storage after this !!!
    unlock_storage_fn()

    while retrieved_items:
        # ``item.vobject_item`` might be accessed during filtering.
        # Don't keep reference to ``item``, because VObject requires a lot of
        # memory.
        item, filters_matched = retrieved_items.pop(0)

        found_props = []
        not_found_props = []

        for tag in props:
            element = ET.Element(tag)
            if tag == xmlutils.make_clark("D:getetag"):
                element.text = item.etag
                found_props.append(element)
            elif tag == xmlutils.make_clark("D:getcontenttype"):
                element.text = xmlutils.get_content_type(item, encoding)
                found_props.append(element)
            elif tag in (
                    xmlutils.make_clark("C:calendar-data"),
                    xmlutils.make_clark("CR:address-data")):
                element.text = item.serialize()
                found_props.append(element)
            else:
                not_found_props.append(element)

        assert item.href
        uri = pathutils.unstrip_path(
            posixpath.join(collection.path, item.href))
        multistatus.append(xml_item_response(
            base_prefix, uri, found_props=found_props,
            not_found_props=not_found_props, found_item=True))

    return client.MULTI_STATUS, multistatus


def xml_item_response(base_prefix: str, href: str,
                      found_props: Sequence[ET.Element] = (),
                      not_found_props: Sequence[ET.Element] = (),
                      found_item: bool = True) -> ET.Element:
    response = ET.Element(xmlutils.make_clark("D:response"))

    href_element = ET.Element(xmlutils.make_clark("D:href"))
    href_element.text = xmlutils.make_href(base_prefix, href)
    response.append(href_element)

    if found_item:
        for code, props in ((200, found_props), (404, not_found_props)):
            if props:
                propstat = ET.Element(xmlutils.make_clark("D:propstat"))
                status = ET.Element(xmlutils.make_clark("D:status"))
                status.text = xmlutils.make_response(code)
                prop_element = ET.Element(xmlutils.make_clark("D:prop"))
                for prop in props:
                    prop_element.append(prop)
                propstat.append(prop_element)
                propstat.append(status)
                response.append(propstat)
    else:
        status = ET.Element(xmlutils.make_clark("D:status"))
        status.text = xmlutils.make_response(404)
        response.append(status)

    return response


def retrieve_items( collection: storage.BaseCollection) -> Iterator[Tuple[radicale_item.Item, bool]]:
    """Retrieves all items that are referenced in ``hreferences`` from
       ``collection`` and adds 404 responses for missing and invalid items
       to ``multistatus``."""
    for item in collection.get_all():
        yield item, True


def test_filter(collection_tag: str, item: radicale_item.Item,
                filter_: ET.Element) -> bool:
    """Match an item against a filter."""
    if (collection_tag == "VCALENDAR" and
            filter_.tag != xmlutils.make_clark("C:%s" % filter_)):
        if len(filter_) == 0:
            return True
        if len(filter_) > 1:
            raise ValueError("Filter with %d children" % len(filter_))
        if filter_[0].tag != xmlutils.make_clark("C:comp-filter"):
            raise ValueError("Unexpected %r in filter" % filter_[0].tag)
        return radicale_filter.comp_match(item, filter_[0])
    if (collection_tag == "VADDRESSBOOK" and
            filter_.tag != xmlutils.make_clark("CR:%s" % filter_)):
        for child in filter_:
            if child.tag != xmlutils.make_clark("CR:prop-filter"):
                raise ValueError("Unexpected %r in filter" % child.tag)
        test = filter_.get("test", "anyof")
        if test == "anyof":
            return any(radicale_filter.prop_match(item.vobject_item, f, "CR")
                       for f in filter_)
        if test == "allof":
            return all(radicale_filter.prop_match(item.vobject_item, f, "CR")
                       for f in filter_)
        raise ValueError("Unsupported filter test: %r" % test)
    raise ValueError("Unsupported filter %r for %r" %
                     (filter_.tag, collection_tag))


class ApplicationPartReport(ApplicationBase):

    def do_REPORT(self, environ: types.WSGIEnviron, base_prefix: str,
                  path: str, user: str) -> types.WSGIResponse:
        """Manage REPORT request."""
        try:
            xml_content = self._read_xml_request_body(environ)
        except RuntimeError as e:
            logger.warning("Bad REPORT request on %r: %s", path, e,
                           exc_info=True)
            return httputils.BAD_REQUEST
        except socket.timeout:
            logger.debug("Client timed out", exc_info=True)
            return httputils.REQUEST_TIMEOUT
        with contextlib.ExitStack() as lock_stack:
            lock_stack.enter_context(self._storage.acquire_lock("r", user))
            item = next(iter(self._storage.discover(path)), None)
            if not item:
                return httputils.NOT_FOUND
            if isinstance(item, storage.BaseCollection):
                collection = item
            else:
                assert item.collection is not None
                collection = item.collection
            try:
                status, xml_answer = xml_report(
                    base_prefix, path, xml_content, collection, self._encoding,
                    lock_stack.close)
            except ValueError as e:
                logger.warning(
                    "Bad REPORT request on %r: %s", path, e, exc_info=True)
                return httputils.BAD_REQUEST
        headers = {"Content-Type": "text/xml; charset=%s" % self._encoding}
        return status, headers, self._xml_response(xml_answer)
