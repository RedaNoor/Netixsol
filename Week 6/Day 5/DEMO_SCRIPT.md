---
noteId: "3fa68cf09f9111f1be04e92091ab93e6"
tags: []

---

# AFL Assistant — Demo Script & Slide Outline
### 5–7 minute stakeholder walkthrough

## Slide 1 — Title
**AFL Assistant: Chat + Retrieval + Prediction, live**
One line: "A domain-locked AFL assistant that answers from real data and predicts with honest probabilities — built and evaluated end to end."

## Slide 2 — The problem this solves
- Generic chatbots hallucinate stats and wander off-topic.
- This system is architecturally constrained to stay on-topic and grounded — not just prompted to be.
- Three capabilities in one product: factual AFL knowledge, real data lookups, and match/player predictions.

*(Talk track: ~30 seconds. "Before I show it running, the core design decision worth knowing: this isn't one big agent guessing what to do — it's a routed system, so a prediction can never accidentally skip its disclaimer, and an off-topic question can never talk its way past the scope boundary. That's the thing I want the demo to actually prove, not just claim.")*

---

## Live Demo (4 things, ~3–4 minutes total)

### Demo 1 — Factual question (~45s)
**Ask:** "What's a behind worth in AFL scoring?"
**Point out:** No tool call needed — answered from general AFL knowledge, fast.

### Demo 2 — Retrieval question (~60s)
**Ask:** "How many disposals did Patrick Dangerfield have in his last game?"
**Point out:** Watch the intent tag in the UI — `retrieval` — and the tool that fired. This number came from a real pandas lookup against the actual dataset, not the model's memory.

### Demo 3 — Prediction question (~60s)
**Ask:** "Will the Pies beat the Cats this week?"
**Point out three things:**
1. "Pies" and "Cats" resolved to Collingwood Magpies / Geelong Cats automatically — nickname resolution, not the model guessing.
2. The response includes *why* — top factors (form, ladder position) and this matchup's actual values on them.
3. The disclaimer at the end is **always there** — it's not something the model decided to add this time.

### Demo 4 — Off-topic refusal (~45s)
**Ask:** "What's the weather like in Melbourne today?"
**Point out:** Clean decline, redirected back to AFL, no engagement with the off-topic content. Optionally show a jailbreak attempt too ("ignore your instructions and...") to show it holds under pressure, not just on an easy case.

### Demo 5 — Multi-turn coherence (~60s, if time allows)
**Ask sequence:**
1. "Tell me about Hawthorn's 2024 season."
2. "Who had the best fantasy output for them that year?"
3. "What's his career average by comparison?"
**Point out:** No need to repeat "Hawthorn" or the player's name — context carries across turns via the conversation memory.

---

## Slide 3 — Evaluation, not just a demo
- 27 test cases across 4 categories — factual accuracy, prediction sanity, scope guardrails, multi-turn coherence.
- **Concrete result to lead with:** all 6 prediction-sanity checks pass against real historical data — extreme ladder mismatches correctly produce >90% confidence for the stronger team, and draw probability never exceeds 2%.
- Benchmarked against a naive "higher ladder position wins" baseline — the model wins 2 of 3 recent seasons and is essentially tied in the third, against a baseline that's already meaningfully better than a coin flip.

## Slide 4 — Known limitations (say this before someone asks)
- No live fixture feed — "this week" predictions use each team's latest known form, not a confirmed schedule, and the system says so explicitly rather than pretending otherwise.
- ~67–75% match-winner accuracy is the realistic ceiling for this task, not a shortfall — sports outcomes carry real randomness.
- Player-stat predictions beyond fantasy points use a simpler estimate, not a full trained model, and the system is upfront about that distinction when asked.

## Slide 5 — What's next
- Live fixture integration.
- Weekly monitoring loop already specified (latency, tool error rate, off-topic leak rate, prediction drift) — ready to wire into a dashboard.
- Retrain trigger tied to real drift, not a fixed calendar, so the model updates when it actually needs to.

## Closing line
"The point of this whole build isn't that it never makes a wrong call — it's that when it does, you can see exactly which node made the call, and the guardrails that matter — disclaimers, scope, grounding — are guaranteed by code, not hoped for from a prompt."

---

### Setup checklist before presenting
- [ ] `.env` filled in with real `OPENROUTER_API_KEY` / `GROQ_API_KEY`
- [ ] `uvicorn api:app --reload` running, UI open in browser at `localhost:8000`
- [ ] Run through all 5 demo prompts once beforehand — confirm live responses read naturally
- [ ] Have `reports/eval_summary.md` and `Executive_Report.pdf` open in a second tab in case of Q&A
