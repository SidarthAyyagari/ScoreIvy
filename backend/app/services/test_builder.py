"""Assemble a full-length test from the question bank.

Each part (USMLE block, SAT module) draws its questions from active questions of the exam,
optionally limited to some subject sections, split across those sections in proportion to how
many questions each has available. By default questions already used in any test are skipped,
so a student who buys several tests never sees a repeat.
"""

import random
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import Package, PackageTest, Question, Section, Test, TestQuestion, TestSection
from app.schemas.admin_schemas import BuildPartResult, BuildTestRequest, BuildTestResult


class BuildError(ValueError):
    pass


def question_pool(db: Session, exam_id: int, exclude_used: bool) -> List[Question]:
    query = db.query(Question).filter(Question.exam_id == exam_id, Question.is_active == True)  # noqa: E712
    if exclude_used:
        used = db.query(TestQuestion.question_id)
        query = query.filter(~Question.id.in_(used))
    return query.order_by(Question.id).all()


def _allocate(groups: Dict[Optional[int], List[Question]], count: int) -> Dict[Optional[int], int]:
    """Split ``count`` across groups in proportion to their size (largest remainder)."""
    total = sum(len(g) for g in groups.values())
    shares = {key: count * len(g) / total for key, g in groups.items()}
    allocation = {key: int(share) for key, share in shares.items()}
    leftover = count - sum(allocation.values())
    for key in sorted(shares, key=lambda k: shares[k] - allocation[k], reverse=True)[:leftover]:
        allocation[key] += 1
    return allocation


def build_test(db: Session, request: BuildTestRequest) -> BuildTestResult:
    """Pick questions for every part; with ``dry_run`` only report what would be built. Caller commits."""
    rng = random.Random(request.seed)
    pool = question_pool(db, request.exam_id, request.exclude_used)
    section_names = {s.id: s.name for s in db.query(Section).filter(Section.exam_id == request.exam_id)}
    remaining = list(pool)
    chosen_parts: List[List[Question]] = []
    results: List[BuildPartResult] = []
    shortfalls: List[str] = []

    for part in request.parts:
        allowed = set(part.section_ids or [])
        candidates = [q for q in remaining if not allowed or q.section_id in allowed]
        if len(candidates) < part.question_count:
            shortfalls.append(
                f"{part.name} needs {part.question_count} questions but only {len(candidates)} are available"
            )
            chosen: List[Question] = []
        else:
            groups: Dict[Optional[int], List[Question]] = {}
            for question in candidates:
                groups.setdefault(question.section_id, []).append(question)
            chosen = []
            for key, take in _allocate(groups, part.question_count).items():
                chosen.extend(rng.sample(groups[key], take))
            rng.shuffle(chosen)
            taken = {q.id for q in chosen}
            remaining = [q for q in remaining if q.id not in taken]
        chosen_parts.append(chosen)

        by_section: Dict[str, int] = {}
        for question in chosen:
            label = section_names.get(question.section_id, "No section")
            by_section[label] = by_section.get(label, 0) + 1
        results.append(BuildPartResult(
            name=part.name,
            question_count=len(chosen),
            time_limit_minutes=part.time_limit_minutes,
            available=len(candidates),
            by_section=by_section,
        ))

    result = BuildTestResult(
        test_id=None,
        parts=results,
        pool_size=len(pool),
        pool_remaining=len(remaining),
        problems=shortfalls,
    )
    if request.dry_run or shortfalls:
        if shortfalls and not request.dry_run:
            raise BuildError("; ".join(shortfalls))
        return result

    package = db.get(Package, request.package_id) if request.package_id else None
    if request.package_id and package is None:
        raise BuildError(f"Package {request.package_id} not found")

    test = Test(
        exam_id=request.exam_id,
        name=request.name,
        description=request.description,
        time_limit_minutes=sum(p.time_limit_minutes for p in request.parts),
        question_count=sum(len(c) for c in chosen_parts),
        break_pool_minutes=request.break_pool_minutes,
        scoring=request.scoring,
        is_active=True,
    )
    db.add(test)
    db.flush()

    order = 0
    for index, (part, chosen) in enumerate(zip(request.parts, chosen_parts), start=1):
        subjects = set(part.section_ids or [])
        test_section = TestSection(
            test_id=test.id,
            section_id=next(iter(subjects)) if len(subjects) == 1 else None,
            section_order=index,
            question_count=len(chosen),
            name=part.name,
            time_limit_minutes=part.time_limit_minutes,
            break_after_minutes=part.break_after_minutes,
        )
        db.add(test_section)
        db.flush()
        for position, question in enumerate(chosen, start=1):
            order += 1
            db.add(TestQuestion(
                test_id=test.id,
                question_id=question.id,
                section_id=question.section_id,
                test_section_id=test_section.id,
                question_order=order,
                section_question_order=position,
            ))

    if package is not None:
        last = max((pt.test_order for pt in package.package_tests), default=0)
        db.add(PackageTest(package_id=package.id, test_id=test.id, test_order=last + 1))

    db.flush()
    result.test_id = test.id
    return result
