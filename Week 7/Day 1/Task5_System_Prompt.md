# Task 5 — System Prompt

**Week 7 Capstone — Day 1: Foundations of AI Voice Agents & Conversation Design**

## Context

Everything designed in Tasks 1–4 (architecture, conversation flows, persona, voice) needs to be codified into a single production system prompt that governs the agent's behavior on every call. This is where the design work actually becomes enforceable rather than aspirational.

## Objective

Design a production-grade system prompt defining:

- Scope
- Goals
- Guardrails
- Persuasion rules
- Appointment booking policy
- Escalation rules

## Deliverable

A complete system prompt, structured so each of the six areas above is unambiguous and testable against a real call transcript.

## Notes for implementation

- Scope should explicitly state what the agent must not do (legal/financial advice beyond general property info, price negotiation authority, commitments the company hasn't authorized) since undefined scope is where a persuasive sales persona is most likely to overstep.
- Guardrails need to cover both content (no false claims about a property) and behavior (no pressuring a hesitant caller past the point of discomfort) — persuasive tone from Task 3 and guardrails against overreach are in tension and the prompt needs to resolve that explicitly, not leave it implicit.
- Appointment booking policy should define what counts as a valid booking (confirmed date, time, contact info) before the agent is allowed to call the calendar tool, to avoid partial or malformed bookings.
- Escalation rules need concrete triggers (caller asks for a human, caller is angry, request falls outside scope) rather than a vague "escalate when appropriate," since that's the line that determines whether the system fails gracefully or badly on edge cases.
