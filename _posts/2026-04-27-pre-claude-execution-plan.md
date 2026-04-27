---
layout: default
title: "PRE-CLAUDE EXECUTION PLAN"
date: 2026-04-27
---
# PRE-CLAUDE EXECUTION PLAN

**Generated:** 2026-04-27 08:34

---

## 1️⃣ TOPIC VALIDATION

**Topic:** junior developers  
**Category:** EMPLOYMENT IMPACT  

### Mandatory Criteria

| Criteria | Result | Evidence |
|----------|--------|----------|
| Untouched Category | ✅ YES | EMPLOYMENT IMPACT |
| Breaking News (24-48h) | ✅ YES | Recent news event |
| Scale/Impact | ✅ YES | Affects 1M+ or personal impact |
| Not Political | ✅ YES | Data-driven angle |
| Unique Angle | ✅ YES | Not covered previously |

**Overall Decision:** GO (MEDIUM confidence)  
**Reason:** All mandatory criteria met ✅

---

## 2️⃣ HEADLINE OPTIONS (Ranked by Score)


### 1. **They Tried to junior . It Just Backfired.**
- **Formula:** Formula 5: Direct Observation + Twist  
- **Score:** 86/100  
- **Explanation:** Punchy, specific, high curiosity gap  
- **Curiosity Gap:** high  

### 2. **They're junior Your developers Right Now (And Why It Matters)**
- **Formula:** Formula 1: Urgency + Threat  
- **Score:** 85/100  
- **Explanation:** High curiosity gap, personal threat, specific action  
- **Curiosity Gap:** high  

### 3. **The junior developers That Just Became Irreplaceable Again**
- **Formula:** Formula 2: Inversion/Expectation Flip  
- **Score:** 82/100  
- **Explanation:** Inverts common assumption, creates mystery  
- **Curiosity Gap:** medium-high  

### 4. **After 10 Years in Tech, I Realized Why This Matters More Than Ever**
- **Formula:** Formula 6: Authority + Insight  
- **Score:** 78/100  
- **Explanation:** Establishes credibility, promises insight  
- **Curiosity Gap:** medium  

---

## 3️⃣ ARTICLE OUTLINE

**Word Count Target:** 1050-1100 words

### Structure

- **Hook** (150w): Open with surprising juxtaposition or contradiction that mirrors headline
- **Section 1** (220w): What's the surface-level assumption?
- **Section 2** (230w): What's actually happening underneath?
- **Section 3** (220w): Why is everyone missing this?
- **Section 4** (220w): What does this mean going forward?
- **So What?** (80w): Restate the insight in fresh language. Answer: 'Why should reader care?'
- **Conclusion** (100w): Call to action or thought-provoking final line. No corporate jargon.

### Tone Requirements
- Witty but empathetic
- Contrarian but data-driven
- Provocative but not sensationalist
- Zero jargon, high clarity
- Mix of short and long sentences

### Required Elements
- 2-3 surprising juxtapositions
- 1 blockquote or data callout
- 1 bullet list or numbered structure
- Punchy subheadings (not generic)
- Reader's emotional reality acknowledged

---

## 4️⃣ IMAGE PROMPT

```
Visual metaphor of junior developers reversing course. Style: photorealistic, dramatic lighting, professional photography, editorial quality, cinematic, high contrast.
```

---

## 5️⃣ CLAUDE INSTRUCTIONS (COPY & PASTE)

```

TASK: Write a Medium blog post matching this exact specification.

TOPIC: junior developers
CATEGORY: EMPLOYMENT IMPACT

HEADLINE (primary):
They Tried to junior . It Just Backfired.

ARTICLE OUTLINE:
{
  "word_count": "1050-1100 words",
  "hook": {
    "target_words": 150,
    "instructions": "Open with surprising juxtaposition or contradiction that mirrors headline"
  },
  "section_1": {
    "target_words": 220,
    "question": "What's the surface-level assumption?",
    "key_point": "Latest trend data",
    "subheading": "Punchy, 4-8 words"
  },
  "section_2": {
    "target_words": 230,
    "question": "What's actually happening underneath?",
    "key_point": "Market reaction",
    "subheading": "Punchy, 4-8 words"
  },
  "section_3": {
    "target_words": 220,
    "question": "Why is everyone missing this?",
    "key_point": "Industry blind spot",
    "subheading": "Punchy, 4-8 words"
  },
  "section_4": {
    "target_words": 220,
    "question": "What does this mean going forward?",
    "key_point": "Forward implications",
    "subheading": "Punchy, 4-8 words"
  },
  "so_what": {
    "target_words": 80,
    "instructions": "Restate the insight in fresh language. Answer: 'Why should reader care?'"
  },
  "conclusion": {
    "target_words": 100,
    "instructions": "Call to action or thought-provoking final line. No corporate jargon."
  },
  "tone": [
    "Witty but empathetic",
    "Contrarian but data-driven",
    "Provocative but not sensationalist",
    "Zero jargon, high clarity",
    "Mix of short and long sentences"
  ],
  "required_elements": [
    "2-3 surprising juxtapositions",
    "1 blockquote or data callout",
    "1 bullet list or numbered structure",
    "Punchy subheadings (not generic)",
    "Reader's emotional reality acknowledged"
  ]
}

REQUIRED DATA POINTS (cite these):
[]

IMAGE PROMPT (for designer/Canva):
Visual metaphor of junior developers reversing course. Style: photorealistic, dramatic lighting, professional photography, editorial quality, cinematic, high contrast.

QUALITY CHECKLIST:
- Word count: 1050-1100 words
- All sections meet target word counts
- Structure: Hook → 4 sections → So What → Conclusion
- Tone matches specification (no jargon, witty, contrarian)
- Includes all required elements
- No hallucinated data points
- Fresh angle on junior developers

OUTPUT:
- Complete markdown file with H1 title
- Front matter: layout: default, title, date
- Clean formatting, no extra blank lines

```

---

## 6️⃣ COST ESTIMATE

**Estimated Claude API Cost:** $0.15-0.25 (text-only) or $0.40-0.60 (with image)

**Cost Savings by Using This Plan:**
- ✅ No topic validation API calls (done locally)
- ✅ No headline generation API calls (done locally)
- ✅ No image prompt refinement cycles (done locally)
- ✅ Structured outline reduces Claude's creative guessing
- **Total savings: ~60% fewer tokens**

---

## NEXT STEPS

1. **Review this plan** - Validate topic choice and headlines
2. **Run Claude** - Copy-paste section 5 into Claude with your topic context
3. **Process output** - Use `process_and_publish_posts.py` to clean and publish
4. **Push to blog** - Jekyll build + git push
