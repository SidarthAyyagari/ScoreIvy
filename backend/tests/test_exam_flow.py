from datetime import datetime, timedelta, timezone

from app.models.models import AttemptSection, UserPackage
from tests.conftest import auth_headers


def _purchase(client, student, package):
    response = client.post(f"/api/payments/checkout/{package.id}", headers=auth_headers(student))
    assert response.status_code == 200
    user_package_id = response.json()["user_package_id"]
    purchased = client.get("/api/packages/user/purchased", headers=auth_headers(student)).json()
    return next(item for item in purchased if item["id"] == user_package_id)


def _start(client, student, test_id, user_package_id):
    return client.post(
        f"/api/tests/{test_id}/start",
        params={"user_package_id": user_package_id},
        headers=auth_headers(student),
    )


def _save(client, student, attempt_id, question_id, answer):
    return client.put(
        f"/api/tests/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "selected_answer": answer},
        headers=auth_headers(student),
    )


def _submit_section(client, student, attempt_id, order, answers=()):
    return client.post(
        f"/api/tests/attempts/{attempt_id}/sections/{order}/submit",
        json={"question_attempts": [{"question_id": q, "selected_answer": a} for q, a in answers]},
        headers=auth_headers(student),
    )


def _expire_current_section(db, attempt_id, minutes_ago=10):
    section = (
        db.query(AttemptSection)
        .filter(AttemptSection.test_attempt_id == attempt_id, AttemptSection.completed_at.is_(None))
        .order_by(AttemptSection.section_order)
        .first()
    )
    section.deadline_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    db.commit()


def test_exams_and_packages_are_listed_per_exam(client, catalog):
    exams = client.get("/api/exams/").json()
    assert [e["slug"] for e in exams] == ["usmle-step-1", "sat"]
    assert exams[1]["tools"] == ["calculator", "reference_sheet"]
    sat_packages = client.get("/api/packages/", params={"exam": "sat"}).json()
    assert [p["name"] for p in sat_packages] == ["SAT Starter"]


def test_purchase_sets_expiry_from_package_validity(client, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    expires_at = datetime.fromisoformat(user_package["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    expected = datetime.now(timezone.utc) + timedelta(days=30)
    assert abs((expires_at - expected).total_seconds()) < 60


def test_user_cannot_edit_or_delete_own_package_or_attempts(client, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    headers = auth_headers(student)
    assert client.put(
        f"/api/packages/user-packages/{user_package['id']}", json={"tests_remaining": 999}, headers=headers
    ).status_code in (404, 405)
    assert client.delete(f"/api/packages/user-packages/{user_package['id']}", headers=headers).status_code in (404, 405)
    assert client.put("/api/test-results/attempts/1", json={"score": 100}, headers=headers).status_code in (404, 405)


def test_test_detail_requires_auth_and_hides_questions(client, student, catalog):
    test_id = catalog["test1"].id
    assert client.get(f"/api/tests/{test_id}").status_code == 401
    body = client.get(f"/api/tests/{test_id}", headers=auth_headers(student)).json()
    assert "questions" not in body


def test_start_consumes_one_credit_and_resume_does_not(client, db, student, catalog):
    user_package = _purchase(client, student, catalog["package"])

    first = _start(client, student, catalog["test1"].id, user_package["id"])
    assert first.status_code == 200
    session = first.json()
    assert session["status"] == "in_section"
    assert session["test"]["exam"]["tools"] == ["lab_values"]
    current = session["current_section"]
    assert len(current["questions"]) == 3
    assert all("correct_answer" not in q for q in current["questions"])
    assert 3500 < current["seconds_remaining"] <= 3600

    resumed = _start(client, student, catalog["test1"].id, user_package["id"])
    assert resumed.json()["attempt_id"] == session["attempt_id"]

    db.expire_all()
    assert db.get(UserPackage, user_package["id"]).tests_remaining == 1


def test_single_section_submit_grades_every_question_and_blocks_retake(client, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    headers = auth_headers(student)
    session = _start(client, student, catalog["test1"].id, user_package["id"]).json()
    attempt_id = session["attempt_id"]
    q1, q2, _q3 = [q["id"] for q in session["current_section"]["questions"]]

    assert _save(client, student, attempt_id, q1, "A").status_code == 204
    assert client.get(f"/api/test-results/attempts/{attempt_id}/results", headers=headers).status_code == 409

    done = _submit_section(client, student, attempt_id, 1, [(q2, "B")])
    assert done.status_code == 200
    assert done.json()["status"] == "completed"

    results = client.get(f"/api/test-results/attempts/{attempt_id}/results", headers=headers).json()
    assert results["attempt"]["total_questions"] == 3
    assert results["attempt"]["correct_answers"] == 1
    assert [q["selected_answer"] for q in results["questions"]] == ["A", "B", None]
    [section_score] = results["attempt"]["section_scores"]
    assert (section_score["name"], section_score["correct"], section_score["total"]) == ("Physiology", 1, 3)
    assert section_score["scaled"] is None

    assert _submit_section(client, student, attempt_id, 1).status_code == 409
    assert _start(client, student, catalog["test1"].id, user_package["id"]).status_code == 409
    available = client.get(f"/api/tests/user-package/{user_package['id']}/available", headers=headers).json()
    assert [t["id"] for t in available] == [catalog["test2"].id]


def test_multi_block_exam_serves_and_locks_one_block_at_a_time(client, db, student, catalog):
    user_package = _purchase(client, student, catalog["big_package"])
    session = _start(client, student, catalog["blocks"].id, user_package["id"]).json()
    attempt_id = session["attempt_id"]

    assert [s["status"] for s in session["sections"]] == ["active", "pending"]
    assert [s["name"] for s in session["sections"]] == ["Block 1", "Block 2"]
    block1 = [q["id"] for q in session["current_section"]["questions"]]
    assert len(block1) == 2
    assert 3500 < session["current_section"]["seconds_remaining"] <= 3600

    after_block1 = _submit_section(client, student, attempt_id, 1, [(block1[0], "A")]).json()
    assert after_block1["status"] == "between_sections"
    assert after_block1["next_section"]["order"] == 2
    assert after_block1["current_section"] is None

    assert _save(client, student, attempt_id, block1[1], "A").status_code == 409

    block2 = client.post(
        f"/api/tests/attempts/{attempt_id}/sections/2/start", headers=auth_headers(student)
    ).json()
    assert block2["status"] == "in_section"
    block2_ids = [q["id"] for q in block2["current_section"]["questions"]]
    assert len(block2_ids) == 1
    assert 1700 < block2["current_section"]["seconds_remaining"] <= 1800

    assert _save(client, student, attempt_id, block1[1], "A").status_code == 400

    final = _submit_section(client, student, attempt_id, 2, [(block2_ids[0], "A")]).json()
    assert final["status"] == "completed"
    results = client.get(
        f"/api/test-results/attempts/{attempt_id}/results", headers=auth_headers(student)
    ).json()
    assert results["attempt"]["correct_answers"] == 2
    scores = {s["name"]: (s["correct"], s["total"]) for s in results["attempt"]["section_scores"]}
    assert scores == {"Physiology": (1, 2), "Pharmacology": (1, 1)}


def test_abandoned_attempt_runs_out_every_block_and_is_graded(client, db, student, catalog):
    user_package = _purchase(client, student, catalog["big_package"])
    session = _start(client, student, catalog["blocks"].id, user_package["id"]).json()
    attempt_id = session["attempt_id"]
    q1 = session["current_section"]["questions"][0]["id"]
    _save(client, student, attempt_id, q1, "A")

    _expire_current_section(db, attempt_id)
    state = client.get(f"/api/tests/attempts/{attempt_id}/session", headers=auth_headers(student)).json()
    assert state["status"] == "between_sections"

    section1 = db.query(AttemptSection).filter(
        AttemptSection.test_attempt_id == attempt_id, AttemptSection.section_order == 1
    ).one()
    section1.completed_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db.commit()

    ended = client.get(f"/api/tests/attempts/{attempt_id}/session", headers=auth_headers(student)).json()
    assert ended["status"] == "completed"
    results = client.get(
        f"/api/test-results/attempts/{attempt_id}/results", headers=auth_headers(student)
    ).json()
    assert results["attempt"]["correct_answers"] == 1
    assert results["attempt"]["total_questions"] == 3


def test_late_submission_is_graded_on_autosaved_answers_only(client, db, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    session = _start(client, student, catalog["test1"].id, user_package["id"]).json()
    attempt_id = session["attempt_id"]
    q1, q2, _q3 = [q["id"] for q in session["current_section"]["questions"]]
    _save(client, student, attempt_id, q1, "A")

    _expire_current_section(db, attempt_id)

    assert _save(client, student, attempt_id, q2, "A").status_code == 409
    assert _submit_section(client, student, attempt_id, 1, [(q2, "A")]).status_code == 409
    results = client.get(
        f"/api/test-results/attempts/{attempt_id}/results", headers=auth_headers(student)
    ).json()
    assert results["attempt"]["correct_answers"] == 1


def test_numeric_entry_accepts_equivalent_values_and_scales_score(client, student, catalog):
    user_package = _purchase(client, student, catalog["sat_package"])
    session = _start(client, student, catalog["sat_test"].id, user_package["id"]).json()
    attempt_id = session["attempt_id"]
    mc, numeric = session["current_section"]["questions"]
    assert numeric["question_type"] == "numeric_entry"
    assert numeric["answer_choices"] == {}

    assert _save(client, student, attempt_id, numeric["id"], "abc").status_code == 400
    assert _save(client, student, attempt_id, numeric["id"], "0.750").status_code == 204

    _submit_section(client, student, attempt_id, 1, [(mc["id"], "B")])
    results = client.get(
        f"/api/test-results/attempts/{attempt_id}/results", headers=auth_headers(student)
    ).json()
    assert results["attempt"]["correct_answers"] == 1
    assert results["attempt"]["section_scores"][0]["scaled"] == 500
    assert results["attempt"]["scaled_score"] == 500


def test_invalid_answers_are_rejected(client, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    session = _start(client, student, catalog["test1"].id, user_package["id"]).json()
    attempt_id = session["attempt_id"]
    assert _save(client, student, attempt_id, 99999, "A").status_code == 400
    first = session["current_section"]["questions"][0]["id"]
    assert _save(client, student, attempt_id, first, "Z").status_code == 400


def test_cannot_start_test_outside_package(client, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    assert _start(client, student, catalog["other"].id, user_package["id"]).status_code == 404


def test_cannot_use_someone_elses_package(client, db, student, catalog):
    from app.models.models import User

    user_package = _purchase(client, student, catalog["package"])
    other = User(email="other@example.com", is_active=True)
    db.add(other)
    db.commit()
    assert _start(client, other, catalog["test1"].id, user_package["id"]).status_code == 404


def test_expired_package_cannot_start_tests(client, db, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    row = db.get(UserPackage, user_package["id"])
    row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    assert _start(client, student, catalog["test1"].id, user_package["id"]).status_code == 403
    available = client.get(
        f"/api/tests/user-package/{user_package['id']}/available", headers=auth_headers(student)
    ).json()
    assert available == []


def test_no_credits_left_cannot_start_tests(client, db, student, catalog):
    user_package = _purchase(client, student, catalog["package"])
    row = db.get(UserPackage, user_package["id"])
    row.tests_remaining = 0
    db.commit()
    assert _start(client, student, catalog["test1"].id, user_package["id"]).status_code == 403
