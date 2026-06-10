# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." 
     
     I want to tackle the experience of neuroscience majors at UCLA - useful because despite the school size, the neuroscience department doesn't have it's own dedicated undergrad department and is run by a larger interdepartmental group. As a result, information can feel scattered.
     
     -->

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | reddit | forum post| https://www.reddit.com/r/ucla/comments/heshap/a_little_neuroscience_advice/|
| 2 | reddit | forum post | https://www.reddit.com/r/ucla/comments/1tx4w7h/recommended_first_quarter_freshman_classes_for/|
| 3 | reddit | forum post | https://www.reddit.com/r/ucla/comments/1siadcz/ucla_neuro_students_how_is_it/ |
| 4 | ucla neuro dep website | list of profs| https://www.neurosci.ucla.edu/faculty/|
| 5 | ucla neuro dep website | reqs page | https://www.neurosci.ucla.edu/program/major-requirements/|
| 6 | ucla neuro dep website | reqs page | https://www.neurosci.ucla.edu/program/minor-requirements/|
| 7 | ucla neuro dep website | reqs page | https://www.neurosci.ucla.edu/program/major-capstone/ |
| 8 | bruinwalk | prof review | https://www.bruinwalk.com/professors/natik-piri/all/ |
| 9 | bruinwalk | prof review | https://www.bruinwalk.com/professors/william-grisham/|
| 10 | bruinwalk | prof review | https://www.bruinwalk.com/professors/stephanie-a-white/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
The chunk size is 1200 characters, which is big enough to capture an entire student course review or reddit post, but not so big that it gets noisy and other unrelated posts and reviews are wrapped into the chunk.

**Overlap:**
200 tokens is a good overlap, helping to retain important contextual data without creating too much data redundancy.

**Why these choices fit your documents:**
As explained above, these are good constraints to gain enough relevant information from each course review, professor review, department info page, reddit thread, without wrapping in other noise or repeating too much data across chunks. These were also changed back and forth after testing it out. 

**Final chunk count:**
124 chunks
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I used sentence-transformers/all-MiniLM-L6-v2, since it's a small, lightweight model but is more than enough for the relatively small amount of chunks/data that we're working with.

**Production tradeoff reflection:**
We could definitely increase the model size and parameters if we wanted, which would probably increase the accuracy, and provide slighly more domain knowledge (of academic processes in general). Also, we would benefit from an increase in context window size in the case we wanted to parse larger reddit threads/subreddits, longer course reviews, etc.
---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

```
You are a helpful academic assistant for UCLA Neuroscience students. 
Answer the user's question using ONLY the information provided in the Context Documents below. 

Strict Rules:
- If the documents do not contain enough information to fully answer the question, explicitly say "I don't have enough information on that." 
- Do not use any outside knowledge.
- Do not hallucinate or guess.
- Keep your answer clear, direct, and conversational.

Context Documents:
{context_text}

User Question:
{question}

Answer:
```

After several rounds of trial and error, this prompt helped a lot in ensuring that the model adheres strictly to the information parsed from the documents, instead of degrading into a confidently incorrect state. Stressing avoiding outside knowledge and using the chunks significantly increased accuracy.

**How source attribution is surfaced in the response:**
The url (since all docs are sourced from currently online pages) is given for each response based on the document that the chunks relevant to the answer are parsed from. Multiple chunks from multiple documents providing answers leads to multiple urls given that the user can follow to verify the information. 

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Who are the department chairs of the Undergraduate Neuroscience Interdepartmental Program? | Dr. Emily White is the chair, and Dr. Stephanie Leal is the Vice Chair. | Not enough information - only has info on the various chairs of subdepartments of the group.| Partially relevant | Accurate|
| 2 | What are the core upper division major requirements?| Neuro M101A/B/C, Neuro 102, Chem 153A| The core upper division major requirements for the Neuroscience major consist of 5 courses: 

1. Neuroscience M101A (Fall Quarter Only) 
2. Neuroscience M101B (Winter Quarter Only) 
3. Neuroscience M101C (Spring Quarter Only) 
4. Neuroscience 102 (Fall Quarter or Summer) 
5. Chemistry and Biochemistry (CHEM) 153A.| Relevant | Accurate|
| 3 | What rating does Professor White have for NEUROSC M101A?| 2.6| Not enough information for NERUOSC M101A, but Professor White has an overall rating of 2.7.| Relevant | Partially accurate|
| 4 | What is the minimum GPA for students to declare the Neuroscience minor?| 2.0 GPA overall, 2.5 in the prerequisite courses to M101A | To declare the Neuroscience minor, students must have an overall 2.0 GPA or better and a minimum 2.5 GPA in the prerequisite courses to Neuroscience M101A and M101B. | Relevant | Accurate |
| 5 | Where is successful completion of the minor indicated?| On the transcript and the diploma. | Successful completion of the minor is indicated on the transcript and diploma. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
What rating does Professor White have for NEUROSC M101A?
**What the system returned:**
Not enough information for NERUOSC M101A, but Professor White has an overall rating of 2.7.
**Root cause (tied to a specific pipeline stage):**
I believe this is due to some complex HTML in the BruinWalk page that the chunking and ingesting portion of the pipeline had some difficulties in parsing accurately. The page layout is unlike the other sources that we used, and had a lot of visual elements, so this information requires some more careful scraping.
**What you would change to fix it:**
Custom scraping for the BruinWalk website would work a lot better, and maybe even scraping each professor's page in addition to each of their attached course pages - essentially grabbing more information while paying closer attention to the HTML/CSS differences that change the chunking compared to other sources we used.
---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
On a general level, the spec helped a lot with keeping track of what steps I was on, what next I needed to implement, and pinpointing where something went wrong. Having a spec to refer to meant that I spent less time searching through code and more time assessing the logic of the app.

**One way your implementation diverged from the spec, and why:**
I had to chunk differently than I initially thought, mostly because of unexpected difficulties with HTML/CSS pages. Since I have 3-4 sources of information across the 10 documents, accounting for the quirks of each source took more attention and detail than the spec initially required. These quirks included unexpected tags, links, walls of text that were unrelated (noise from other unrelated forum posts), and bot blockers.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I gave ChatGPT my chunking strategy after I realized that Reddit was blocking my scraping with a simple bot blocker.
- *What it produced:* It produced a simple code change, that I wouldn't have realized, to bypass the bot blocking and access the threads I needed via old.reddit.com.
- *What I changed or overrode:* It initially suggested a separate chunking method for reddit posts, but since we only have 10 documents that we're working with, I just incorporated it into the existing chunk function.

**Instance 2**

- *What I gave the AI:* I gave ChatGPT the outline of how I wanted the pipeline to be structured, and to create a markdown diagram to fit cleanly into the planning.md and readme.md.
- *What it produced:* It gave me a Mermaid diagram, which I didn't have experience with at all, and had to learn more in order to use it correctly. 
- *What I changed or overrode:* I had open my own Mermaid editor in order to produce the image, and changed a few aspects that were inaccurate (placement, ordering of some elements of the pipeline) before I could put it into planning.md.
