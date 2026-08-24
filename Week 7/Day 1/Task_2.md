## Task 2: Conversation Flow Design

### 1. Objective

Design complete conversation flows for buyer, rental, commercial, investment, returning-customer, appointment-rescheduling, and appointment-cancellation scenarios.

The agent should behave like a professional real estate sales representative rather than a conventional chatbot.

---

## 2. Buyer Inquiry

```text
START
  ↓
Greeting
  ↓
Identify Intent
  ↓
Buyer?
  ↓
Collect Requirements
  ↓
Location + Budget + Property Type + Bedrooms
  ↓
Search Properties
  ↓
Properties Found?
 ┌──────────────┴──────────────┐
 NO                           YES
 │                             │
Refine Requirements       Recommend 2–3
 │                         Properties
 └──────────────┬──────────────┘
                ↓
        Customer Interested?
          ┌─────┴─────┐
         NO          YES
          │            │
       Refine       Offer Visit
                       ↓
                 Check Calendar
                       ↓
                 Book Appointment
                       ↓
                 Send Confirmation
                       ↓
                      END
```

### Information to Collect

- Property type
- Location
- Budget
- Number of bedrooms
- Size
- Purpose
- Preferred visit time

---

## 3. Rental Inquiry

```text
START
 ↓
Greeting
 ↓
Identify Rental Requirement
 ↓
Collect:
 ├── Location
 ├── Monthly Budget
 ├── Bedrooms
 ├── Furnished/Unfurnished
 └── Move-in Date
 ↓
Search Rental Properties
 ↓
Results Found?
 ├── NO → Refine Requirements
 └── YES
       ↓
Recommend Properties
       ↓
Customer Selects Property
       ↓
Offer Property Visit
       ↓
Check Calendar
       ↓
Book Appointment
       ↓
Send Confirmation
       ↓
END
```

---

## 4. Commercial Property Inquiry

```text
START
 ↓
Identify Commercial Requirement
 ↓
Collect:
 ├── Location
 ├── Commercial Property Type
 ├── Area Required
 ├── Budget
 ├── Business Type
 └── Buy/Rent
 ↓
Search Commercial Inventory
 ↓
Rank Suitable Properties
 ↓
Recommend Properties
 ↓
Customer Interested?
 ├── NO → Refine Search
 └── YES
       ↓
Schedule Site Visit
       ↓
Calendar
       ↓
Confirmation
       ↓
END
```

---

## 5. Investment Inquiry

```text
START
 ↓
Identify Investor
 ↓
Collect:
 ├── Investment Budget
 ├── Location
 ├── Investment Horizon
 ├── Rental Income / Appreciation
 ├── Risk Preference
 └── Residential / Commercial
 ↓
Retrieve Relevant Information
 ↓
Identify Suitable Properties
 ↓
Present Factual Information
 ↓
Customer Interested?
 ├── NO → Refine Requirements
 └── YES
       ↓
Schedule Consultation / Visit
       ↓
Calendar
       ↓
Confirmation
       ↓
END
```

### Investment Guardrail

The agent must never guarantee financial returns.

Instead of:

> "Sir, is property ka 30% return guaranteed hai."

Use:

> "Sir, available historical information ke basis par is area mein appreciation hui hai, lekin future returns guarantee nahi kiye ja sakte."

---

## 6. Returning Customer

```text
Incoming Call
      ↓
Identify Phone Number
      ↓
Customer Exists?
   ┌──┴──┐
  YES    NO
   │      │
Load    Create
Memory  Customer
   │      │
   └──┬───┘
      ↓
Welcome Customer
      ↓
Recall Previous Preferences
      ↓
Ask What Has Changed
      ↓
Continue Conversation
```

Example:

> "Assalam-o-Alaikum Ahmed sahib. Welcome back. Aap last time DHA mein 5 marla house dekh rahe thay. Kya abhi bhi same requirement hai?"

---

## 7. Appointment Rescheduling

```text
Customer Requests Reschedule
          ↓
Identify Customer
          ↓
Find Existing Appointment
          ↓
Confirm Appointment
          ↓
Ask New Date/Time
          ↓
Check Calendar
          ↓
Available?
     ┌────┴────┐
    NO        YES
     │          │
Offer        Update
Alternative  Appointment
                ↓
          Send Confirmation
                ↓
               END
```

---

## 8. Appointment Cancellation

```text
Customer Requests Cancellation
            ↓
Identify Customer
            ↓
Find Appointment
            ↓
Confirm Appointment
            ↓
Cancel Calendar Event
            ↓
Update Database
            ↓
Send Confirmation
            ↓
END
```

---

## 9. General Conversation Pattern

All flows should follow a common high-level pattern:

```text
Greeting
   ↓
Intent Detection
   ↓
Requirement Discovery
   ↓
Information Retrieval
   ↓
Recommendation / Answer
   ↓
Objection Handling
   ↓
Next Best Action
   ↓
Appointment / Follow-up
   ↓
Confirmation
   ↓
Conversation End
```

### Design Principles

1. Ask one important question at a time.
2. Avoid long monologues.
3. Confirm important details.
4. Never invent property information.
5. Offer alternatives when requirements cannot be met.
6. Do not pressure customers.
7. Always confirm successful tool execution before reporting success.
8. Escalate complex cases to humans.
9. Maintain context throughout the conversation.
10. End with a clear next step.
