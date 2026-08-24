## Task 1: Modern Voice Agent Architecture

### 1. Objective
Design a production-grade architecture for a real estate AI voice agent capable of handling phone calls, understanding customer intent, retrieving verified property information, using business tools, maintaining conversation context, and responding naturally in UrduLish.

### 2. Proposed Architecture

```text
                         CUSTOMER
                            │
                     Phone Call / Audio
                            │
                            ▼
                    ┌───────────────┐
                    │    TWILIO     │
                    │   Telephony   │
                    └───────┬───────┘
                            │ Audio
                            ▼
                    ┌───────────────┐
                    │   DEEPGRAM    │
                    │      STT      │
                    └───────┬───────┘
                            │ Transcript
                            ▼
                    ┌───────────────┐
                    │    FASTAPI    │
                    │ Backend Layer │
                    └───────┬───────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      LANGGRAPH      │
                 │   Agent Workflow    │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌────────────┐
        │  Memory  │  │   RAG    │  │   Tools    │
        └──────────┘  └──────────┘  └─────┬──────┘
                                           │
                              ┌────────────┼─────────────┐
                              ▼            ▼             ▼
                         PostgreSQL    Calendar       Email/CRM
                              │            │             │
                              └────────────┼─────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   GPT LLM    │
                                    │ Reasoning +  │
                                    │ Tool Calling │
                                    └───────┬──────┘
                                            │
                                       UrduLish Text
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │  FISH AUDIO  │
                                    │     TTS      │
                                    └───────┬──────┘
                                            │ Audio
                                            ▼
                                         TWILIO
                                            │
                                            ▼
                                         CUSTOMER
```

### 3. Speech-to-Text Pipeline

Twilio receives the customer's phone call and streams audio to the backend. Deepgram converts the audio into text in real time.

```text
Customer Speech
      ↓
Twilio Audio Stream
      ↓
Deepgram STT
      ↓
UrduLish Transcript
```

The STT component should handle Urdu, English, code-switching, Pakistani pronunciation, and real-time streaming.

### 4. LLM Reasoning

The transcript is passed to the LangGraph agent. The LLM determines:

1. Customer intent.
2. Required information.
3. Whether additional questions are required.
4. Whether RAG is required.
5. Whether a business tool should be called.
6. What response should be generated.

Example:

```text
Customer:
"Mujhe Bahria Town mein 2 crore tak house chahiye."

        ↓

Intent:
BUY_PROPERTY

        ↓

Extracted requirements:
Location = Bahria Town
Budget = 20,000,000
Property Type = House

        ↓

Property Search Tool

        ↓

Suitable Properties

        ↓

UrduLish Response
```

### 5. Retrieval-Augmented Generation

The RAG layer provides verified company knowledge such as:

- Property descriptions
- Company FAQs
- Sales policies
- Location information
- General company information

The retrieval pipeline is:

```text
Customer Question
       ↓
Query Processing
       ↓
Vector Search
       ↓
Relevant Documents
       ↓
Context
       ↓
LLM
       ↓
Grounded Response
```

Structured property information such as price, availability, area, and bedrooms should preferably be stored in PostgreSQL.

### 6. Memory

#### Short-Term Memory
Stores information during the current call:

- Current intent
- Current property
- Current requirements
- Conversation history
- Appointment details

#### Long-Term Memory
Stores information useful for future calls:

- Customer name
- Previous requirements
- Previous property interests
- Previous appointments
- Communication preferences

Example:

> "Assalam-o-Alaikum Ahmed sahib. Aap pichli dafa DHA mein property dekh rahe thay. Kya aap abhi bhi DHA mein hi search kar rahe hain?"

### 7. Tool Calling

The LLM should use controlled tools rather than directly performing business operations.

```text
search_properties()
get_property_details()
search_knowledge_base()

get_customer()
create_customer()
update_customer()

check_calendar_availability()
book_property_visit()
reschedule_appointment()
cancel_appointment()

send_email()
send_confirmation()

create_lead()
update_lead()

escalate_to_human()
```

### 8. Text-to-Speech

```text
LLM
 ↓
UrduLish Text
 ↓
Fish Audio
 ↓
Streaming Audio
 ↓
Twilio
 ↓
Customer
```

The TTS system should prioritize low latency, natural pronunciation, appropriate emotion, Urdu-English switching, natural pauses, and human-like speech.

### 9. Telephony

Twilio is responsible for:

- Receiving calls
- Maintaining call connections
- Streaming audio
- Returning generated audio
- Managing call termination

### 10. Workflow Orchestration

LangGraph manages the internal agent workflow, while n8n can automate external business processes.

```text
Appointment Booked
       ↓
Google Calendar
       ↓
n8n Workflow
       ↓
Send Email
       ↓
Update CRM
       ↓
Log Activity
```

### 11. Recommended Technology Stack

| Component | Technology |
|---|---|
| Telephony | Twilio |
| Speech-to-Text | Deepgram |
| LLM | OpenAI GPT |
| Agent Framework | LangGraph + LangChain |
| Vector Database | ChromaDB |
| Structured Database | PostgreSQL |
| TTS | Fish Audio |
| Backend | FastAPI |
| Workflow Automation | n8n |
| Scheduling | Google Calendar API |
| Email | Gmail API / Resend |
| Deployment | Docker + Railway/Render |

### 12. Final Architecture Flow

```text
CUSTOMER
   │
   ▼
TWILIO
   │
   ▼
DEEPGRAM STT
   │
   ▼
FASTAPI
   │
   ▼
LANGGRAPH AGENT
   │
   ├── MEMORY
   ├── RAG / CHROMADB
   ├── POSTGRESQL
   ├── PROPERTY SEARCH
   ├── GOOGLE CALENDAR
   ├── EMAIL
   └── CRM
   │
   ▼
GPT
   │
   ▼
URDULISH RESPONSE
   │
   ▼
FISH AUDIO TTS
   │
   ▼
TWILIO
   │
   ▼
CUSTOMER
```

### 13. Conclusion

The proposed architecture separates telephony, speech recognition, reasoning, retrieval, memory, business tools, scheduling, and speech synthesis into modular components. This makes the system easier to develop, test, scale, monitor, and deploy for an actual real estate client.
