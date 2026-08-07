from __future__ import annotations


def decode_non_ascii_percent_escapes(value: str) -> str:
    """Decode UTF-8 URL escapes while preserving escaped ASCII delimiters."""
    output: list[str] = []
    index = 0
    while index < len(value):
        if index + 2 >= len(value) or value[index] != "%":
            output.append(value[index])
            index += 1
            continue
        try:
            first = int(value[index + 1 : index + 3], 16)
        except ValueError:
            output.append(value[index])
            index += 1
            continue
        if first < 0x80:
            output.append(value[index : index + 3].upper())
            index += 3
            continue
        if 0xC2 <= first <= 0xDF:
            length = 2
        elif 0xE0 <= first <= 0xEF:
            length = 3
        elif 0xF0 <= first <= 0xF4:
            length = 4
        else:
            output.append(value[index : index + 3].upper())
            index += 3
            continue
        encoded_length = length * 3
        encoded = value[index : index + encoded_length]
        if len(encoded) != encoded_length or any(encoded[offset] != "%" for offset in range(0, encoded_length, 3)):
            output.append(value[index : index + 3].upper())
            index += 3
            continue
        try:
            raw = bytes(int(encoded[offset + 1 : offset + 3], 16) for offset in range(0, encoded_length, 3))
            decoded = raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            output.append(value[index : index + 3].upper())
            index += 3
            continue
        output.append(decoded)
        index += encoded_length
    return "".join(output)
