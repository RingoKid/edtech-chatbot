# Spec 001: Homepage Feedback Updates

## Overview

Update the homepage content based on stakeholder feedback to better reflect the L4C (Language for Composing) framework and educational approach.

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| AboutSection.jsx - About Us copy | ✅ Done | Updated L4C description, centered full-width |
| AboutSection.jsx - Remove image | ✅ Done | Removed `AboutUs.png` and "Early Writing Development" |
| AboutSection.jsx - Principles section | ✅ Done | Renamed `empowermentSteps` → `principles` |
| FeaturesSection.jsx - 3 Hubs | ✅ Done | Renamed `features` → `hubs`, new icons |
| FeaturesSection.jsx - Remove Philosophy | ✅ Done | Deleted entire block |

## Implementation Files

| File | Purpose |
|------|---------|
| `frontend/src/components/AboutSection.jsx` | About Us copy + L4C Principles section |
| `frontend/src/components/FeaturesSection.jsx` | 3 Hubs cards + removed Philosophy section |

---

## Change 1: AboutSection.jsx - Update "About Us" Copy

### Current (lines 81-89)
```jsx
<p className="text-gray-700 leading-relaxed mb-6 text-lg">
  Language for Early Childhood Composing is an innovative language immersion program that early childhood teachers enhance their effectiveness with practical support for effective teaching strategies.
</p>

<p className="text-gray-700 leading-relaxed mb-6 text-lg">
  With our Advanced lesson builder, educators can easily create tailored lessons that connect real-world classroom with engaging writing activities. Join us in fostering a love for writing and effective communication in young learners!
</p>
```

### New Copy
```jsx
<p className="text-gray-700 leading-relaxed mb-6 text-lg">
  Language for Composing (L4C) is an instructional approach grounded in the Science of Literacy, Learning, and Instruction. Through authentic composing, teachers intentionally support young children as they notice, analyze, and use language structures at multiple levels, including sounds, words, sentences, and discourse. L4C helps teachers make language visible, strengthening the connections among language, writing, and learning.
</p>

<p className="text-gray-700 leading-relaxed mb-6 text-lg">
  L4C's Advanced Lesson Builder helps teachers translate the science of literacy, learning, and instruction into clear, actionable classroom practice. The builder visually supports lesson sequencing and organization, helping teachers plan instruction in ways that reduce cognitive load while making the language demands of writing explicit. As teachers design composing lessons, they deepen their understanding of how language structures—across phonology, word, sentence, and discourse levels—operate during the writing process and how these structures can be intentionally supported as children generate meaning through text. By making the relationship between language and composing visible, the L4C Lesson Builder supports responsive instruction while strengthening teachers' expertise in language-based writing instruction.
</p>
```

---

## Change 2: AboutSection.jsx - Replace "Empowers Teachers" with "Principles of the L4C Approach"

### Current Section Title (lines 117-124)
```jsx
<motion.h2 ...>
  <span className="text-primary-600">How Language4Composing</span>
  <br />
  <span className="text-gray-900">Empowers Teachers</span>
</motion.h2>
```

### New Section Title
```jsx
<motion.h2 ...>
  <span className="text-primary-600">Principles of the</span>
  <br />
  <span className="text-gray-900">L4C Approach</span>
</motion.h2>
```

### Current Steps Data (lines 32-53)
```javascript
const empowermentSteps = [
  {
    number: "01",
    title: "Build knowledge of the language and writing skills young children need to become confident composors.",
    description: "Understanding developmental stages and foundational literacy skills that support early writing development."
  },
  {
    number: "02",
    title: "Integrate language and literacy skills during meaningful, authentic writing tasks.",
    description: "Connecting reading, speaking, listening, and writing in purposeful activities that engage young learners."
  },
  {
    number: "03",
    title: "Equip teachers with the tools to seamlessly integrate early writing practices into daily classroom interactions.",
    description: "Providing practical strategies and resources for embedding writing instruction throughout the school day."
  },
  {
    number: "04",
    title: "Equip teachers with the tools to seamlessly integrate early writing processes into daily classroom interactions.",
    description: "Supporting the development of writing as a process through planning, drafting, and sharing in age-appropriate ways."
  }
]
```

### New Principles Data
```javascript
const principles = [
  {
    number: "01",
    title: "Make language visible through responsive and explicit instruction.",
    description: "Teachers intentionally highlight how language works during composing, helping children notice, analyze, and apply language structures as they write."
  },
  {
    number: "02",
    title: "Scaffold children to increase the complexity of their language production and expression.",
    description: "Instruction supports children in moving from simpler to more complex ideas, sentences, and language forms within meaningful writing tasks."
  },
  {
    number: "03",
    title: "Anchor language instruction within authentic composing tasks that build language and concepts.",
    description: "Language development is inseparable from meaning-making and content knowledge; children learn language best when they use it to communicate ideas that matter."
  },
  {
    number: "04",
    title: "Coordinate multiple levels of language to support functional writing.",
    description: "L4C coordinates spelling and handwriting, sentence construction, and idea development so children experience how language works together to communicate ideas and meaning."
  }
]
```

**Note:** Also rename the variable from `empowermentSteps` to `principles` throughout the component.

---

## Change 3: FeaturesSection.jsx - Update Section Header

### Current (lines 70-84)
```jsx
<motion.h2 ...>
  <span className="text-gray-900">Educational</span>
  <br />
  <span className="text-primary-600">Enhancement Features</span>
</motion.h2>

<motion.p ...>
  Discover how Language for Composing transforms early childhood education through innovative approaches to writing and language development.
</motion.p>
```

### New
```jsx
<motion.h2 ...>
  <span className="text-gray-900">Educational</span>
  <br />
  <span className="text-primary-600">Enhancement</span>
</motion.h2>

<motion.p ...>
  L4C supports teachers by making language learning visible, connected, and meaningful—both in and beyond the classroom.
</motion.p>
```

---

## Change 4: FeaturesSection.jsx - Replace 3 Feature Cards with 3 Hubs

### Current Features Data (lines 10-35)
```javascript
const features = [
  {
    icon: Palette,
    title: "Enhances Creativity",
    subtitle: "Creative Expression Builder",
    description: "Unlock unlimited creative potential with tools designed to inspire imagination and artistic expression in young learners through structured writing activities.",
    color: "from-purple-500 to-pink-500",
    bgColor: "from-purple-50 to-pink-50"
  },
  {
    icon: Users,
    title: "Collaborative Learning",
    subtitle: "Community Learning Hub",
    description: "Foster collaborative learning environments where teachers and students can share, learn, and grow together in supportive educational communities.",
    color: "from-green-500 to-emerald-500",
    bgColor: "from-green-50 to-emerald-50"
  },
  {
    icon: Heart,
    title: "Nurturing Development",
    subtitle: "Child-Centered Approach",
    description: "Support the whole child through developmentally appropriate practices that nurture both academic growth and social-emotional learning.",
    color: "from-orange-500 to-red-500",
    bgColor: "from-orange-50 to-red-50"
  }
]
```

### New Hubs Data
```javascript
import { Users, Video, BookOpen } from 'lucide-react'  // Update imports

const hubs = [
  {
    icon: Users,
    title: "Community Learning Hub",
    subtitle: "Connect & Share",
    description: "Teachers, families, and researchers come together to share questions, insights, and classroom experiences. This space supports responsive instruction by helping educators learn from one another and from research on how children use language in real writing contexts.",
    color: "from-green-500 to-emerald-500",
    bgColor: "from-green-50 to-emerald-50"
  },
  {
    icon: Video,
    title: "Knowledge Builder Hub",
    subtitle: "Learn & Grow",
    description: "Short videos for teachers to deepen their understanding of the language skills and processes involved in early writing development.",
    color: "from-blue-500 to-cyan-500",
    bgColor: "from-blue-50 to-cyan-50"
  },
  {
    icon: BookOpen,
    title: "Resource Hub",
    subtitle: "Explore & Discover",
    description: "A curated collection of trusted resources to help teachers explore research and practical strategies for supporting language, writing, and learning in the classroom.",
    color: "from-purple-500 to-pink-500",
    bgColor: "from-purple-50 to-pink-50"
  }
]
```

**Note:**
- Update import: Replace `Palette, Heart` with `Video, BookOpen`
- Rename variable from `features` to `hubs` throughout the component

---

## Change 5: FeaturesSection.jsx - REMOVE "Educational Philosophy" Section

### Delete Entirely (lines 117-132)
```jsx
{/* Educational Philosophy */}
<motion.div
  className="text-center bg-white rounded-3xl p-12 shadow-xl"
  initial={{ opacity: 0, y: 30 }}
  animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
  transition={{ duration: 0.8, delay: 0.6 }}
>
  <h3 className="text-3xl font-bold text-gray-900 mb-6">
    Our Educational Philosophy
  </h3>
  <p className="text-lg text-gray-600 max-w-4xl mx-auto leading-relaxed">
    We believe that every child is a natural storyteller. Through structured yet flexible approaches to early writing,
    we help teachers create environments where children feel confident to express their thoughts, share their experiences,
    and develop essential literacy skills that will serve them throughout their educational journey.
  </p>
</motion.div>
```

**Action:** Delete this entire block.

---

## Summary of Changes

| Section | Action | File |
|---------|--------|------|
| About Us copy | UPDATE text, centered full-width | AboutSection.jsx |
| About Us image | DELETE image + caption | AboutSection.jsx |
| "Empowers Teachers" → "Principles of L4C" | RENAME + UPDATE content | AboutSection.jsx |
| 4 empowerment steps → 4 principles | REPLACE data | AboutSection.jsx |
| "Enhancement Features" → "Enhancement" | UPDATE header | FeaturesSection.jsx |
| 3 feature cards → 3 hub cards | REPLACE data + icons | FeaturesSection.jsx |
| Educational Philosophy box | DELETE | FeaturesSection.jsx |

---

## Verification

### Manual Test (Docker)
```bash
# Rebuild and start containers
docker compose down && docker compose up -d --build

# Open homepage
open http://localhost:3000
```

### Expected Output
- [ ] **About Us section:** Shows new L4C description (2 paragraphs, centered, full-width)
- [ ] **No image:** `AboutUs.png` and "Early Writing Development" caption removed
- [ ] **Principles section:** Title is "Principles of the L4C Approach" with 4 new principle cards
- [ ] **Enhancement section:** Title is "Educational Enhancement" (no "Features"), tagline mentions L4C
- [ ] **3 Hub cards:** Community Learning Hub, Knowledge Builder Hub, Resource Hub
- [ ] **No Philosophy box:** "Our Educational Philosophy" section is removed
- [ ] **Animations work:** Framer Motion fade-in effects on scroll
- [ ] **No console errors:** Check browser dev tools

---

## References

- Feedback source: `frontend/specs/001-feedback-updates/feedbacks/homepage-feedback.md`

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-21 | Initial implementation - all homepage feedback changes complete |
| 0.2 | 2026-01-21 | Removed About Us image + caption, centered text full-width |
