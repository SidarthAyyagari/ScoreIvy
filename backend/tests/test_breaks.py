from datetime import datetime, timedelta, timezone

from app.models.models import AttemptSection, PackageTest
from app.models.models import Test as TestRow
from app.models.models import TestSection as TestSectionRow
from tests.conftest import _add_question, auth_headers


def _three_part_test(db, catalog, break_pool_minutes=None, break_after=(None, None, None)):
    """A 3-part test (one question each, 30 minutes each) added to the big package."""
    usmle, physiology = catalog["usmle"], catalog["blocks"].test_sections[0].section
    test = TestRow(exam_id=usmle.id, name="Three Blocks", time_limit_minutes=90, question_count=3,
                   is_active=True, break_pool_minutes=break_pool_minutes)
    db.add(test)
    db.flush()
    for order in (1, 2, 3):
        part = TestSectionRow(test_id=test.id, section_id=None, section_order=order, question_count=1,
                           name=f"Block {order}", time_limit_minutes=30, break_after_minutes=break_after[order - 1])
        db.add(part)
        db.flush()
        _add_question(db, usmle, physiology, test, order, part)
    db.add(PackageTest(package_id=catalog["big_package"].id, test_id=test.id, test_order=2))
    db.commit()
    return test


def _start(client, student, catalog, test):
    user_package_id = client.post(
        f"/api/payments/checkout/{catalog['big_package'].id}", headers=auth_headers(student)
    ).json()["user_package_id"]
    response = client.post(
        f"/api/tests/{test.id}/start", params={"user_package_id": user_package_id}, headers=auth_headers(student)
    )
    assert response.status_code == 200, response.text
    return response.json()


def _submit(client, student, attempt_id, order):
    response = client.post(
        f"/api/tests/attempts/{attempt_id}/sections/{order}/submit",
        json={"question_attempts": []}, headers=auth_headers(student),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _session(client, student, attempt_id):
    return client.get(f"/api/tests/attempts/{attempt_id}/session", headers=auth_headers(student)).json()


def _backdate_completion(db, attempt_id, order, minutes):
    section = db.query(AttemptSection).filter(
        AttemptSection.test_attempt_id == attempt_id, AttemptSection.section_order == order
    ).one()
    section.completed_at = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    db.commit()


def test_overrun_break_starts_next_block_instead_of_ending(client, db, student, catalog):
    test = _three_part_test(db, catalog, break_after=(10, 10, None))
    attempt_id = _start(client, student, catalog, test)["attempt_id"]
    after = _submit(client, student, attempt_id, 1)
    assert after["status"] == "between_sections"
    assert after["next_section"]["break_kind"] == "scheduled"
    assert 590 <= after["next_section"]["break_seconds_remaining"] <= 600

    _backdate_completion(db, attempt_id, 1, minutes=15)
    state = _session(client, student, attempt_id)
    assert state["status"] == "in_section"
    assert state["current_section"]["order"] == 2
    # Block 2's clock started when the 10-minute break ran out, 5 minutes ago.
    assert 24 * 60 <= state["current_section"]["seconds_remaining"] <= 25 * 60 + 5


def test_zero_break_moves_straight_to_next_module(client, db, student, catalog):
    test = _three_part_test(db, catalog, break_after=(0, 10, None))
    attempt_id = _start(client, student, catalog, test)["attempt_id"]
    after = _submit(client, student, attempt_id, 1)
    assert after["status"] == "in_section"
    assert after["current_section"]["order"] == 2
    assert _submit(client, student, attempt_id, 2)["status"] == "between_sections"


def test_shared_break_pool_shrinks_across_breaks(client, db, student, catalog):
    test = _three_part_test(db, catalog, break_pool_minutes=45)
    attempt_id = _start(client, student, catalog, test)["attempt_id"]

    first_break = _submit(client, student, attempt_id, 1)
    assert first_break["next_section"]["break_kind"] == "pool"
    assert 44 * 60 < first_break["next_section"]["break_seconds_remaining"] <= 45 * 60

    _backdate_completion(db, attempt_id, 1, minutes=20)
    client.post(f"/api/tests/attempts/{attempt_id}/sections/2/start", headers=auth_headers(student))

    second_break = _submit(client, student, attempt_id, 2)
    remaining = second_break["next_section"]["break_seconds_remaining"]
    assert 24 * 60 < remaining <= 25 * 60

    _backdate_completion(db, attempt_id, 2, minutes=30)
    state = _session(client, student, attempt_id)
    assert state["status"] == "in_section" and state["current_section"]["order"] == 3


def test_break_can_be_ended_early(client, db, student, catalog):
    test = _three_part_test(db, catalog, break_pool_minutes=45)
    attempt_id = _start(client, student, catalog, test)["attempt_id"]
    _submit(client, student, attempt_id, 1)
    started = client.post(f"/api/tests/attempts/{attempt_id}/sections/2/start", headers=auth_headers(student)).json()
    assert started["status"] == "in_section" and started["current_section"]["order"] == 2
