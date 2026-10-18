from app.models.models import Question, User
from app.models.models import TestQuestion as TestQuestionRow
from tests.conftest import auth_headers


def _admin_headers(db):
    admin = User(email="admin@example.com", is_active=True, is_admin=True)
    db.add(admin)
    db.commit()
    return auth_headers(admin)


def _new_question(client, headers, exam_id, **fields):
    body = {
        "exam_id": exam_id,
        "question_text": "Which nerve?",
        "answer_choices": {"A": "Ulnar", "B": "Median"},
        "correct_answer": "A",
        "explanation": "Because.",
        "tags": ["system:Musculoskeletal"],
        **fields,
    }
    response = client.post("/api/questions/", headers=headers, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _start(client, student, package, test):
    user_package_id = client.post(
        f"/api/payments/checkout/{package.id}", headers=auth_headers(student)
    ).json()["user_package_id"]
    response = client.post(
        f"/api/tests/{test.id}/start", params={"user_package_id": user_package_id}, headers=auth_headers(student)
    )
    assert response.status_code == 200, response.text
    return response.json()


def _question_ids(session):
    return [q["id"] for q in session["current_section"]["questions"]]


def test_history_records_who_and_revert_restores_content(client, db, catalog):
    headers = _admin_headers(db)
    created = _new_question(client, headers, catalog["usmle"].id)
    qid = created["id"]

    edited = client.put(f"/api/questions/{qid}", headers=headers, json={
        "question_text": "Wrong text", "correct_answer": "B", "explanation": None, "tags": [],
    })
    assert edited.status_code == 200
    assert edited.json()["explanation"] is None and edited.json()["tags"] == []

    history = client.get(f"/api/questions/{qid}/history", headers=headers).json()
    assert [h["action"] for h in history] == ["updated", "created"]
    assert history[0]["changed_by_email"] == "admin@example.com"

    reverted = client.post(f"/api/questions/{qid}/revert/{history[1]['id']}", headers=headers).json()
    assert reverted["question_text"] == "Which nerve?"
    assert reverted["correct_answer"] == "A"
    assert reverted["explanation"] == "Because."
    assert reverted["tags"] == ["system:Musculoskeletal"]
    assert client.get(f"/api/questions/{qid}/history", headers=headers).json()[0]["action"] == "reverted"


def test_revert_rejects_revision_of_other_question(client, db, catalog):
    headers = _admin_headers(db)
    first = _new_question(client, headers, catalog["usmle"].id)
    second = _new_question(client, headers, catalog["usmle"].id)
    revision = client.get(f"/api/questions/{first['id']}/history", headers=headers).json()[0]
    assert client.post(f"/api/questions/{second['id']}/revert/{revision['id']}", headers=headers).status_code == 400


def test_delete_unused_question_is_permanent_but_history_remains(client, db, catalog):
    headers = _admin_headers(db)
    qid = _new_question(client, headers, catalog["usmle"].id)["id"]
    db.add(TestQuestionRow(test_id=catalog["test1"].id, question_id=qid, section_id=catalog["sat_math"].id,
                           question_order=99, section_question_order=99))
    db.commit()

    assert client.delete(f"/api/questions/{qid}", headers=headers).json() == {"result": "deleted"}
    assert client.get(f"/api/questions/{qid}", headers=headers).status_code == 404
    assert db.query(TestQuestionRow).filter(TestQuestionRow.question_id == qid).count() == 0
    assert client.get(f"/api/questions/{qid}/history", headers=headers).json()[0]["action"] == "deleted"


def test_delete_served_question_archives_and_only_affects_new_attempts(client, db, student, catalog):
    headers = _admin_headers(db)
    test = catalog["test1"]
    session = _start(client, student, catalog["package"], test)
    served = _question_ids(session)
    target = served[0]

    detail = client.get(f"/api/questions/{target}", headers=headers).json()
    assert detail["usage"]["attempt_count"] == 1
    assert detail["usage"]["tests"][0]["id"] == test.id

    assert client.delete(f"/api/questions/{target}", headers=headers).json() == {"result": "archived"}
    assert db.get(Question, target) is not None

    resumed = client.get(f"/api/tests/attempts/{session['attempt_id']}/session", headers=auth_headers(student)).json()
    assert _question_ids(resumed) == served

    other = User(email="other@example.com", is_active=True)
    db.add(other)
    db.commit()
    fresh = _start(client, other, catalog["package"], test)
    assert target not in _question_ids(fresh)
    assert len(_question_ids(fresh)) == len(served) - 1

    restored = client.post(f"/api/questions/{target}/restore", headers=headers).json()
    assert restored["is_active"] is True


def test_search_filters_and_counts(client, db, catalog):
    headers = _admin_headers(db)
    sat = catalog["sat"].id
    keep = _new_question(client, headers, sat, question_text="Solve for x in a linear equation", tags=["domain:Algebra"])
    _new_question(client, headers, sat, question_text="Area of a circle", tags=["domain:Geometry"])
    archived = _new_question(client, headers, sat, question_text="Old linear item")
    client.post(f"/api/questions/{archived['id']}/archive", headers=headers)

    def search(**params):
        return client.get("/api/questions/", headers=headers, params={"exam_id": sat, **params}).json()

    assert search(q="linear")["total"] == 1
    assert search(q="linear", status="all")["total"] == 2
    assert search(status="archived")["items"][0]["id"] == archived["id"]
    assert [i["id"] for i in search(tag="domain:Algebra")["items"]] == [keep["id"]]
    assert search(q=str(keep["id"]))["items"][0]["id"] == keep["id"]
    page = search(status="all", limit=1)
    assert page["total"] >= 3 and len(page["items"]) == 1


def test_export_round_trips_through_import(client, db, catalog):
    headers = _admin_headers(db)
    sat = catalog["sat"]
    _new_question(client, headers, sat.id, question_type="numeric_entry", answer_choices={},
                  correct_answer="3/4", accepted_answers=[".75"], tags=["domain:Algebra"])
    archived = _new_question(client, headers, sat.id, question_text="Retired")
    client.post(f"/api/questions/{archived['id']}/archive", headers=headers)

    export = client.get("/api/questions/export", headers=headers, params={"exam_id": sat.id})
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    before = client.get("/api/questions/", headers=headers, params={"exam_id": sat.id, "status": "all"}).json()["total"]

    upload = client.post(
        "/api/questions/upload-csv", headers=headers,
        files={"file": ("backup.csv", export.content, "text/csv")},
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["imported_count"] == before

    after = client.get("/api/questions/", headers=headers, params={"exam_id": sat.id, "status": "archived"}).json()
    assert after["total"] == 2
    imported = next(q for q in upload.json()["questions"] if q["tags"] == ["domain:Algebra"])
    assert imported["question_type"] == "numeric_entry" and imported["accepted_answers"] == [".75"]
    history = client.get(f"/api/questions/{imported['id']}/history", headers=headers).json()
    assert history[0]["action"] == "imported"


def test_question_bank_requires_admin(client, student, catalog):
    assert client.get("/api/questions/", headers=auth_headers(student)).status_code == 403
    assert client.get("/api/questions/export", headers=auth_headers(student)).status_code == 403
