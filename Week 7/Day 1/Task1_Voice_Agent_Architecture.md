# Task 1 — Research Modern Voice Agent Architecture

**Week 7 Capstone — Day 1: Foundations of AI Voice Agents & Conversation Design**

## Context

Before writing any code, the underlying architecture of a phone-based AI voice agent needs to be understood end to end. A voice agent is not a chatbot with audio bolted on — every stage in the pipeline has its own latency budget, failure modes, and design trade-offs that affect how natural the call feels to the person on the other end.

## Objective

Study and document each stage of the pipeline:

- Speech-to-Text
- LLM reasoning
- Tool calling
- Retrieval
- Memory
- Text-to-Speech
- Telephony
- Workflow orchestration

## Deliverable

An architecture diagram covering the full call flow end to end — from the moment a call connects through telephony, to STT transcription, LLM reasoning with tool calls and retrieval, memory read/write, TTS synthesis, and back out through telephony to the caller. The diagram should make the round-trip latency path visible, since that's the main constraint that shapes every other decision in this system.

## Notes for implementation

- Each stage in the pipeline adds latency; the diagram should be usable later to identify where latency can be cut (e.g. streaming STT/TTS instead of waiting for full utterances).
- Tool calling and retrieval both sit inside the LLM reasoning stage but have different failure modes (a failed tool call vs a bad retrieval match) — worth distinguishing them as separate blocks rather than collapsing them into one "LLM" box.
- Memory needs to cover both short-term (within-call context) and longer-term (returning customer history) — the diagram should show both paths since they likely hit different storage.
