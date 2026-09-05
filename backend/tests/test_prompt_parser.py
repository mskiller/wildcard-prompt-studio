import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.services.prompt_parser import parse_prompt_file

def test_parse_prompt_format():
    content = """name: Cyberpunk Warrior
author: User
---
subject:
- female warrior
style:
- cinematic"""
    result = parse_prompt_file(content)
    assert result["metadata"]["name"] == "Cyberpunk Warrior"
    assert result["metadata"]["author"] == "User"
    assert "female warrior" in result["sections"]["subject"]
    assert "cinematic" in result["sections"]["style"]

def test_parse_prompt_format_no_metadata():
    content = """subject:
- female warrior"""
    result = parse_prompt_file(content)
    assert result["metadata"] == {}
    assert "female warrior" in result["sections"]["subject"]
