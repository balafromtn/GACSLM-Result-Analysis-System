"""
test_hybrid_engine.py — Comprehensive test suite for the Generic Hybrid Academic Data Intelligence Engine.
"""

import sys
import os
import asyncio

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from intelligence.schema import AcademicSchema
from intelligence.engine import AcademicQueryEngine, QueryPlan, FilterCondition
from intelligence.planner import QueryPlanner
from intelligence.memory import ConversationMemory
from intelligence.dispatcher import HybridIntelligenceDispatcher


def build_mock_dataset():
    """Create a realistic academic dataset with 8 students, ties, absent students, arrears, and multiple subjects."""
    return [
        {
            "name": "BALAJI M",
            "register_no": "24UCS250904",
            "gender": "Male",
            "community": "BC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "90", "result": "PASS"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "80", "result": "PASS"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "85", "result": "PASS"},
                {"semester": "II", "code": "23UCS03", "title": "C++ Programming", "total": "60", "result": "PASS"},
            ]
        },
        {
            "name": "PRIYA S",
            "register_no": "24UCS250915",
            "gender": "Female",
            "community": "MBC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "95", "result": "PASS"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "80", "result": "PASS"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "80", "result": "PASS"},
            ]
        },
        {
            "name": "KAVIN R",
            "register_no": "24UCS250908",
            "gender": "Male",
            "community": "BC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "90", "result": "PASS"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "80", "result": "PASS"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "85", "result": "PASS"},
            ]
        },
        {
            "name": "SNEHA K",
            "register_no": "24UCS250920",
            "gender": "Female",
            "community": "SC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "45", "result": "PASS"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "28", "result": "RA"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "50", "result": "PASS"},
            ]
        },
        {
            "name": "DINESH V",
            "register_no": "24UCS250905",
            "gender": "Male",
            "community": "MBC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "32", "result": "RA"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "20", "result": "RA"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "35", "result": "RA"},
            ]
        },
        {
            "name": "ANITHA M",
            "register_no": "24UCS250902",
            "gender": "Female",
            "community": "BC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "65", "result": "PASS"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "55", "result": "PASS"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "70", "result": "PASS"},
            ]
        },
        {
            "name": "PRAVEEN S",
            "register_no": "24UCS250914",
            "gender": "Male",
            "community": "SC",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "AA", "result": "ABSENT"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "42", "result": "PASS"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "58", "result": "PASS"},
            ]
        },
        {
            "name": "VIKRAM T",
            "register_no": "24UCS250925",
            "gender": "Male",
            "community": "ST",
            "degree_branch": "B.Sc. - Computer Science",
            "exam_month_year": "APR 2026",
            "subjects": [
                {"semester": "IV", "code": "23UCS07", "title": "Java Programming", "total": "AA", "result": "ABSENT"},
                {"semester": "IV", "code": "23ASTM2", "title": "Mathematical Statistics - II", "total": "AA", "result": "ABSENT"},
                {"semester": "IV", "code": "23FEL04", "title": "Foundation English - IV", "total": "AA", "result": "ABSENT"},
            ]
        }
    ]


async def run_tests():
    dataset = build_mock_dataset()
    print("=== 1. Testing Schema Discovery ===")
    schema = AcademicSchema(dataset)
    meta = schema.to_metadata_dict()
    print(f"Degree: {meta['degree_branch']}, Semester: {meta['current_semester']}")
    print(f"Core Subjects: {[s['code'] for s in meta['core_subjects']]}")
    print(f"Arrear Subjects: {[s['code'] for s in meta['arrear_subjects']]}")
    assert "23UCS07" in schema.core_subjects
    assert "23UCS03" in schema.arrear_subjects
    assert schema.resolve_subject("java") == "23UCS07"
    assert schema.resolve_subject("statistics") == "23ASTM2"
    print("Schema discovery: PASS\n")

    print("=== 2. Testing Query Engine (Deterministic Python) ===")
    engine = AcademicQueryEngine(dataset)
    assert len(engine.students) == 8

    # Test 2.1: Tied Topper Handling
    # BALAJI M (90+80+85 = 255) and KAVIN R (90+80+85 = 255) and PRIYA S (95+80+80 = 255) are ALL TIED for Rank 1 with 255 marks!
    plan_topper = QueryPlan(operation="ranking", limit=1, meta={"topper_only": True})
    res_topper = engine.execute(plan_topper)
    print("Topper Result Summary:\n" + res_topper.summary_markdown)
    assert len(res_topper.data) == 3  # Balaji, Priya, Kavin all tied at 255
    assert res_topper.data[0]["total"] == 255
    print("Tied Topper Test: PASS\n")

    # Test 2.2: Subject Topper
    plan_subj_topper = QueryPlan(operation="ranking", subject_code="23UCS07")
    res_subj_topper = engine.execute(plan_subj_topper)
    print("Subject Topper (Java):\n" + res_subj_topper.summary_markdown)
    assert res_subj_topper.data[0]["name"] == "PRIYA S"
    assert res_subj_topper.data[0]["subject_score"] == 95
    print("Subject Topper Test: PASS\n")

    # Test 2.3: Female Topper (Filter + Ranking)
    plan_f_topper = QueryPlan(
        operation="ranking",
        filters=[FilterCondition(field="gender", op="==", val="Female")],
        limit=1,
        meta={"topper_only": True}
    )
    res_f_topper = engine.execute(plan_f_topper)
    print("Female Topper:\n" + res_f_topper.summary_markdown)
    assert res_f_topper.data[0]["name"] == "PRIYA S"
    print("Female Topper Test: PASS\n")

    # Test 2.4: Overall Aggregation (Pass %, Counts)
    plan_agg = QueryPlan(operation="aggregation")
    res_agg = engine.execute(plan_agg)
    print("Class Aggregation:\n" + res_agg.summary_markdown)
    # Total enrolled: 8. Fully absent: 1 (VIKRAM T). Appeared: 7.
    # Passed all core: BALAJI M, PRIYA S, KAVIN R, ANITHA M = 4 passed out of 7 appeared = 57.14%
    assert res_agg.data["total_students"] == 8
    assert res_agg.data["appeared_students"] == 7
    assert res_agg.data["passed_students"] == 4
    assert res_agg.data["pass_percentage"] == 57.14
    print("Overall Aggregation Test: PASS\n")

    # Test 2.5: Multi-condition / Conditional Analysis (Failing in > 2 subjects)
    plan_cond = QueryPlan(
        operation="conditional",
        filters=[FilterCondition(field="failed_core_count", op=">=", val=3)]
    )
    res_cond = engine.execute(plan_cond)
    print("Failing in >= 3 subjects:\n" + res_cond.summary_markdown)
    assert len(res_cond.data) == 1
    assert res_cond.data[0]["name"] == "DINESH V"
    print("Conditional Filter Test: PASS\n")

    # Test 2.6: Gender Comparison
    plan_cmp = QueryPlan(operation="comparison", target="gender")
    res_cmp = engine.execute(plan_cmp)
    print("Gender Comparison:\n" + res_cmp.summary_markdown)
    assert "male" in res_cmp.data and "female" in res_cmp.data
    print("Gender Comparison Test: PASS\n")

    # Test 2.7: Performance Distribution Bands
    plan_dist = QueryPlan(operation="distribution")
    res_dist = engine.execute(plan_dist)
    print("Distribution Bands:\n" + res_dist.summary_markdown)
    assert "Distinction (>= 75%)" in res_dist.data
    print("Distribution Test: PASS\n")

    # Test 2.8: Semester & Backlog Comparison
    plan_sem = QueryPlan(operation="semester_comparison")
    res_sem = engine.execute(plan_sem)
    print("Semester Comparison:\n" + res_sem.summary_markdown)
    assert res_sem.data["students_with_arrears"] == 1  # Balaji M has 23UCS03
    print("Semester Comparison Test: PASS\n")

    print("=== 3. Testing Conversation Memory & Follow-up Resolution ===")
    memory = ConversationMemory()
    planner = QueryPlanner()

    # Step 1: User asks topper
    q1 = "Who is the class topper?"
    plan1, is_dir1, intent1 = planner.plan_query(q1, schema, memory)
    res1 = engine.execute(plan1)
    memory.record_turn(q1, res1.summary_markdown, query_type=intent1)
    print(f"Q1: '{q1}' -> Planned: {intent1}, DirectPath: {is_dir1}")

    # Step 2: Follow-up "What about the girls?"
    q2 = "What about the girls?"
    resolved_q2, hints2 = memory.resolve_follow_up(q2, schema)
    print(f"Q2: '{q2}' -> Resolved: '{resolved_q2}', Hints: {hints2}")
    plan2, is_dir2, intent2 = planner.plan_query(q2, schema, memory)
    res2 = engine.execute(plan2)
    print("Resolved Q2 Result:\n" + res2.summary_markdown)
    assert any(f.field == "gender" and f.val == "Female" for f in plan2.filters)
    print("Memory follow-up resolution: PASS\n")

    print("=== 4. Testing Hybrid Dispatcher (Path A - Direct Execution) ===")
    dispatcher = HybridIntelligenceDispatcher(dataset, memory=memory)

    queries_to_test = [
        "Who is the class topper?",
        "What is the pass percentage?",
        "Who failed in more than 2 subjects?",
        "Who is the topper in Java?",
        "Tell me about BALAJI M",
        "Compare boys and girls performance",
        "Show performance distribution"
    ]

    for q in queries_to_test:
        out = await dispatcher.process_query(q)
        print(f"Query: '{q}'")
        print(f"  Path: {out['path']}, Latency: {out['latency_ms']['total']}ms, Tokens: {out['tokens_consumed']}")
        assert out["path"] == "path_a_direct"
        assert out["tokens_consumed"] == 0
        assert out["latency_ms"]["total"] < 50.0  # Should be virtually instantaneous!

    print("\nAll Direct Path A queries executed in < 50ms with 0 LLM tokens: PASS\n")

    print("=== 5. Testing Path B (Pedagogical / Recommendation routing) ===")
    out_b = await dispatcher.process_query("What are your recommendations to improve the pass percentage of this class?")
    print("Open-ended Query Path: " + out_b["path"])
    assert out_b["path"] == "path_b_llm"
    print("Path B routing: PASS\n")

    print("ALL TESTS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_tests())
