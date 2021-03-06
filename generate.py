from collections import OrderedDict, namedtuple
from typing import Any

create_metadata = namedtuple('metadata', ('career_page', 'strike_out', 'glassdoor__link', 'software_engineer__link'))


# % README Generation API


def make_table_headers(headers: list):
    header_titles = "| " + " | ".join(headers) + " |"
    word_lengths = [len(header) + 2 for header in headers]
    table_structure = "|" + "|".join("-" * word_length for word_length in word_lengths) + '|'
    return f'{header_titles}\n{table_structure}'


def parse_row_data(key: str, data: dict, columns_mapping: dict) -> (dict, create_metadata):
    """
    Extracts out column -> Values and the associated metadata with this company
    """
    data['key'] = key
    row = OrderedDict()

    for column_key in columns_mapping.keys():
        if column_key == 'benefits':
            column_value = _translate_benefits(data['benefits'])
        else:
            column_value = _get_data(column_key, data)
        row[column_key] = column_value

    metadata = _get_metadata(data)
    return row, metadata


def row_data_to_row_markdown(row_data: dict, metadata: create_metadata):
    is_strike_out = metadata.strike_out
    metadata = {'glassdoor': metadata.glassdoor__link,
                'software_engineer': metadata.software_engineer__link,
                'key': metadata.career_page}

    row_markdown = '|'

    for column, value in row_data.items():
        value = "Yes" if value is True else "No" if value is False else value

        if is_strike_out & (column != 'office_picture'):
            if isinstance(value, list):
                value = [f"~~{v}~~" if v != '' else v for v in value]
            else:
                value = f"~~{value}~~" if value != '' else value

        if column.split('__')[0] in metadata:
            value = f'[{value}]({metadata[column.split("__")[0]]})'

        elif column == 'office_picture':
            value = f'<img src="{value}" alt="{row_data["key"]} Office" height="250" width="400" >'

        elif (column == 'benefits') or isinstance(value, list):
            value = _create_markdown_bullet_list(value)

        row_markdown += f' {value} |'

    return row_markdown


# % Utilities

def _get_data(key: str, nested_data: dict) -> Any:
    sub_key_i = key.rfind('__')
    if sub_key_i != -1:
        return _get_data(key[(sub_key_i + 2):], _get_data(key[:sub_key_i], nested_data))
    if key and nested_data:
        return nested_data.get(key, None)
    return None


def _get_metadata(data: dict, metadata_fields=create_metadata._fields):
    return create_metadata(**{metadata: _get_data(metadata, data) for metadata in metadata_fields})


def _create_markdown_bullet_list(items: list):
    bullet_items = ' '.join(f'<li> {item} </li>' for item in items)
    return f'<ul> {bullet_items} </ul>'


def _translate_benefits(benefits: dict) -> list:
    """
    Rule based NLP
    """
    benefit = []

    if benefits.get('good_insurance'):
        benefit.append("Has good insurance")
    else:
        benefit.append('Has standard insurance')
    if benefits.get('pregnancy') or benefits.get('covers_dependents'):
        benefit[0] = "Has GREAT insurance"

    if benefits.get('pregnancy'):
        benefit.append("Pregnancy & childbirth is covered")

    if benefits.get('covers_dependents'):
        benefit.append("Insurance is extended to dependents")

    try:
        if benefits.get('maternity_leaves') > 4:
            benefit.append(f"Maternity leave is more than standard, {benefits.get('maternity_leaves')} months")
        else:
            benefit.append("Maternity leave is standard to gov policy")
    except TypeError: 
        benefit.append("WIP")

    if (benefits.get('extras') is not None) and (benefits.get('extras') is not False):
        benefit.append(benefits.get('extras'))

    return benefit
