## Task 4: Fish Audio Evaluation

### 1. Objective

Evaluate Fish Audio as the primary text-to-speech solution for the real estate AI voice agent and compare it with ElevenLabs.

The evaluation focuses on:

- Latency
- Naturalness
- Emotion
- Streaming
- Voice cloning
- Pricing
- Multilingual support
- Urdu pronunciation
- Urdu-English switching

---

## 2. Fish Audio

Fish Audio provides text-to-speech capabilities with realtime streaming support and multilingual/expressive speech models.

For a production voice agent, the most important characteristics are:

- Low time-to-first-audio
- Streaming generation
- Natural speech
- Expressive delivery
- Voice customization
- Multilingual capability
- Reasonable operating cost

Fish Audio's current developer documentation provides REST and realtime WebSocket TTS interfaces.

---

## 3. ElevenLabs

ElevenLabs provides:

- Text-to-speech
- Low-latency speech models
- Realtime conversational capabilities
- Voice cloning
- Multilingual speech
- Speech-to-text services

ElevenLabs is a strong alternative and should be retained as a benchmark or fallback.

---

## 4. Comparison

| Criterion | Fish Audio | ElevenLabs | Project Assessment |
|---|---|---|---|
| Latency | Excellent | Excellent | Fish preferred for testing |
| Naturalness | Excellent | Excellent | Tie |
| Emotion | Strong | Very strong | ElevenLabs |
| Streaming | Yes | Yes | Tie |
| Voice cloning | Yes | Yes | Tie |
| Multilingual support | Very strong | Very strong | Fish |
| Urdu pronunciation | Requires testing | Requires testing | Experimental |
| Urdu-English switching | Requires testing | Requires testing | Experimental |
| Pricing | Competitive | Higher depending on model | Fish |
| Realtime suitability | Excellent | Excellent | Tie |
| Student project cost | Attractive | More expensive depending on usage | Fish |

---

## 5. UrduLish Testing

Because the project specifically requires Pakistani UrduLish, published language counts should not be treated as proof of Urdu quality.

Both engines should be tested using the same sentences.

### Test Sentence 1

> "Assalam-o-Alaikum sir, aap kis area mein property search kar rahe hain?"

### Test Sentence 2

> "Aap ka budget approximately kitna hai?"

### Test Sentence 3

> "Ji sir, main aap ke liye available properties check karti hoon."

### Test Sentence 4

> "DHA mein ek five marla house available hai, jo aap ke budget ke kaafi close hai."

### Test Sentence 5

> "Agar aap chahein to main kal afternoon mein property visit schedule kar sakti hoon."

---

## 6. Evaluation Method

Each sample should receive a score from 1 to 5.

| Metric | Score |
|---|---:|
| Urdu pronunciation | /5 |
| English pronunciation | /5 |
| Urdu-English switching | /5 |
| Naturalness | /5 |
| Emotion | /5 |
| Speaking speed | /5 |
| Pausing | /5 |
| Voice clarity | /5 |
| Overall quality | /5 |

The same test set should be used for both TTS systems to make the comparison fair.

---

## 7. Latency Evaluation

For a voice agent, end-to-end latency is more important than raw TTS generation speed.

The system should measure:

```text
User stops speaking
        ↓
STT final transcript
        ↓
LLM response generation
        ↓
TTS first audio
        ↓
Customer hears response
```

The key metric is:

**Time-to-First-Audio (TTFA)**

The lower the TTFA, the more responsive the voice agent feels.

---

## 8. Naturalness Evaluation

The following should be assessed:

- Human-like rhythm
- Natural pauses
- Sentence stress
- Pronunciation
- Emotion
- Speaking speed
- Absence of robotic patterns

---

## 9. Urdu-English Switching

A key test is whether the voice can naturally switch between Urdu and English.

Example:

> "Ji sir, aap ki requirement ke according main DHA mein available properties check kar leti hoon."

The system should not pronounce English words unnaturally or create noticeable breaks when switching languages.

---

## 10. Voice Cloning

Voice cloning can be useful for maintaining a consistent company representative persona.

However:

- Only authorized voices should be cloned.
- Consent should be obtained.
- The system should not impersonate unauthorized individuals.
- A production deployment should document voice ownership and permissions.

---

## 11. Recommended Choice

### Primary TTS: Fish Audio

Fish Audio is recommended as the primary TTS engine for this project because it aligns well with the project's requirements for realtime streaming, multilingual speech, expressive generation, and cost-conscious deployment.

### Secondary / Benchmark: ElevenLabs

ElevenLabs should be retained as a comparison benchmark and possible fallback because of its strong speech quality, voice ecosystem, realtime capabilities, and mature platform.

### Important Experimental Requirement

The final selection should be validated using actual UrduLish audio tests. Language support claims alone are not sufficient to establish that a TTS system produces high-quality Pakistani UrduLish.

---

## 12. Final Evaluation Conclusion

**Selected primary engine: Fish Audio**

**Benchmark/fallback: ElevenLabs**

The final production decision should consider measured TTFA, Urdu pronunciation, Urdu-English switching, naturalness, emotional quality, reliability, and total cost under realistic call volume.
