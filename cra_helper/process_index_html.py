import re

endblock_re = re.compile(r'{%\s*endblock\s*%}')
style_sheet_re = re.compile(r'^\s*<head><([^<]*)</head>')


def process_html(html: str) -> str:
    # move style sheet link to the end
    matches = list(style_sheet_re.finditer(html))
    if matches:
        link = '<' + matches[0].group(1)
        pos = matches[0].regs[1][1]
        html = html[pos + 7:] + link

    # push script & style sheet into {% block %}
    matches = list(endblock_re.finditer(html))
    if matches:
        start, end = matches[::-1][0].span()
        html = html[0:start] + html[end:] + '{% endblock %}'

    return html
