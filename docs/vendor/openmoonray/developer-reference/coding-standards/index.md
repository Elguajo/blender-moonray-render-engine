---
title: MoonRay Coding Standards
---
# Coding Standards

This document details the coding practices that are used in the MoonRay codebase. Contributed code should conform to
these guidelines to maintain consistency and maintainability. If there is a rule that you would like clarified, changed,
or added, please send a note to [MoonRay@dreamworks.com](mailto:MoonRay@dreamworks.com).

The single most important guideline to ahere to is to follow the local standards and style of the source file you are editing. Where more detail is needed, please refer to the relevant section below.

{% assign section = site.data.site-nav-tree[2].subitems[4].subitems %}
{%- for item in section -%}
- [{{ item.text }}]({{ item.path | replace: "index.md", "" | relative_url | replace: ".md", "/"}})
{% endfor %}

