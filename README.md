# Hybrid RAG & Reasoning Pipeline

An advanced, asynchronous Question-Answering system designed to dynamically route queries and execute domain-specific reasoning. This project leverages a multi-phase architecture to handle Math, Reading Comprehension, and General Knowledge queries with high precision, utilizing local LLMs and semantic search.

## 🚀 Key Features & Architecture

The system is broken down into four distinct processing phases:

### Phase 1: Hybrid Routing
* **O(1) Keyword Matching:** Instantly catches Reading Comprehension tasks based on specific structural markers in the prompt.
* **LLM Zero-Shot Classification:** Utilizes `qwen3:8b` to deterministically route remaining queries into either `MATH` (pure calculation) or `KNOWLEDGE` (requiring external context).

### Phase 2: Precision RAG Pipeline (Knowledge Queries)
* **Query Expansion:** Generates multiple optimized search queries from the user's original prompt.
* **Concurrent Retrieval:** Uses `AsyncTavilyClient` to fetch web snippets concurrently, deduplicating the content.
* **Cross-Encoder Reranking:** Applies `BAAI/bge-reranker-v2-m3` to score and rank documents against the original query.
* **Dynamic Confidence Queuing:** Calculates a sigmoid confidence score. If the retrieval confidence falls below 0.70, the query is pushed to a background asynchronous queue to be rewritten and retried without blocking the main event loop.

### Phase 3: Reasoning Engine
* **Domain-Specific Prompts:** Applies tailored system instructions based on the routing category (e.g., enforcing step-by-step algebraic breakdowns for Math vs. context-grounded extraction for Knowledge).
* **Strict Output Formatting:** Forces the LLM to output its thought process and final answers within strict XML tags (`<answer_reasoning>` and `<final_answer>`) to prevent hallucinated formats.

### Phase 4: Orchestration & Deterministic Output
* **Regex Extraction:** Parses the XML tags to deterministically extract the final multiple-choice letter.
* **Async Batching:** Processes the evaluation dataset concurrently, significantly reducing execution time over synchronous loops.

## 🛠️ Tech Stack
* **LLM / Generation:** Ollama (`qwen3:8b`)
* **Retrieval:** Tavily API (Async)
* **Reranking:** FlagEmbedding (`bge-reranker-v2-m3`)
* **Concurrency:** Python `asyncio`
* **Data Processing:** Pandas, Regex, NumPy

## 📊 Evaluation & Results

The system was evaluated against a multi-choice dataset of 463 questions, taking approximately 4.7 hours to process the entire batch asynchronously. 

**Overall Accuracy:** **86.00%**

### Performance by Category

| Category | Total Questions | Correct Questions | Accuracy (%) |
| :--- | :--- | :--- | :--- |
| **KNOWLEDGE** | 270 | 221 | 81.85 |
| **MATH** | 94 | 89 | 94.68 |
| **READING** | 99 | 90 | 90.91 |

*Note: The MATH category performs exceptionally well due to the model bypassing the retrieval phase and relying entirely on the mathematically optimized system prompt.*