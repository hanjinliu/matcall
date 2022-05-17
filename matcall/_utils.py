import re

_HTML_PATTERN = re.compile(r"<[^>]*?>")

def remove_html(s: str):
    _disps = s.split("\n")
    for i, line in enumerate(_disps):
        n0 = line.count("<")
        n1 = line.count(">")
        if "</" in line and n0 == n1 and n0 > 1:
            _disps[i] = _HTML_PATTERN.sub("", line)
    return "\n".join(_disps)
