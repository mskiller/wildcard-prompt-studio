import pytest
from app.services.importer import ImporterService

def test_parse_txt_wildcard():
    content = "red cat\nblue dog\n# comment line\n"
    res = ImporterService.parse_txt("animals.txt", content)
    assert "animals" in res
    assert res["animals"] == ["red cat", "blue dog"]

def test_export_wildcards_to_txt():
    wildcards = {"colors": ["red", "green", "blue"]}
    txt = ImporterService.export_to_txt("colors", wildcards["colors"])
    assert "red\ngreen\nblue" in txt
