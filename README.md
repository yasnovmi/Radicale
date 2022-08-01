# Radicale

[![Test](https://github.com/Kozea/Radicale/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/Kozea/Radicale/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/Kozea/Radicale/badge.svg?branch=master)](https://coveralls.io/github/Kozea/Radicale?branch=master)

Radicale is a small but powerful CalDAV (calendars, to-do lists) and CardDAV
(contacts) server, that:

* Shares calendars and contact lists through CalDAV, CardDAV and HTTP.
* Supports events, todos, journal entries and business cards.
* Works out-of-the-box, no complicated setup or configuration required.
* Can limit access by authentication.
* Can secure connections with TLS.
* Works with many CalDAV and CardDAV clients
* Stores all data on the file system in a simple folder structure.
* Can be extended with plugins.
* Is GPLv3-licensed free software.

For the complete documentation, please visit
[Radicale master Documentation](https://radicale.org/master.html).

This fork using LDAP for sync CardDAV contacts and check LDAP authorization with this plugin [radicale3-auth-ldap.](https://github.com/jdupouy/radicale3-auth-ldap)
