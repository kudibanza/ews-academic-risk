"""
Schema and integrity tests for OULAD raw data.
Run from project root: pytest tests/test_data_schema.py -v
"""
from pathlib import Path

import pandas as pd
import pytest

RAW_DIR = Path("data/raw")

EXPECTED_COLUMNS = {
    "courses.csv": ["code_module", "code_presentation", "module_presentation_length"],
    "assessments.csv": ["code_module", "code_presentation", "id_assessment",
                        "assessment_type", "date", "weight"],
    "vle.csv": ["id_site", "code_module", "code_presentation",
                "activity_type", "week_from", "week_to"],
    "studentAssessment.csv": ["id_assessment", "id_student", "date_submitted",
                              "is_banked", "score"],
    "studentVle.csv": ["code_module", "code_presentation", "id_student",
                       "id_site", "date", "sum_click"],
    "studentInfo.csv": ["code_module", "code_presentation", "id_student",
                        "gender", "region", "highest_education",
                        "imd_band", "age_band", "num_of_prev_attempts",
                        "studied_credits", "disability", "final_result"],
    "studentRegistration.csv": ["code_module", "code_presentation", "id_student",
                                "date_registration", "date_unregistration"],
}


@pytest.fixture(scope="module")
def tables():
    out = {}
    for name in EXPECTED_COLUMNS:
        path = RAW_DIR / name
        assert path.exists(), f"missing file: {path}"
        out[name] = pd.read_csv(path)
    return out


@pytest.mark.parametrize("name", list(EXPECTED_COLUMNS.keys()))
def test_columns_present(tables, name):
    expected = EXPECTED_COLUMNS[name]
    actual = tables[name].columns.tolist()
    missing = [c for c in expected if c not in actual]
    assert not missing, f"{name} missing columns: {missing}"


def test_student_info_key_unique(tables):
    df = tables["studentInfo.csv"]
    key = ["id_student", "code_module", "code_presentation"]
    assert len(df) == len(df.drop_duplicates(subset=key)), \
        "studentInfo has duplicate (id_student, module, presentation) rows"


def test_courses_key_unique(tables):
    df = tables["courses.csv"]
    key = ["code_module", "code_presentation"]
    assert len(df) == len(df.drop_duplicates(subset=key))


def test_assessments_key_unique(tables):
    df = tables["assessments.csv"]
    assert len(df) == len(df.drop_duplicates(subset=["id_assessment"]))


def test_vle_key_unique(tables):
    df = tables["vle.csv"]
    assert len(df) == len(df.drop_duplicates(subset=["id_site"]))


def test_student_registration_key_unique(tables):
    df = tables["studentRegistration.csv"]
    key = ["id_student", "code_module", "code_presentation"]
    assert len(df) == len(df.drop_duplicates(subset=key))


def test_referential_integrity_student_ids(tables):
    info = tables["studentInfo.csv"]
    info_key = set(zip(info["id_student"], info["code_module"], info["code_presentation"]))
    for name in ["studentVle.csv", "studentRegistration.csv"]:
        df = tables[name]
        key = set(zip(df["id_student"], df["code_module"], df["code_presentation"]))
        orphans = key - info_key
        assert not orphans, f"{name} has {len(orphans)} orphan (student, module, pres) keys"


def test_referential_integrity_id_site(tables):
    vle = tables["vle.csv"]
    svle = tables["studentVle.csv"]
    orphans = set(svle["id_site"]) - set(vle["id_site"])
    assert not orphans, f"studentVle has {len(orphans)} orphan id_site values"


def test_referential_integrity_id_assessment(tables):
    asm = tables["assessments.csv"]
    sa = tables["studentAssessment.csv"]
    orphans = set(sa["id_assessment"]) - set(asm["id_assessment"])
    assert not orphans, f"studentAssessment has {len(orphans)} orphan id_assessment values"


def test_final_result_values(tables):
    df = tables["studentInfo.csv"]
    allowed = {"Pass", "Fail", "Withdrawn", "Distinction"}
    observed = set(df["final_result"].unique())
    assert observed.issubset(allowed), f"unexpected final_result values: {observed - allowed}"