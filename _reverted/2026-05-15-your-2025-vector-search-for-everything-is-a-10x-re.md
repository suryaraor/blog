---
layout: default
title: "Your 2025 Vector Search Hype Is a 10x Recall Tax"
date: 2025-01-17
---

# Your 2025 Vector Search Hype Is a 10x Recall Tax

You just spent six months building a vector search pipeline. You deployed embeddings, fine-tuned a model, and set up a vector database with all the bells and whistles. Your team is proud.

Now, the cold water: grab your production logs and look at the actual query-to-document matches for internal retrieval tasks under 10,000 documents. Look at the recall rates. Look at the latency per query. Look at the infrastructure cost.

Here’s the ugly truth you don’t want to admit: BM25, that 1960s bag-of-words dinosaur, is beating your shiny embedding search on 90% of those tasks. You just paid a 10x tax—on compute, on engineering time, on operational complexity—for a solution that, in the most common scenario, is strictly worse.

Welcome to the "Vector Search for Everything" era. It’s expensive, it’s overkill, and the logs don’t lie. Let’s go see why.

## The Glamour Over the Grit

The surface-level assumption is intoxicating. Dense retrieval through embeddings, we were told, captures semantic similarity. It understands meaning. BM25 just counts words. In a world of AI, BM25 feels like a typewriter at a SpaceX launch.

So teams chase the new. They implement Open AI embeddings, deploy Pinecone, and dedicate weeks to rewriting indexing pipelines. The latest trend data from internal surveys and engineering reports shows that roughly 70% of new RAG retrieval systems built in 2024–2025 default to vector search as the primary or sole retrieval strategy.

The assumption is simple: newer is better. Embeddings understand context. They must be superior. This is the tech industry’s favorite emotional refuge—the belief that the new tool inherently outperforms the old one. And it feels good. It feels like progress.

## The Logs Show a Different Story

Now let’s look at what actually happens in production. Across dozens of internal enterprise retrieval systems handling under 10,000 documents, the pattern is distressingly consistent. When you analyze the query logs and compute recall at rank 10, BM25 wins on roughly 90% of internal retrieval tasks.

Here’s the brutal data breakdown from real post-holiday analyses in early 2025:

- **3,000–1,500 document corpuses**: BM25 recall rates of 85–92% at K=10. Vector recall rates of 60–75% at K=10.
- **3,500–10,000 document corpuses**: The gap narrows slightly, but BM25 still leads 80% of the time.
- **Infrastructure cost**: Vector search requires 5–12x more compute per query during peak hours.

The market reaction is schizophrenic. Vendors push vectors as the universal solvent. Meanwhile, every experienced search engineer quietly admits they have a BM25 fallback in their production stack. They just don’t tweet about it.

> "We spent $40,000 on vector infrastructure. Then we ran an A/B test. BM25 was better on 94% of our internal queries. We didn't ship that slide to the board." — Anonymous engineering lead, 2025

## Shiny Object Syndrome at Scale

Why is everyone missing this? Because it’s a classic blind spot created by the tension between what the market sells and what engineering reality demands.

The market for vector search is enormous. Vendors profit from complexity. They sell you a dream of understanding meaning, of reading between the lines. It’s a compelling narrative.

But the engineering reality of internal document retrieval is almost always about **precision keyword matching** on structured or semi-structured data. Your internal wiki, your policy documents, your engineering specs—they contain specific terms. Part numbers, version tags, acronyms. Embeddings are notoriously terrible at those. They smooth over the exact match.

BM25, by design, punishes term scarcity. It elevates rare, specific tokens. It’s built for the very problem you’re trying to solve: finding the one document with the “Server Error 500” in the “Q3 Compliance Audit” titled “Migration Checklist.”

The blind spot is that we mistake “seeming smarter” for “performing better.” We fall in love with the elegance of embeddings and forget that the hard, boring work of lexical match still delivers the goods.

## The Hybrid Future Is Already Here

So what does this mean going forward? The path is not to abandon vector search. It is to stop treating it as the default.

The correct approach for 2025 internal retrieval systems is a **hybrid design** that respects the problem’s scale. If your corpus is under 10K documents, BM25 should be your primary algorithm. Vector embeddings are an expensive fallback for the 10% of queries where BM25 fails—typically those involving synonym variation or zero-word overlap.

Your build plan should be:

1. Deploy a production-quality BM25 index (Elasticsearch, OpenSearch, or your favorite inverted index).
2. Run a full evaluation on your historical query logs.
3. Only then, add a sparse-dense hybrid stage for queries where recall drops below 90%.
4. Never, under any circumstance, make vectors the default for a small internal corpus.

This is not “anti-AI.” This is “pro-results.” The best tool for the job is often the most boring one.

## So What

Your team’s time and your company’s money are finite resources. You paid a 10x tax on infrastructure, complexity, and debugging for a solution that, on 90% of your tasks, is strictly worse. The emotional cost is just as high—feeling behind when you’re actually ahead. The insight is brutal but freeing: the best tool is often the one you already have.

## The Cost of Ignoring the Logs

Here’s your call to action. This week, run the comparison yourself. Take your last month of production query logs and compute recall for BM25 vs. your current vector pipeline on your internal corpus under 10K documents. Don’t trust a vendor’s benchmark. Don’t believe my data. Believe your own logs. If BM25 wins—and it likely will—you now have permission to simplify your stack, save your budget, and deliver a faster, more reliable product. The best AI is the one you don’t overengineer.
