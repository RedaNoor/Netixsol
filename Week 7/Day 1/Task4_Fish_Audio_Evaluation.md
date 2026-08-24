# Task 4: Fish Audio Evaluation

**Foundations of AI Voice Agents & Conversation Design**

## Context

Fish Audio is the recommended TTS provider for this project, with ElevenLabs as the comparison point. The choice of TTS provider affects both call quality and unit economics at scale, so it needs a real evaluation rather than a default pick.

## Objective

Evaluate Fish Audio against ElevenLabs on:

- Latency
- Naturalness
- Emotion
- Streaming
- Voice cloning
- Pricing
- Multilingual support
- Urdu pronunciation
- Urdu-English switching

## Deliverable

A conclusion on whether Fish Audio is the better choice for this use case, with reasoning tied directly to the comparison criteria above. Not a general recommendation, but one grounded in what this specific agent needs (Urdu-English code-switching, phone-call latency budget, per-minute cost at call volume).

## Notes for implementation

- Latency and streaming support matter more here than in most TTS use cases, since phone calls have almost no tolerance for dead air; a provider that scores well on naturalness but poorly on streaming latency may still be the wrong choice for this project.
- Urdu-English switching is the make-or-break criterion given the UrduLish persona requirement, a provider that handles each language well in isolation but mispronounces code-switched sentences will undermine the persona work from Task 3 regardless of how good it sounds otherwise.
- Pricing should be evaluated at expected call volume (dozens of calls/day, ongoing), not per-character list price alone, since the cost profile changes at scale.
