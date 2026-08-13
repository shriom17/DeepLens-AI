from services.azure_content import analyze_notice


def process_notice(file_bytes):

    result = analyze_notice(file_bytes)

    fields = result.contents[0].fields

    notice_data = {}

    for field_name, field_value in fields.items():

        if hasattr(field_value, "value_string"):
            notice_data[field_name] = field_value.value_string

        elif hasattr(field_value, "value_array"):
            notice_data[field_name] = [
                item.value_string
                for item in field_value.value_array
            ]

        else:
            notice_data[field_name] = str(field_value)

    return notice_data