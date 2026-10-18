from app.models.models import Exam, Question, User
from tests.conftest import auth_headers


def _admin(db):
    admin = User(email="admin@example.com", is_active=True, is_admin=True)
    db.add(admin)
    db.commit()
    return auth_headers(admin)


def test_create_numeric_question_with_tags(client, db):
    headers = _admin(db)
    exam = Exam(slug="sat", name="SAT", tools=[])
    db.add(exam)
    db.commit()

    response = client.post("/api/questions/", headers=headers, json={
        "exam_id": exam.id,
        "question_type": "numeric_entry",
        "question_text": "What is 3 divided by 4?",
        "correct_answer": "3/4",
        "accepted_answers": [".75"],
        "tags": ["domain:Algebra", "skill:Linear equations"],
    })
    assert response.status_code == 201, response.text
    question = db.get(Question, response.json()["id"])
    assert sorted(f"{t.category}:{t.name}" for t in question.tags) == ["domain:Algebra", "skill:Linear equations"]


def test_numeric_question_rejects_choices_and_bad_answers(client, db):
    headers = _admin(db)
    base = {"question_type": "numeric_entry", "question_text": "Q"}
    assert client.post("/api/questions/", headers=headers, json={
        **base, "correct_answer": "3/4", "answer_choices": {"A": "x", "B": "y"},
    }).status_code == 422
    assert client.post("/api/questions/", headers=headers, json={**base, "correct_answer": "three"}).status_code == 422


def test_multiple_choice_allows_up_to_ten_options(client, db):
    headers = _admin(db)
    choices = {chr(ord("A") + i): f"option {i}" for i in range(10)}
    response = client.post("/api/questions/", headers=headers, json={
        "question_text": "USMLE-style", "answer_choices": choices, "correct_answer": "J",
    })
    assert response.status_code == 201, response.text


def test_update_revalidates_answer_fields(client, db):
    headers = _admin(db)
    created = client.post("/api/questions/", headers=headers, json={
        "question_text": "Q", "answer_choices": {"A": "a", "B": "b"}, "correct_answer": "A",
    }).json()
    bad = client.put(f"/api/questions/{created['id']}", headers=headers, json={"correct_answer": "C"})
    assert bad.status_code == 400
    switched = client.put(f"/api/questions/{created['id']}", headers=headers, json={
        "question_type": "numeric_entry", "correct_answer": "12",
    })
    assert switched.status_code == 200, switched.text
    assert switched.json()["answer_choices"] == {}


def test_csv_import_supports_exam_types_and_tags(client, db):
    headers = _admin(db)
    db.add(Exam(slug="usmle-step-1", name="USMLE Step 1", tools=[]))
    db.commit()
    csv_text = (
        "exam,question_type,question_text,choice_a,choice_b,correct_answer,accepted_answers,tags\n"
        "usmle-step-1,multiple_choice,Which drug?,Aspirin,Heparin,B,,system:Cardiovascular;discipline:Pharmacology\n"
        "usmle-step-1,numeric_entry,Calculate,,,1/2,.5,\n"
        "unknown-exam,multiple_choice,Bad,x,y,A,,\n"
    )
    response = client.post(
        "/api/questions/upload-csv", headers=headers,
        files={"file": ("questions.csv", csv_text, "text/csv")},
    )
    assert response.status_code == 422
    assert response.json()["errors"] == [{"row": 4, "message": "Unknown exam 'unknown-exam'", "column": "exam"}]

    response = client.post(
        "/api/questions/upload-csv", headers=headers,
        files={"file": ("questions.csv", "\n".join(csv_text.splitlines()[:3]), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["imported_count"] == 2
