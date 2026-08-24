# Task 3 — UrduLish Persona Engineering

**Week 7 Capstone — Day 1: Foundations of AI Voice Agents & Conversation Design**

## Context

The agent needs to sound like a real Pakistani sales rep speaking natural UrduLish, not a text response translated word-for-word into Urdu. Direct translation is the main failure mode to avoid here — it reads as robotic and breaks the human-like effect the whole project depends on.

## Objective

Design the agent's personality so it reads as:

- Pakistani
- Professional
- Warm
- Persuasive
- Patient

Example greeting:

```
"Assalam-o-Alaikum sir! RealEstate Hub se baat ho rahi hai. Main aap ki kis tarah madad kar sakta hoon?"
```

## Deliverable

A distinct set of phrases for each of the following categories — not one generic line reused everywhere, since real conversation varies its phrasing by context and repeating the same line across every call is one of the more obvious tells of a scripted bot:

- Greeting
- Confirmations
- Hesitation phrases
- Acknowledgement phrases
- Objection handling

## Notes for implementation

- Avoid direct English-to-Urdu translation; write each phrase the way a Pakistani salesperson would actually say it, code-switching naturally rather than translating a fixed English template.
- Hesitation phrases matter more than they seem — filler like "hmm," "acha," "bas ek second" fills the latency gap while the LLM is generating a response, and its absence is one of the fastest ways a caller identifies they're talking to a bot.
- Objection handling phrases should be tied to the specific objections real estate calls actually get (price too high, wrong location, not ready to commit) rather than generic reassurance lines.
