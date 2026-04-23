# CUG 2026 Review Packet Transcript for `pap143s2`

This document is a markdown reference transcript of the confirmed source PDF:

- Source file: `/Users/sfarrell/Downloads/pap143 Reviews Details.pdf`
- Extraction method: `pdftotext -layout`
- Normalization: minor markdown formatting cleanup, no substantive content edits

## Header

- Submission: `pap143s2`
- Decision: **CUG Proceedings and ACM ICPS Accept**
- Paper: **An Agentic Toolkit and Comparative Study for HPC Operations and User Support**
- Contributors: Demeure, Ding, Farrell, Konate, Lei, Naylor

## Summary of Reviews

| Reviewer | rel | tech | orig | rec |
| --- | --- | --- | --- | --- |
| Reviewer 5 | 3 | 3 | 3 | WEAK ACCEPT for ACM ICPS proceeding (3) |
| Reviewer 6 | 3 | 3 | 3 | ACCEPT for ACM ICPS proceeding (4) |
| Reviewer 7 | 5 | 4 | 5 | ACCEPT for ACM ICPS proceeding (4) |
| Reviewer 8 | 4 | 4 | 3 | WEAK ACCEPT for ACM ICPS proceeding (3) |
| Averages | 3.8 | 3.5 | 3.5 | 3.5 |

## Full Reviews

### Reviewer 5

#### Full Paper Evaluation

This paper discusses ATHOS, a model agnostic agentic HPC assistance tool. The authors discuss how ATHOS is deployed, present a framework for testing the performance of various base LLM models, RAGs and use of MCP. This is of interest to the CUG community and the HPC community as a whole.

Though studies have explored models ability to address user tickets and questions using models before, these have not deployed and tested a PoC HPC friendly agentic framework, something ATHOS aims to do.

Though the rough details are provided for the agentic framework, there are missing details that limit the ability of other centres to deploy such a framework. For instance, the text details the open-source tools used (Chroma, Langchain) but do not discuss how the agents manage/limit their resource consumption nor what guardrails are required or were tested.

The paper provides a useful preliminary assessment of LLM and harness, noting that some models are better paired with specific harnesses. It would be useful to diver deeper into why there is a degradation in performance but the study is still useful nonetheless.

This is not the only example of results that warrant further investigation. For instance, the curated Q&A and tickets show the two tested LLMs perform well and that simply attaching a semantic retrieval toolchain to an agent can reduce answer quality and reliability. Why? A deeper dive into this is warranted. It is understandable that an unstable retrieval path is unstable can give rise to failures but why would this affect one model over the other? Is the reduced performance of one model really due to pulling in far more context than the model can use effectively? The optimized variants that give seemingly systematic improved performance are designed to reduce unnecessary context loading but how exactly? How much effort was needed to produced this optimised set?

The LLAMA 4 judge rubric should be discussed in detail to truly interpret results presented. Are answers to some Q&A where it works well general questions? How much HPC specific knowledge is required (slurm, slingshot, MPI, parallel IO, etc)? The study does at least assess three different models as judges, but it would be useful to see in the technically challenging questions (which are a small subset) whether a human judge agrees with the assessments.

Overall, the paper is a useful preliminary study of LLMs + RAGs to provide user support but is missing some key details related to the framework and does not dive deep enough to answer the question on whether centres should deploy such frameworks given many (likely basic to moderate) questions can be answered by a number of LLMs or just a good search tool of a centres documentation paired with an LLM to summarise key bits of information.

#### Scored Review Questions

| rel | tech | orig | rec |
| --- | --- | --- | --- |
| 3 | 3 | 3 | WEAK ACCEPT for ACM ICPS proceeding (3) |

### Reviewer 6

#### Full Paper Evaluation

The paper centers around an open, model-agnostic agentic toolkit, ATHOS, for HPC operations and user support. The toolkit is pitched as a platform for systematically exploring design choices in agentic AI for HPC centers. The paper contributes an evaluation framework and dataset suite derived from real operational workflows and tailored to HPC operations.

In terms of strengths, the toolkit design and comparative studies are well-documented. The toolkit and empirical guidance provided by the work has potential to make for a timely and impactful contribution.

In terms of weaknesses, the results discussion is difficult to follow due row references using different names at times. Consider standardization naming conventions used when referencing results.

Additional comments:

- The author list at the top of pages runs into conference text. Consider using the `shortauthors` field to avoid run-in.
- Line 154 mentions SRE-oriented. Consider defining SRE.
- Section 2.1 primarily focuses on chatHPC. Consider exploring these potentially related works:
  - Joslin et. al. "Generating Frequently Asked Questions from Technical Support Tickets using Large Language Models." SC'25 Workshops.
  - Bondapalli et al. "AskHPC: A ChatBot for High Performance Computing User Support." SC'25 Workshops.
- Section 4.2 mentions configurations for models used with LangChain. Consider discussing configurations for models used with the external coding agent as well.
- Line 574 mentions single-turn cases. Consider defining what single-turn is.
- Line 583 discusses exclusion of administrative/policy-only cases. Consider adding explanation as to why these are excluded.
- Line 620 mentions partitioning incidents by Sept. 1, 2025. Consider adding explanation as to why this date is chosen.
- Line 660 mentions multi-turn tickets. Consider defining what multi-turn is.
- Line 748 mentions no-tool rows. Is this in reference to `lang_<model>_base` rows? Consider using config names when referencing rows.
- Section 5.5 mentions four points. Consider enumerating points.
- Section 5.5 reads as though it is the end of the section yet several additional results subsections follow. Consider revisiting the organization of Section 5 and/or splitting Section 5 into multiple sections.
- Line 890 mentions zeroes in Figure 3. These are difficult to see. Consider increasing zero size.
- Line 961 mentions `LangChain+Claude Sonnet` while line 967 mentions `SmolAgents + Claude Sonnet`. Consider standardizing whether or not a space is included before and after the `+`.
- Line 1022 mentions the paper's main table by name. Consider referencing this by table number.

#### Scored Review Questions

| rel | tech | orig | rec |
| --- | --- | --- | --- |
| 3 | 3 | 3 | ACCEPT for ACM ICPS proceeding (4) |

### Reviewer 7

#### Full Paper Evaluation

The paper presents a toolkit, named ATHOS, for creating AI agents focused on HPC operations and user support tasks.

The toolkit is modular and enables agents to be constructed by combining different models, harnesses, and tools, primarily retrieval-oriented components. The paper also introduces curated datasets and an evaluation methodology for HPC-focused AI agents, and uses them to analyze ATHOS across several dimensions.

Strengths:

- The topic is highly timely and relevant. AI agents are currently a prominent area of interest, and their use in streamlining operations and user support is likely to be of particular interest to CUG members.
- The paper is generally well written, informative, and easy to follow, especially in Sections 1, 2, 5, and 6.
- The analysis and discussion of results in Section 5 are extensive. The paper examines many relevant aspects of agentic usage, including the influence of models, retrieval tools and patterns, agent harnesses, output variance, and comparison with third-party coding agents.
- The empirical guidance could be a useful reference for sites evaluating similar agentic approaches.

Weaknesses:

The main weaknesses of the paper relate to presentation, particularly in Sections 3 and 4.

In these sections, the text is denser, less linear, and more difficult to follow. The exposition at times appears to assume substantial familiarity with concepts and terminology related to AI agents and associated tooling.

Given that the paper introduces a new project, the design description in Section 3 could be less succinct and would benefit from more frequent references to Figures 1 and 2 in order to better ground the discussion and guide the reader.

Section 4.3 could likely be moved before Section 4.6 so that the progression of topics more closely matches the structure reflected in Table 1.

More broadly, Sections 3 and 4 would benefit from a more linear progression of topics to improve readability and make the paper easier to follow.

Another important point is that, although the paper introduces a new project, it does not mention the availability of the software, for example through a source repository or project website, either as a citation or in a footnote.

It would be helpful for the authors to clarify whether the project materials are intended to be publicly available and, if so, to provide an appropriate reference.

#### Scored Review Questions

| rel | tech | orig | rec |
| --- | --- | --- | --- |
| 5 | 4 | 5 | ACCEPT for ACM ICPS proceeding (4) |

### Reviewer 8

#### Full Paper Evaluation

The paper presents a model-agnostic tool for AI-powered HPC user support and evaluates its performance for resolving user tickets and providing Q&A style answers. Many HPC centers have a need and interest for similar approaches and a such the paper could be of wider relevance. The methods and approaches used were explained in detail and the results are interesting albeit a bit underwhelming. Nevertheless, there is clear value in publishing the work.

#### Scored Review Questions

| rel | tech | orig | rec |
| --- | --- | --- | --- |
| 4 | 4 | 3 | WEAK ACCEPT for ACM ICPS proceeding (3) |

## Committee Comments

### Committee Comments for Authors

None.
