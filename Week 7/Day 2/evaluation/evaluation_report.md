---
noteId: "5d911b30a07311f195900762b9117099"
tags: []

---

# Day 2 — RAG & Hallucination Evaluation Report

## 1. Objective

Evaluate whether the property knowledge system retrieves verified evidence and prevents unsupported property claims.

## 2. Test Set

20 questions are provided in `test_questions.json`, covering:
- Exact prices
- Availability
- Bedrooms
- Sizes
- Developers
- Payment plans
- Amenities
- Schools
- Hospitals
- Family suitability
- Investment-oriented recommendations
- Safety/no-evidence behavior

## 3. Metrics

### Retrieval Accuracy

`Correctly retrieved relevant results / total retrieval queries`

### Grounding Rate

`Grounded claims / total generated claims`

### Hallucination Rate

`Unsupported claims / total generated claims`

## 4. Chunk Size Experiment

Run the RAG pipeline with:

| Experiment | Chunk Size | Overlap | Retrieval Accuracy | Grounding Rate | Hallucination Rate |
|---|---:|---:|---:|---:|---:|
| A | 250 | 50 | TBD | TBD | TBD |
| B | 500 | 100 | TBD | TBD | TBD |
| C | 750 | 150 | TBD | TBD | TBD |
| D | 1000 | 200 | TBD | TBD | TBD |

Populate the final three columns only after running the actual evaluation.

## 5. Target Thresholds

| Metric | Target |
|---|---:|
| Retrieval Accuracy | >= 90% |
| Grounding Rate | >= 95% |
| Hallucination Rate | <= 5% |

These are engineering targets, not measured results.

## 6. Grounding Policy

If verified evidence is not retrieved, the assistant must not invent a fact.

Recommended fallback:

> I don't have verified information about that in the company knowledge base. I can connect you with a sales representative to confirm it.

## 7. Structured vs Semantic Retrieval

SQL is used for exact numerical and categorical constraints such as price, availability, bedrooms, sizes and other structured attributes.

Vector retrieval is used for brochures, descriptions, developer profiles and FAQs where semantic similarity is useful.

For mixed queries, structured constraints should be applied first and semantic evidence should then enrich the candidate results.

## 8. Final Result

Record actual measured values here after running the evaluation.

- Retrieval Accuracy: TBD
- Grounding Rate: TBD
- Hallucination Rate: TBD
- Best Chunk Configuration: TBD
