from app.models.models import Question, Section, User
from app.models.models import Test as TestRow
from app.models.models import TestQuestion as TestQuestionRow
from app.models.models import TestSection as TestSectionRow
from tests.conftest import auth_headers


def _admin_headers(db):
    admin = User(email="admin@example.com", is_active=True, is_admin=True)
    db.add(admin)
    db.commit()
    return auth_headers(admin)


def _bank(db, catalog, physiology_count=12, pharmacology_count=8):
    usmle = catalog["usmle"]
    sections = {s.name: s for s in db.query(Section).filter(Section.exam_id == usmle.id)}
    for name, count in (("Physiology", physiology_count), ("Pharmacology", pharmacology_count)):
        for n in range(count):
            db.add(Question(exam_id=usmle.id, section_id=sections[name].id, question_text=f"{name} bank {n}",
                            answer_choices={"A": "a", "B": "b"}, correct_answer="A"))
    db.commit()
    return sections


def _request(catalog, **overrides):
    body = {
        "exam_id": catalog["usmle"].id,
        "name": "Full-Length 1",
        "parts": [
            {"name": "Block 1", "question_count": 8, "time_limit_minutes": 60},
            {"name": "Block 2", "question_count": 8, "time_limit_minutes": 60},
        ],
        "break_pool_minutes": 45,
        "seed": 7,
    }
    body.update(overrides)
    return body


def test_pool_counts_only_unused_active_questions(client, db, catalog):
    headers = _admin_headers(db)
    _bank(db, catalog)
    pool = client.get("/api/admin/test-builder/pool", params={"exam_id": catalog["usmle"].id}, headers=headers).json()
    assert pool["total"] == 20
    assert {row["name"]: row["count"] for row in pool["by_section"]} == {"Pharmacology": 8, "Physiology": 12}


def test_dry_run_previews_without_saving(client, db, catalog):
    headers = _admin_headers(db)
    _bank(db, catalog)
    tests_before = db.query(TestRow).count()
    preview = client.post("/api/admin/test-builder", json=_request(catalog, dry_run=True), headers=headers).json()
    assert preview["test_id"] is None and preview["problems"] == []
    assert [p["question_count"] for p in preview["parts"]] == [8, 8]
    first = preview["parts"][0]["by_section"]
    assert first["Physiology"] + first["Pharmacology"] == 8 and first["Physiology"] > first["Pharmacology"]
    assert preview["pool_remaining"] == 4
    assert db.query(TestRow).count() == tests_before


def test_build_creates_timed_blocks_without_repeats(client, db, student, catalog):
    headers = _admin_headers(db)
    _bank(db, catalog)
    result = client.post(
        "/api/admin/test-builder", json=_request(catalog, package_id=catalog["big_package"].id), headers=headers
    )
    assert result.status_code == 200, result.text
    test_id = result.json()["test_id"]

    test = db.get(TestRow, test_id)
    assert test.break_pool_minutes == 45 and test.question_count == 16 and test.time_limit_minutes == 120
    parts = db.query(TestSectionRow).filter(TestSectionRow.test_id == test_id).order_by(TestSectionRow.section_order).all()
    assert [(p.name, p.question_count, p.time_limit_minutes, p.section_id) for p in parts] == [
        ("Block 1", 8, 60, None), ("Block 2", 8, 60, None),
    ]
    rows = db.query(TestQuestionRow).filter(TestQuestionRow.test_id == test_id).all()
    assert len({r.question_id for r in rows}) == 16
    assert sorted(r.question_order for r in rows) == list(range(1, 17))

    user_package_id = client.post(
        f"/api/payments/checkout/{catalog['big_package'].id}", headers=auth_headers(student)
    ).json()["user_package_id"]
    session = client.post(
        f"/api/tests/{test_id}/start", params={"user_package_id": user_package_id}, headers=auth_headers(student)
    ).json()
    assert session["current_section"]["name"] == "Block 1"
    assert len(session["current_section"]["questions"]) == 8


def test_second_build_reports_shortfall_unless_reuse_allowed(client, db, catalog):
    headers = _admin_headers(db)
    _bank(db, catalog)
    assert client.post("/api/admin/test-builder", json=_request(catalog), headers=headers).status_code == 200

    again = client.post("/api/admin/test-builder", json=_request(catalog, name="Full-Length 2"), headers=headers)
    assert again.status_code == 409
    assert "Block 1 needs 8 questions but only 4 are available" in again.json()["detail"]

    reuse = client.post(
        "/api/admin/test-builder", json=_request(catalog, name="Full-Length 2", exclude_used=False), headers=headers
    )
    assert reuse.status_code == 200


def test_part_can_be_limited_to_subjects(client, db, catalog):
    headers = _admin_headers(db)
    sections = _bank(db, catalog)
    pharm = sections["Pharmacology"].id
    body = _request(catalog, parts=[
        {"name": "Pharm module", "question_count": 8, "time_limit_minutes": 30, "section_ids": [pharm],
         "break_after_minutes": 10},
    ])
    test_id = client.post("/api/admin/test-builder", json=body, headers=headers).json()["test_id"]
    part = db.query(TestSectionRow).filter(TestSectionRow.test_id == test_id).one()
    assert part.section_id == pharm and part.break_after_minutes == 10
    picked = db.query(Question).join(TestQuestionRow, TestQuestionRow.question_id == Question.id).filter(
        TestQuestionRow.test_id == test_id
    ).all()
    assert {q.section_id for q in picked} == {pharm}


def test_builder_requires_admin(client, student, catalog):
    response = client.post("/api/admin/test-builder", json=_request(catalog), headers=auth_headers(student))
    assert response.status_code == 403
