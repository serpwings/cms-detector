#!/usr/bin/env python
# -*- coding: utf-8 -*- #

"""
cms-detector: A Python Package to detect the Content Management System of a Website.

MIT License
Copyright (c) 2023 SERP Wings www.serpwings.com
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# +++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORTS Standard Library
# +++++++++++++++++++++++++++++++++++++++++++++++++++++

import re
from unittest.mock import Mock

# +++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORTS 3rd Party Libraries
# +++++++++++++++++++++++++++++++++++++++++++++++++++++

import requests
from requests.adapters import HTTPAdapter
from requests.models import Response
from bs4 import BeautifulSoup

# +++++++++++++++++++++++++++++++++++++++++++++++++++++
# DATABASE/CONSTANTS LIST
# +++++++++++++++++++++++++++++++++++++++++++++++++++++

HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
}

# +++++++++++++++++++++++++++++++++++++++++++++++++++++
# Utility Functions
# +++++++++++++++++++++++++++++++++++++++++++++++++++++


def mock_requests_object(url):
    """Generates a mock request object"""
    response = Mock(spec=Response)
    response.text = ""
    response.status_code = 9999
    response.url = url
    return response


def get_remote_content(url, max_retires=2):
    """Get remote content avialble on a given url"""
    try:
        s = requests.Session()
        s.mount(url, HTTPAdapter(max_retries=max_retires))
        return s.get(url, headers=HEADER)
    except:
        return mock_requests_object(url)


def get_corrected_url(url, fix_slash="/"):
    """correct scheme and end slash of a url"""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    if not url.endswith(fix_slash):
        url = f"{url}{fix_slash}"

    return url


def wp_details(target_url):
    """Check if WordPress is installed on a given webiste.

    It will also return name of plugins and themes, if installed on the website.

    """

    target_url = get_corrected_url(target_url, fix_slash="/")
    response = get_remote_content(target_url)

    if response.status_code < 400:
        link_regex = re.compile(
            "((https?):((/)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)",
            re.DOTALL,
        )
        all_link = set([link[0] for link in re.findall(link_regex, response.text)])
        wp_content = [meta for meta in all_link if "wp-content" in meta]
        wp_includes = [meta for meta in all_link if "wp-includes" in meta]
        wp_json = [meta for meta in all_link if "wp-json" in meta]

        themes = [
            re.search("/themes/(.*)/", link) for link in all_link if "/themes/" in link
        ]

        if themes:
            themes = list(
                set([theme.group(1).split("/")[0] for theme in themes if theme])
            )

        plugins = [
            re.search("/plugins/(.*)/", link)
            for link in all_link
            if "/plugins/" in link
        ]

        if plugins:
            plugins = list(
                set([plugin.group(1).split("/")[0] for plugin in plugins if plugin])
            )

        wp_found = False
        wp_version = ""

        if any([wp_content, wp_includes, wp_json]):
            wp_found = True
            soup_xml = BeautifulSoup(response.content, "lxml")
            wp_version_tag = soup_xml.find("meta", attrs={"name": "generator"})
            if wp_version_tag:
                wp_version = wp_version_tag.get("content")

        return {
            "is_wp_installed": wp_found,
            "wp_version": wp_version,
            "themes": themes,
            "plugins": plugins,
        }
