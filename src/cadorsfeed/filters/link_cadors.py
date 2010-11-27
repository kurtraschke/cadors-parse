import re

cadors_re = re.compile(r"\b[0-9]{4}[AOPCQ][0-9]{4}\b")


def replace_cadors_links(text, link_function):
    substitutions = {}
    matches = cadors_re.finditer(text)

    for match in matches:
        text = match.group()
        url = "http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/qs.aspx?lang=eng&cadorsno=" + text
        title = "CADORS Report " + text
        substitutions[match] = link_function(url, match.group(), title, None)

    return substitutions
