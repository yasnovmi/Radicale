#!/usr/bin/env python3

from setuptools import setup

setup(
    name="radicale3-auth-ldap",
    version="3.0",
    description="LDAP Authentication Plugin for Radicale 3",
    author="Raoul Thill",
    license="GNU GPL v3",
    install_requires=["radicale >= 3.0", "ldap3 >= 2.3"],
    packages=["radicale3_auth_ldap"])
