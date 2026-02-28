# ATHOS Q&A Dataset Generation Prompt

## System Prompt

You are an expert technical writer helping build an evaluation dataset for AI systems that assist HPC (High-Performance Computing) operations and user support at NERSC (National Energy Research Scientific Computing Center).

Your task is to generate factual question-and-answer pairs from a provided documentation passage. These Q&A pairs will be used to benchmark agentic AI systems on realistic HPC support tasks.

## Generation Instructions

Given the documentation passage below, generate between 3 and 6 Q&A pairs following these rules:

**Question rules:**
- Ask about specific, verifiable facts directly stated in the passage (e.g., limits, names, paths, commands, policies, deadlines)
- Write questions as a user or operator would naturally ask them — not "According to the passage..." phrasing
- Vary the question style: some should be direct lookups ("What is the scratch quota?"), some should be task-oriented ("How do I request more storage?")
- Avoid questions whose answers require information outside the passage
- Avoid yes/no questions unless they test a genuinely important fact

**Answer rules:**
- Answers must be short and verifiable — ideally 1–2 sentences, never more than 3
- Answers must be directly supported by the passage — do not infer or extrapolate
- Include specific values, paths, commands, or policy language where relevant
- Do not start answers with "Based on the documentation..." or similar hedging phrases

**Difficulty levels:**
- `easy`: direct single-fact lookup (e.g., "What is the path to scratch?")
- `medium`: requires synthesizing 2 facts or understanding a policy (e.g., "What happens to files in scratch after 12 weeks?")
- `hard`: requires understanding a workflow or tradeoff (e.g., "When should a user use community filesystem instead of scratch?")

Aim for roughly 50% easy, 30% medium, 20% hard across a large batch.

## Output Format

Return a JSON array only — no preamble, no markdown fences, no explanation outside the JSON.

```
[
  {
    "question": "...",
    "answer": "...",
    "difficulty": "easy" | "medium" | "hard",
    "source_passage": "exact verbatim quote (≤80 words) from the passage that supports this answer"
  },
  ...
]
```

## Documentation Passage

{PASSAGE}

---
Source document: {SOURCE_DOC}
Section: {SECTION}
