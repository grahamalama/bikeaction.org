import json
import re
import urllib.request

# Map CF7 field names to the labels used by violation-matcher.ts
FIELD_NAME_MAP = {
    "vehicle_make": "Make",
    "body_style": "Body Style",
    "vehicle_color": "Vehicle Color",
    "violation_observed": "Violation Observed",
    "frequency": "How frequently does this occur?",
}


def parse_html_form(html_content):
    """Parse CF7 HTML form to extract select fields and their options."""
    mapping = {}

    select_pattern = r"<select[^>]*>(.*?)</select>"

    for select_match in re.finditer(select_pattern, html_content, re.DOTALL):
        select_tag = html_content[select_match.start() : select_match.end()]
        name_match = re.search(r'name="([^"]*)"', select_tag)
        if not name_match:
            continue
        name = name_match.group(1)
        select_content = select_match.group(1)

        # Map CF7 field name to display label
        label = FIELD_NAME_MAP.get(name)
        if not label:
            continue

        # Extract option values (skip empty placeholder options)
        option_pattern = r'<option[^>]*value="([^"]*)"[^>]*>[^<]*</option>'
        options = []
        for opt_match in re.finditer(option_pattern, select_content):
            value = opt_match.group(1).strip()
            if value:
                options.append(value)

        if options:
            mapping[label] = options

    return mapping


req = urllib.request.Request(
    "https://philapark.org/mobility-access-violation-form/",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
)
r = urllib.request.urlopen(req)
html = r.read().decode()
form_mapping_json = parse_html_form(html)

print(json.dumps(form_mapping_json, indent=2))
