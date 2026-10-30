# PRD: Moroccan Legal Assistant

| | |
|---|---|
| **Owner** | Amine Ben Elmahdi |
| **Status** | v1 shipped (capstone) · v2 in progress |
| **Last update** | October 2026 |

## 1. Problem

Moroccan law is public but not usable. The main codes are long PDFs, often scanned, split between French and Arabic, with no reliable search. People who need a quick, sourced answer (students, founders, citizens) either read hundreds of pages or ask a general chatbot that may cite articles that do not exist.

**Problem statement:** a non-lawyer cannot get a sourced answer to a simple question about Moroccan law in under a minute.

## 2. Users and jobs to be done

| Persona | Job to be done | Today's workaround |
|---|---|---|
| Law / business student | Find the article that answers an exam or case question | Ctrl+F in PDFs, course notes |
| Founder / small business owner | Understand an obligation before calling a lawyer | Forums, asking around, generic chatbots |
| Citizen | Check a right or a rule (family, work, constitution) | Social media, word of mouth |

## 3. Goals and non-goals

**Goals**
- Answer in natural language **from official texts only**, with a verifiable citation for each claim.
- Work in French and Arabic.
- Be usable in under a minute, with no setup beyond an API key.

**Non-goals**
- Replacing a lawyer or giving personalised legal advice.
- Covering case law (jurisprudence) in v1/v2.
- Drafting legal documents.

## 4. Scope

| Version | Scope |
|---|---|
| **v1 (shipped)** | Upload documents or URLs, RAG chat, OpenAI / Azure OpenAI models |
| **v2 (this cleanup)** | Bundled corpus (4 codes) in one click, grounded prompt with `[file, p. N]` citations, refusal when the answer is not in the texts, chunking bug fix, reproducible install |
| **v3 (next)** | Evaluation set, article-level citations, OCR, more codes, hosted demo |

## 5. Success metrics

| Metric | Definition | Target (v3) |
|---|---|---|
| Citation accuracy | Share of answers whose cited article actually supports the claim | ≥ 90 % |
| Correct refusal rate | Share of out-of-corpus questions where the assistant says it does not know | ≥ 95 % |
| Answer coverage | Share of in-corpus questions answered with a correct citation | ≥ 80 % |
| Time to first answer | From opening the app to first sourced answer | < 60 s |

Measured on a hand-built set of 50 questions (FR/AR) with expected articles.

## 6. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Hallucinated articles | User acts on a rule that does not exist | Context-only prompt, mandatory citations, refusal path, eval set |
| Outdated texts | Answer is wrong after an amendment | Show corpus date, refresh process, roadmap item |
| Users treat it as legal advice | Liability, real-world harm | Disclaimer in every answer and in the README |
| Uploaded documents may contain personal data | Privacy exposure | Files are deleted after indexing; index lives only in the session |
| API cost | Demo becomes expensive if public | Users bring their own key; small, cheap default model |

## 7. Open questions

- Which embedding model gives the best retrieval on Arabic queries?
- Is page-level citation enough for students, or is article-level required?
- Would a hosted demo need rate limiting or a shared key with a budget cap?
