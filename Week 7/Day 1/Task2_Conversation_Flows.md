# Task 2 — Design Conversation Flows

**Week 7 Capstone — Day 1: Foundations of AI Voice Agents & Conversation Design**

## Context

A phone agent has to interrupt naturally, respond with low latency, recover gracefully from mis-hearings, sound empathetic, and steer the conversation toward booking a visit. That behavior needs to be mapped out as explicit flows before implementation, not improvised at the prompt level.

## Objective

Design complete conversation flows, as flowcharts, for each of the following scenarios:

- Buyer inquiry
- Rental inquiry
- Commercial property inquiry
- Investment inquiry
- Returning customer
- Appointment rescheduling
- Appointment cancellation

## Deliverable

One flowchart per scenario, covering the branch points that actually matter for a sales call: how the agent identifies intent early, what qualifying questions it asks before recommending a property, how it handles a caller who doesn't have clear requirements yet, and where the conversation exits toward a booked visit vs a follow-up email vs an escalation to a human agent.

## Notes for implementation

- Buyer, rental, commercial, and investment inquiries share a common qualification structure (budget, location, timeline, property type) but diverge on what "success" looks like at the end of the call — worth building one shared sub-flow for qualification and branching only where the paths actually differ.
- Returning customer flow needs a lookup step against stored history before the agent responds, so the persona can reference prior context ("last time we spoke about...") instead of restarting the conversation cold.
- Rescheduling and cancellation are both modification flows against an existing booking — they should share the lookup/confirm structure and differ only in the final action (calendar update vs calendar delete + confirmation).
