# Feature Specifications

This directory contains all feature specifications, implementation reviews, incident resolutions, and architectural decisions for the EdTech Chatbot backend.

## Structure

Each feature is organized in its own numbered folder:

```
specs/
├── 001-auth-jwt-system/
│   ├── spec.md                    # Feature specification
│   ├── reviews/                   # Implementation reviews
│   │   └── 001-implementation.md
│   ├── incidents/                 # Issues encountered and resolved
│   │   └── 001-bcrypt-issue.md
│   └── decisions/                 # Architecture decisions for this feature
│
├── 002-next-feature/
│   ├── spec.md
│   ├── reviews/
│   ├── incidents/
│   └── decisions/
│
└── README.md (this file)
```

## Features

### 001 - JWT Authentication System
**Status:** Implemented
**Spec:** [001-auth-jwt-system/spec.md](./001-auth-jwt-system/spec.md)
**Description:** JWT-based authentication with refresh tokens, role-based access control, and session management using DynamoDB.

**Reviews:**
- [001-implementation.md](./001-auth-jwt-system/reviews/001-implementation.md) - Post-implementation review (Grade: A-, 9/10)

**Incidents:**
- [001-bcrypt-issue.md](./001-auth-jwt-system/incidents/001-bcrypt-issue.md) - Bcrypt compatibility issue with passlib

**Decisions:**
- _(None yet)_

---

## How to Use This Structure

### When Adding a New Feature:
1. Create a new folder with the next number: `00X-feature-name/`
2. Write the spec in `spec.md`
3. Create empty subdirectories: `reviews/`, `incidents/`, `decisions/`
4. Update this README with the new feature

### When Documenting Issues:
Add to the feature's `incidents/` folder with sequential numbering:
- `001-issue-name.md`
- `002-another-issue.md`

### When Writing Reviews:
Add to the feature's `reviews/` folder with sequential numbering:
- `001-implementation.md` (post-implementation)
- `002-security-audit.md` (later reviews)

### When Making Architectural Decisions:
Add to the feature's `decisions/` folder with sequential numbering:
- `001-decision-name.md`
- `002-another-decision.md`

---

## Rebuilding the Application

To rebuild this application (even in a different language):
1. Read specs in numerical order (001, 002, 003...)
2. Check reviews for implementation notes and lessons learned
3. Review incidents to avoid known pitfalls
4. Consult decisions to understand the reasoning behind architectural choices
