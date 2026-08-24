"""
Task 5 — 10 full conversations exercising every path through the graph: factual, retrieval,
prediction (match + player), off-topic refusal, ambiguous input requiring clarification, and
multi-turn follow-ups.

trace: True marks the conversations selected for detailed annotated state-trace logging
(Task 5 asks for 2-3) — chosen to cover the most structurally interesting paths: a straight
retrieval, a prediction with entity resolution, and a clarification loop.
"""

CONVERSATIONS = [
    {
        "id": "e2e_01", "path": "factual",
        "trace": False,
        "turns": ["What's a behind in AFL scoring?"],
    },
    {
        "id": "e2e_02", "path": "retrieval",
        "trace": True,
        "turns": ["How many disposals did Patrick Dangerfield have in his last game?"],
    },
    {
        "id": "e2e_03", "path": "prediction_match",
        "trace": True,
        "turns": ["Will the Pies beat the Cats this week?"],
    },
    {
        "id": "e2e_04", "path": "prediction_player",
        "trace": False,
        "turns": ["Who'll top-score for Geelong this week?"],
    },
    {
        "id": "e2e_05", "path": "off_topic",
        "trace": False,
        "turns": ["What's the weather like in Melbourne today?"],
    },
    {
        "id": "e2e_06", "path": "ambiguous_then_clarify",
        "trace": True,
        "turns": [
            "Tell me about him.",                      # no prior context -> should ask for clarification
            "I mean Patrick Dangerfield.",              # resolves the ambiguity
        ],
    },
    {
        "id": "e2e_07", "path": "multiturn_followup",
        "trace": False,
        "turns": [
            "Tell me about Hawthorn's 2024 season.",
            "Who had the best fantasy output for them that year?",
            "What's his career average by comparison?",
        ],
    },
    {
        "id": "e2e_08", "path": "unresolvable_team_then_clarify",
        "trace": False,
        "turns": [
            "Will Hawthorn beat Man United?",           # not an AFL team -> clarification
            "Sorry, I meant Carlton.",
        ],
    },
    {
        "id": "e2e_09", "path": "mixed_session",
        "trace": False,
        "turns": [
            "What's Hawthorn's head-to-head record against Carlton?",
            "What's their chance of beating them next time?",
            "What's a Grand Final?",
        ],
    },
    {
        "id": "e2e_10", "path": "off_topic_then_redirect",
        "trace": False,
        "turns": [
            "Who won the last Super Bowl?",
            "Okay fine — who won the 2024 AFL Grand Final instead?",
        ],
    },
]
