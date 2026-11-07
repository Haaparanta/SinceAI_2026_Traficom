"""scripts/import_issue.py: the steps before the pipeline (zip, verify, extract, preflight), on synthetic zips.

No network, no mdbtools and no ITU data needed. The pipeline steps it calls (convert, screen, evidence, cache) have
their own tests; a real import is `make import KIND=terrestrial ISSUE=3078`.
"""
from __future__ import annotations

import os
import time
import zipfile
from pathlib import Path

import pytest

from radar.config import settings
from scripts import import_issue as I

JET = b"\x00\x01\x00\x00Standard Jet DB\x00" + b"\x00" * 64     # the first bytes of an Access 2000-2003 .mdb


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    (tmp_path / "raw").mkdir()
    return tmp_path


def make_zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, body in members.items():
            zf.writestr(name, body)
    return path


def test_urls_follow_the_itu_patterns():
    assert I.url("space", 3077) == "https://www.itu.int/sns/ific10/ific3077.zip"
    assert I.url("terrestrial", 3077) == "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3077.zip"


def test_paths_match_the_existing_layout(data):
    p = I.Paths("terrestrial", 3076)
    assert p.zip == data / "raw" / "brific3076.zip"
    assert p.mdb == data / "raw" / "brific3076" / "brific3076.mdb"
    assert p.duckdb == data / "derived" / "terrestrial_3076.duckdb"
    assert I.Paths("space", 3074).duckdb.name == "space_3074.duckdb"     # the names the adapters open


def test_a_good_zip_passes(tmp_path):
    z = make_zip(tmp_path / "ific3077.zip", {"ific3077.mdb": JET, "readme.txt": b"notes"})
    assert I.mdb_member(z, "ific3077").filename == "ific3077.mdb"


@pytest.mark.parametrize("members, message", [
    ({}, "found none"),
    ({"readme.txt": b"x"}, "found none"),
    ({"ific3077.mdb": JET, "other/ific3077.mdb": JET}, "exactly one .mdb"),
    ({"ific3076.mdb": JET}, "wrong issue number"),
    ({"brific3077.mdb": JET}, "wrong issue number"),          # a terrestrial zip given as space
])
def test_zip_contents_are_checked(tmp_path, members, message):
    z = make_zip(tmp_path / "ific3077.zip", members)
    with pytest.raises(I.StepFailed, match=message):
        I.mdb_member(z, "ific3077")


def test_an_html_error_page_is_not_a_zip(tmp_path):
    z = tmp_path / "ific3077.zip"
    z.write_text("<html>404 Not Found</html>")
    with pytest.raises(I.StepFailed, match="not a zip file"):
        I.mdb_member(z, "ific3077")


def test_a_corrupt_member_fails_the_crc_check(tmp_path):
    z = make_zip(tmp_path / "ific3077.zip", {"ific3077.mdb": JET * 50})
    raw = bytearray(z.read_bytes())
    start = raw.index(b"ific3077.mdb") + len("ific3077.mdb")     # first local header: data follows the name
    raw[start + 5] ^= 0xFF
    z.write_bytes(bytes(raw))
    with pytest.raises(I.StepFailed, match="damaged|CRC error"):
        I.mdb_member(z, "ific3077")


def test_a_flipped_byte_in_a_stored_member_is_a_crc_error(tmp_path):
    z = tmp_path / "ific3077.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("ific3077.mdb", JET)
    raw = bytearray(z.read_bytes())
    raw[raw.index(b"Standard Jet DB")] ^= 0xFF                 # data intact in size, wrong in content
    z.write_bytes(bytes(raw))
    with pytest.raises(I.StepFailed, match="CRC error in ific3077.mdb"):
        I.mdb_member(z, "ific3077")


def test_a_bad_local_zip_never_lands_in_data_raw(data, tmp_path):
    bad = tmp_path / "elsewhere.zip"
    bad.write_text("<html></html>")
    p = I.Paths("space", 3077)
    with pytest.raises(I.StepFailed):
        I.get_zip(p, bad, force=False)
    assert not p.zip.exists() and not list((data / "raw").glob("*.part"))


def test_a_local_zip_is_copied_into_place(data, tmp_path):
    src = make_zip(tmp_path / "download.zip", {"ific3077.mdb": JET})
    p = I.Paths("space", 3077)
    assert I.get_zip(p, src, force=False) == str(src.resolve())
    assert p.zip.read_bytes() == src.read_bytes()
    assert I.get_zip(p, p.zip, force=False) == str(p.zip.resolve())   # giving the file already in place is a no-op


def test_an_existing_zip_is_not_downloaded_again(data, monkeypatch):
    p = I.Paths("space", 3077)
    make_zip(p.zip, {"ific3077.mdb": JET})
    monkeypatch.setattr(I, "download", lambda *a: pytest.fail("must not download"))
    assert I.get_zip(p, None, force=False) == I.url("space", 3077)


def test_extract_writes_a_fixed_name_whatever_the_archive_path(data):
    p = I.Paths("space", 3077)
    make_zip(p.zip, {"../../outside/ific3077.mdb": JET})     # a path that tries to leave data/raw
    I.extract(p, force=False)
    assert p.mdb.read_bytes() == JET
    assert not (data / "outside").exists() and not (data.parent / "outside").exists()


def test_extract_skips_an_up_to_date_mdb_and_rejects_a_non_access_file(data):
    p = I.Paths("terrestrial", 3077)
    make_zip(p.zip, {"brific3077.mdb": JET})
    I.extract(p, force=False)
    before = p.mdb.stat().st_mtime_ns
    I.extract(p, force=False)
    assert p.mdb.stat().st_mtime_ns == before                  # skipped

    make_zip(p.zip, {"brific3077.mdb": b"not an access database".ljust(len(JET))})
    os.utime(p.zip, (time.time() + 5, time.time() + 5))        # newer than the .mdb: extracted again
    with pytest.raises(I.StepFailed, match="not an Access"):
        I.extract(p, force=False)


def test_convert_is_skipped_when_the_database_is_newer(data):
    p = I.Paths("space", 3077)
    p.mdb.parent.mkdir(parents=True)
    p.mdb.write_bytes(JET)
    p.duckdb.parent.mkdir(parents=True)
    p.duckdb.write_bytes(b"db")
    os.utime(p.duckdb, (time.time() + 5, time.time() + 5))
    assert I.convert(p, force=False) is None


def test_preflight_needs_the_finnish_table(data):
    with pytest.raises(I.StepFailed, match="Finnish frequency table"):
        I.preflight(I.Paths("space", 3077), force=False)


def test_graded_issues_are_refused_without_the_special_interest_xls(data, monkeypatch):
    (data / "raw" / "taajuusjakotaulukko.json").write_text("[]")
    monkeypatch.setenv("SPECIAL_INTEREST_XLSX", str(data / "raw" / "missing.xlsx"))
    for kind, issue in sorted(I.GRADED):
        with pytest.raises(I.StepFailed, match="graded issue"):
            I.preflight(I.Paths(kind, issue), force=False)
        assert I.preflight(I.Paths(kind, issue), force=True) is False      # --force screens without stations
    assert I.preflight(I.Paths("space", 3077), force=False) is False       # other issues: a warning only


def test_cli_checks_its_arguments(capsys):
    assert I.main(["--kind", "space", "--issue", "3077", "--print-url"]) == 0
    assert capsys.readouterr().out.strip() == I.url("space", 3077)
    with pytest.raises(SystemExit):
        I.main(["--kind", "space", "--issue", "77"])
    with pytest.raises(SystemExit):
        I.main(["--issue", "3077"])                            # --kind is required: the numbers overlap
