"""
Task 2 — router accuracy test set. 20 varied queries with the expected intent, used to compute
a routing accuracy table.
"""

ROUTER_TEST_CASES = [
    {"id": "r_01", "query": "Who won the 2024 AFL Grand Final?", "expected": "retrieval"},
    {"id": "r_02", "query": "How many disposals did Patrick Dangerfield have last round?", "expected": "retrieval"},
    {"id": "r_03", "query": "What's Hawthorn's head-to-head record against Carlton?", "expected": "retrieval"},
    {"id": "r_04", "query": "List the players on Brisbane Lions' roster this season.", "expected": "retrieval"},
    {"id": "r_05", "query": "Who led the league in fantasy points in 2024?", "expected": "retrieval"},
    {"id": "r_06", "query": "What's a behind in AFL scoring?", "expected": "factual"},
    {"id": "r_07", "query": "When does the AFL finals series usually start?", "expected": "factual"},
    {"id": "r_08", "query": "Explain how the AFL draft works.", "expected": "factual"},
    {"id": "r_09", "query": "Will the Pies beat the Cats this week?", "expected": "prediction_match"},
    {"id": "r_10", "query": "What's Hawthorn's chance of beating Carlton?", "expected": "prediction_match"},
    {"id": "r_11", "query": "Who's going to win Geelong vs Richmond?", "expected": "prediction_match"},
    {"id": "r_12", "query": "Who'll top-score for Geelong this week?", "expected": "prediction_player"},
    {"id": "r_13", "query": "How many disposals will Dangerfield get next round?", "expected": "prediction_player"},
    {"id": "r_14", "query": "Which Hawthorn player is likely to have the best fantasy score this week?", "expected": "prediction_player"},
    {"id": "r_15", "query": "What's the weather like in Melbourne today?", "expected": "off_topic"},
    {"id": "r_16", "query": "Who won the last Super Bowl?", "expected": "off_topic"},
    {"id": "r_17", "query": "Write me a poem about the ocean.", "expected": "off_topic"},
    {"id": "r_18", "query": "What about last time?", "expected": "ambiguous"},  # no prior context established
    {"id": "r_19", "query": "Tell me about him.", "expected": "ambiguous"},
    {"id": "r_20", "query": "How did they go last season compared to this one?", "expected": "ambiguous"},
]
