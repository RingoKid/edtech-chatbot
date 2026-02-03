# Handwriting Lesson Composition Map

This document maps how Form C (the example handwriting lesson output) is composed from the various source forms.

---

## Mental Map: How Form C is Built

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FORM C (Example Output)                               │
│                     PreK Letter Z Lesson Plan                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  A. Standards │          │  B. Objectives │          │  C. Materials │
│               │          │               │          │               │
│ Source: GA    │          │ Source:       │          │ Source:       │
│ Standards PDF │          │ FORM A verbs  │          │ Derived from  │
│               │          │ + lesson focus│          │ activities    │
└───────────────┘          └───────────────┘          └───────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    D. Scripted Lesson Plan                                   │
│                    (Structure from FORM B)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SECTION          │ [Explanation]      │ #Teacher Script    │ Activity Source│
├──────────────────┼────────────────────┼────────────────────┼────────────────┤
│ 1. Review &      │ FORM B verbatim    │ "Sound Sparks"     │ FORM D         │
│    Connect       │ "The purpose..."   │ game               │ (low-level)    │
├──────────────────┼────────────────────┼────────────────────┼────────────────┤
│ 2. Model,        │ FORM B verbatim    │ Sound Hunt +       │ FORM D         │
│    Explain,      │ "The purpose..."   │ Letter formation   │ (low-level) +  │
│    Engage        │                    │ ##Verbal Cues      │ FORM F         │
├──────────────────┼────────────────────┼────────────────────┼────────────────┤
│ 3. Guided        │ FORM B verbatim    │ Magic Finger Write │ FORM D         │
│    Practice      │ "The purpose..."   │ + Trace & Say      │ (low + middle) │
├──────────────────┼────────────────────┼────────────────────┼────────────────┤
│ 4. Application   │ FORM B verbatim    │ Sound-Letter Hunt  │ FORM D         │
│                  │ "The purpose..."   │                    │ (middle-level) │
├──────────────────┼────────────────────┼────────────────────┼────────────────┤
│ 5. Wrap-Up       │ FORM B verbatim    │ Review + air write │ N/A            │
│                  │ "The purpose..."   │                    │                │
├──────────────────┼────────────────────┼────────────────────┼────────────────┤
│ *Modification    │ FORM H prompt      │ "Let me know..."   │ FORM H         │
└──────────────────┴────────────────────┴────────────────────┴────────────────┘
```

---

## Source Form Reference

| Form | What It Provides | Used In |
|------|------------------|---------|
| **Form A** | Suggested verbs for objectives (guidance, not strict) | Section B |
| **Form B** | Lesson structure + verbatim `[Explanation]` text | All sections |
| **Form C** | Gold standard example output | Reference only |
| **Form D** | Activity menu (low/middle/high level) | Sections 1-4 |
| **Form F** | Verbal cues for all letters A-Z, a-z | Section 2 |
| **Form G** | Phoneme gestures (PDF) | Section 2 (+Gesture) |
| **Form H** | Modification examples | End of lesson |

---

## Form A: Clarification on Objectives

### What Form A Contains

Form A is a list of **scaffolded verbs** ordered from simple to complex:

```
Orient → Point → Match → Name → Identify →
Pronounce → Discriminate → Repeat → Trace → Write →
Count → Segment → Isolate → Compare → Sort →
Delete → Add → Substitute → Blend → Build →
Spell → Generate → Combine → Construct
```

### How It's Referenced

The training codes say: `#Use FORM A for possible objective verbs`

The word **"possible"** indicates this is guidance, not a strict requirement.

### Inconsistency: Form C Doesn't Strictly Follow Form A

Form C objectives vs Form A verbs:

| Form C Objective | Verb Used | In Form A? |
|------------------|-----------|------------|
| Pronounce the /z/ sound correctly | Pronounce | ✅ Yes |
| Isolate the /z/ sound at the beginning | Isolate | ✅ Yes |
| Write the corresponding letter z | Write | ✅ Yes |
| Form uppercase and lowercase z | Form | ❌ **No** |

**"Form"** is used in the example (Form C) but is NOT in Form A's verb list.

### Implication for Evals

Form A is a **suggested guide** for verb selection, not a strict rule. The generator should:

1. Use Form A verbs when appropriate
2. Order objectives from easier → harder (scaffolded mastery)
3. Not be penalized for using verbs outside Form A's list

LLM-as-judge should evaluate **scaffolding quality** (are objectives ordered by difficulty?) rather than strict Form A verb matching.

---

## Form D Activity Levels → Student Level Mapping

| Student Level | Form D Activities Used |
|---------------|------------------------|
| **struggling** | Low-level activities (Sound Spark, Tap that Sound, Magic Finger Write) |
| **on-level** | Middle-level activities (Sound Detective, Trace & Say, Sound-Letter Hunt) |
| **advanced** | High-level activities (Write the Sound, Sound Puzzle, Cover & Try) |

---

## Tracing Form C Section by Section

### 1. Review & Connect
```
Form C uses: "Sound Sparks" game
↓
Form D source: "Sound Spark: The teacher points to a sound card and
               children must chorally pronounce the sound. (low-level)"
```

### 2. Model, Explain & Engage
```
Form C uses: "Sound Hunt" game + letter formation with verbal cues
↓
Form D source: "Sound Hunt: Teacher says words; children must listen to
               beginning, middle, or end sound... (low-level)"
↓
Form F source: "Z – Little line across, slant down, little line across"
```

### 3. Guided Practice
```
Form C uses: "Magic Finger Write" → "Trace & Say"
↓
Form D sources:
  - "Magic Finger Write: Children use their 'magic' pointer finger
     to trace letter shapes... (low-level)"
  - "Trace & Say: Children trace letters on dotted-line templates
     with a pencil, saying the strokes aloud... (middle-level)"
```

### 4. Application
```
Form C uses: "Sound-Letter Hunt"
↓
Form D source: "Sound-Letter Hunt: Teacher says words; children must listen
               to either the beginning, middle, or end sound... Children then
               write the corresponding sound... (middle-level)"
```

---

## Notation Conventions (from Form B)

| Symbol | Meaning | Example |
|--------|---------|---------|
| `[...]` | AI explains lesson parts | `[Explanation: "The purpose..."]` |
| `#` | Teacher script (what teacher says) | `#Teacher Script:` |
| `(...)` | Expected child response | `(children respond /z/)` |
| `{...}` | Teacher does (actions) | `{Teacher points to sound card}` |
| `+` | Gesture (phoneme gesture) | `+Gesture: zigzag motion` |
| `##` | Sequence verbal cues | `##Sequence Verbal Cues for letter z:` |
| `*` | Modification prompt | `*Adaptation: Let me know...` |

---

## Key Insight

The generator's job is **composition, not creation**:
1. Select appropriate activities from Form D based on student level
2. Copy verbatim explanations from Form B
3. Look up verbal cues from Form F for the target letter
4. Script the activities following Form C's style and detail level

This means LLM-as-judge evals should verify:
- Are Form B explanations copied verbatim?
- Do verbal cues match Form F exactly?
- Are activities selected from the correct Form D level?
- Does the script match Form C's detail and formatting?
