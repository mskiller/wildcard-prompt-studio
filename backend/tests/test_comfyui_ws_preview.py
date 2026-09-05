import base64
import json
from app.services.comfyui_ws import parse_ws_message


def test_parse_binary_preview_message():
    header = (1).to_bytes(4, byteorder='big') + (1).to_bytes(4, byteorder='big')
    jpeg_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 20
    raw_ws_payload = header + jpeg_bytes

    msg_type, payload = parse_ws_message(raw_ws_payload)
    assert msg_type == "PREVIEW_IMAGE"
    assert payload.startswith("data:image/jpeg;base64,")


def test_parse_binary_png_preview_message():
    header = (1).to_bytes(4, byteorder='big') + (2).to_bytes(4, byteorder='big')
    png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 20
    raw_ws_payload = header + png_bytes

    msg_type, payload = parse_ws_message(raw_ws_payload)
    assert msg_type == "PREVIEW_IMAGE"
    assert payload.startswith("data:image/png;base64,")


def test_parse_json_ws_message():
    json_str = json.dumps({"type": "executing", "data": {"node": "5"}})
    msg_type, payload = parse_ws_message(json_str)
    assert msg_type == "executing"
    assert payload == {"node": "5"}


def test_parse_dict_ws_message():
    dict_msg = {"type": "progress", "data": {"value": 50, "max": 100}}
    msg_type, payload = parse_ws_message(dict_msg)
    assert msg_type == "progress"
    assert payload == {"value": 50, "max": 100}
