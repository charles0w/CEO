# CEO Local LLM Research Snapshot

Date: 2026-04-28
Status: baseline research before adding local model backends to CEO
Primary question: what should we learn from the most important current LLM families before we redesign CEO around local inference?

## How to use this file

This is the resume point for future work.

If we return to this project later, start here:
1. Re-read the "Executive conclusions" and "What CEO should do next" sections.
2. Treat the model shortlist in this file as the initial benchmark set.
3. Keep the distinction between hard evidence and inference. Closed vendors do not publish every implementation detail.

## Scope and selection rules

This note focuses on model families that matter most for one of these reasons:
- they are top-of-market frontier models that define product expectations
- they are widely used open or open-weight families with strong local deployment ecosystems
- they contribute specific efficiency ideas that are directly relevant to a local-first CEO assistant

This is not literally every LLM on the market. It is the set that is most relevant to building a strong local assistant on desktop-class hardware as of April 28, 2026.

## Executive conclusions

1. The winning pattern in 2026 is not one giant model. It is a system:
   - routing between fast and deep reasoning modes
   - strong tool use and structured outputs
   - aggressive prompt/context caching
   - memory outside the raw context window
   - smaller specialized models where possible

2. The best open/open-weight families are now good enough that CEO should prototype locally before attempting anything custom.
   - Best early candidates for local testing: Mistral Small 3.1, Devstral Small 2, Gemma 3, Qwen3 mid-size models, Phi-4, and OpenAI gpt-oss-20b.

3. The most transferable efficiency ideas are now clear:
   - Mixture-of-Experts (MoE) with low active parameters
   - grouped-query or multi-query attention and KV-cache efficiency
   - prompt/context caching and context compaction
   - reasoning distillation from stronger models into smaller deployable models
   - quantization as a first-class product concern, not a later optimization
   - hybrid thinking budgets instead of paying deep-reasoning cost on every request

4. For CEO specifically, the right first move is not training a brand-new base model.
   - The right first move is a provider abstraction plus a benchmark harness plus local model trials.

5. Full frontier open models are not automatically local-friendly.
   - DeepSeek-V3/R1 full models, Llama 4 Maverick, gpt-oss-120b, and Devstral 2 are important to learn from, but are not the right first-pass deployment targets for a Mac mini style node.
   - That hardware-fit judgment is an inference based on published model sizes and deployment guidance, not a direct vendor quote.

## What the closed frontier models are teaching us

### OpenAI: GPT-5.5, GPT-5.4, GPT-5, GPT-4.1

What stands out:
- OpenAI is pushing a unified "real work" model story: reasoning, coding, documents, spreadsheets, web research, and agentic task completion.
- GPT-5 introduced a router-style system that decides when to answer quickly and when to think longer.
- GPT-4.1 remains a strong API reference point for long context plus tool calling plus structured outputs.
- OpenAI also now spans hosted frontier models and open-weight local models, which is strategically important.

Ideas to steal:
- Build a provider/router layer, not a single-model architecture.
- Separate flagship, mini, and nano roles. Distill strong behavior into smaller models for subagents and latency-sensitive tasks.
- Treat structured outputs and tool calling as core capabilities, not optional extras.
- Design the backend around cached prefixes and reusable context.

Evidence:
- GPT-5 is described as a unified system with a router that decides when to think longer.
- GPT-5.4 is positioned for professional work across tools and documents.
- GPT-5.5 emphasizes agentic coding, computer use, knowledge work, and next-generation inference efficiency.
- GPT-4.1 supports a 1M-token context window, function calling, structured outputs, fine-tuning, distillation, and tool integrations.
- OpenAI's open-weight gpt-oss line shows that the company now treats local deployment as strategically important, not just a hobbyist edge case.

### Anthropic: Claude Opus 4.7 and Sonnet 4.6

What stands out:
- Anthropic is extremely strong on long-running coding and agent workflows.
- Claude's public docs and releases show unusually explicit product-level thinking about memory, caching, context compaction, and tool orchestration.
- Sonnet 4.6 looks especially important because it pushes frontier-style behavior down into a more practical cost and latency tier.

Ideas to steal:
- File-backed memory, not just bigger context windows.
- Prompt caching with explicit TTL controls.
- Context compaction that summarizes older turns instead of blindly truncating them.
- Tool-result filtering before stuffing everything back into context.
- Adaptive reasoning effort so the system can scale thought depth per task.

Evidence:
- Claude 4 launched extended thinking with tool use, parallel tools, better instruction following, and stronger memory behavior when given file access.
- Sonnet 4.6 adds a 1M-token context window in beta, context compaction, adaptive thinking, and automated tool-side code execution to filter search results for token efficiency.
- Anthropic's prompt caching docs recommend caching tool definitions, system prompts, context, and examples, with 5-minute or 1-hour TTL.

### Google: Gemini 3 and the Gemini/Gemma stack

What stands out:
- Google is still strongest when multimodality, long context, and broad platform integration matter.
- Gemini 3 continues the pattern of reasoning plus multimodality plus tooling.
- Google's caching story is unusually mature and practical.

Ideas to steal:
- Context caching should be first-class in the API and backend.
- Multimodal understanding should be part of the architecture early, not bolted on much later.
- Use one family across different surfaces when possible, but expose cheaper/faster variants for common paths.

Evidence:
- Gemini 3 is presented as Google's most intelligent model with improved reasoning, multimodality, coding, and tool use.
- Gemini API docs describe both implicit caching and explicit caching, with concrete rules for cache-friendly prompt structure and TTL-based reuse.
- Google's open Gemma line inherits many of these platform ideas in a more local-friendly form.

### xAI: Grok 4 / 4.1 / 4.20

What stands out:
- xAI is leaning hard into reasoning, large context, real-time data access, and tool-rich agents.
- Public xAI docs show function calling, structured outputs, reasoning support, and very long context windows on current API models.

Ideas to steal:
- Strong retrieval and real-world tool integration should be part of the product identity.
- Prompt caching and large context only matter if the system is architected to exploit them.
- Real-world tool-domain RL appears to be a serious differentiator for production agents.

Evidence:
- Grok 3 emphasized large-scale RL for reasoning and tool-rich DeepSearch behavior.
- Current xAI docs expose models with reasoning, function calling, structured outputs, cached prompt pricing, and very large context windows.

### Cohere: Command A

What stands out:
- Cohere is still one of the clearest examples of productizing an LLM for enterprise RAG, agents, multilingual work, and efficient deployment.
- Command A is not the "smartest model overall" story; it is the "best enterprise compute/performance ratio" story.

Ideas to steal:
- Optimize explicitly for tool use, RAG, grounded responses, and multilingual enterprise workflows.
- Build models that avoid unnecessary tool calls.
- Keep the model footprint practical for deployment, even when targeting strong capability.

Evidence:
- Cohere describes Command A as excelling at enterprise tasks, tool use, RAG, agents, and multilingual work.
- Cohere states that Command A has a 256K context window, requires only two A100/H100 GPUs, and delivers 150% higher throughput than its predecessor.

## What the open and open-weight model families are teaching us

### OpenAI gpt-oss

Why it matters:
- This is one of the clearest signs that local/open deployment is now part of the frontier strategy itself.
- The 20B variant is especially important for CEO because it is aimed at low-cost local use and edge-style deployment.

Best features:
- Strong reasoning for an open-weight family.
- Function calling and structured outputs.
- Consumer-hardware orientation.
- Paired safety models (gpt-oss-safeguard) suggest a system-level view, not just raw weights.

Efficiency strategies to copy:
- MoE with low active parameter counts.
- Alternating dense and locally banded sparse attention.
- Grouped multi-query attention for inference and memory efficiency.
- Open-weight release plus deployment guides for Ollama, vLLM, LM Studio, and others.

Evidence:
- OpenAI says gpt-oss-120b and gpt-oss-20b are state-of-the-art open-weight reasoning models.
- gpt-oss-120b uses 117B total params with 5.1B active params; gpt-oss-20b uses 21B total with 3.6B active params.
- OpenAI says the 120b model fits a single 80GB GPU and the 20b model can run on edge devices with 16GB of memory.

CEO takeaway:
- gpt-oss-20b belongs in the first serious benchmark pass.
- gpt-oss-120b is more of a later server-class option than a first-pass Mac mini target.

### Meta Llama 4 Scout and Maverick

Why it matters:
- Meta remains one of the most important ecosystem shapers in open-weight LLMs.
- Llama's value is not just raw performance. It is ecosystem depth, community tools, and downstream fine-tunes.

Best features:
- Native multimodality.
- MoE architecture.
- Early fusion for multimodal inputs.
- Massive ecosystem support.

Efficiency strategies to copy:
- Use MoE to increase capacity without dense inference cost.
- Treat multimodal fusion as a core architectural choice.
- Build for ecosystem compatibility, not just raw benchmark wins.

Evidence:
- Meta's official Llama 4 model cards describe Scout and Maverick as natively multimodal models using MoE and early fusion.
- The Scout model card lists 17B activated parameters, 109B total parameters, and an extremely large advertised context length.

CEO takeaway:
- Llama 4 is strategically important to understand.
- It is not the best first local CEO benchmark unless a specific quantized/distilled variant proves compelling.

### Qwen3

Why it matters:
- Qwen3 may be one of the most practically interesting open families for CEO right now.
- It combines broad size coverage, Apache 2.0 licensing, multilingual strength, hybrid thinking, and wide deployment support.

Best features:
- Hybrid thinking and non-thinking modes in the same family.
- Dense and MoE variants across many sizes.
- 119-language support.
- Strong local deployment guidance across Ollama, MLX, llama.cpp, vLLM, and SGLang.

Efficiency strategies to copy:
- Explicit thinking-budget control.
- Small-MoE design for better capability/cost tradeoffs.
- Unified family with broad deployment targets.
- Multi-stage post-training that fuses deep reasoning and fast response behavior into one model.

Evidence:
- Qwen says Qwen3-235B-A22B is the flagship model and Qwen3-30B-A3B is a smaller MoE model.
- Qwen's post describes hybrid thinking modes, a soft switch between /think and /no_think, and stable thinking-budget control.
- Qwen states the family supports 119 languages and dialects and was trained on about 36T tokens.

CEO takeaway:
- Qwen3-30B-A3B is one of the best-looking local benchmark candidates for a serious CEO prototype.
- Mid-size Qwen3 dense models are also good candidates for low-latency assistant roles.

### DeepSeek-V3 and DeepSeek-R1

Why they matter:
- DeepSeek is the clearest public case study in aggressive reasoning progress plus efficiency-oriented architecture work.
- Even when the full models are too large for a Mac mini, their ideas are directly useful.

Best features of V3:
- MoE with 671B total parameters but only 37B activated per token.
- Multi-head Latent Attention (MLA).
- Auxiliary-loss-free load balancing.
- Multi-Token Prediction (MTP), which also helps speculative decoding.
- FP8 mixed-precision training at scale.

Best features of R1:
- RL-first reasoning research direction.
- Strong self-verification, reflection, and long-chain reasoning behavior.
- Distillation into smaller dense models based on Qwen and Llama.

Efficiency strategies to copy:
- Distill reasoning from a larger reasoning model into smaller deployable models.
- Use MTP/speculative-decoding-style thinking wherever the runtime supports it.
- Treat hardware/software/training co-design as a real multiplier.
- Separate the giant teacher model from the practical production model.

Evidence:
- DeepSeek-V3 explicitly highlights MLA, auxiliary-loss-free load balancing, MTP, and FP8 training.
- DeepSeek-R1 highlights RL without initial SFT for R1-Zero, then a fuller pipeline for R1, plus commercial-use distills in many smaller sizes.

CEO takeaway:
- Learn from DeepSeek's ideas.
- Benchmark the distilled descendants or compatible smaller models, not the full V3/R1 models first.

### Google Gemma 3

Why it matters:
- Gemma 3 looks like one of the strongest "actually run this locally" families for practical deployment.

Best features:
- 128K context.
- Function calling and structured outputs.
- Strong multilingual reach.
- Official quantized releases.
- Framing around single-accelerator deployment.

Efficiency strategies to copy:
- Release quantized models as first-party artifacts, not just community afterthoughts.
- Treat on-device performance as part of the core product promise.
- Keep a small number of sizes with clear hardware-fit stories.

Evidence:
- Google says Gemma 3 is intended to run on a single GPU or TPU.
- Google highlights official quantized versions, 128K context, function calling, and structured outputs.

CEO takeaway:
- Gemma 3 is a top-tier early benchmark candidate for a local CEO assistant.

### Mistral Small 3.1, Devstral 2, Devstral Small 2, Codestral

Why they matter:
- Mistral is consistently strong where local and enterprise deployment practicality matters.
- The Small and Devstral lines are especially relevant to CEO because they target real local deployment and coding tasks.

Best features:
- Mistral Small 3.1: multimodal, multilingual, 128K context, function calling, practical local footprint.
- Devstral 2 / Small 2: code-agent specialization, strong SWE-bench performance, explicit local-friendly small variant.
- Codestral: code-focused positioning from a vendor that consistently emphasizes deployment practicality.

Efficiency strategies to copy:
- Ship a strong small general model and a strong small code model instead of one overextended generalist.
- Be explicit about real hardware-fit targets.
- Optimize for code-agent tasks, not only generic code completion.

Evidence:
- Mistral says Small 3.1 can run on a single RTX 4090 or a Mac with 32GB RAM.
- Mistral says Devstral Small 2 is deployable locally on consumer hardware.
- Mistral positions Devstral 2 and Small 2 as highly efficient code-agent models relative to much larger competitors.

CEO takeaway:
- Mistral Small 3.1 is a strong general local candidate.
- Devstral Small 2 should be near the top of the coding benchmark list.

### Microsoft Phi-4 family

Why it matters:
- Phi is the clearest reminder that small models can still be serious if the data and post-training are strong.

Best features:
- Small size with strong reasoning specialization.
- High-quality synthetic data emphasis.
- Group query attention in smaller variants.
- Multimodal expansion via mixture-of-LoRAs rather than making everything huge.

Efficiency strategies to copy:
- Data quality and targeted specialization beat naive scale in many local use cases.
- Small subagents are a real design primitive.
- Adapter-based multimodality is an effective way to expand capability without rebuilding the whole stack.

Evidence:
- Microsoft describes Phi-4 as a 14B dense model trained on a blend of synthetic and curated high-quality data.
- Microsoft says Phi-4-mini and Phi-4-multimodal are designed to enable advanced AI directly on-device.
- The Phi-4 mini technical report highlights group query attention and multimodal mixture-of-LoRAs.

CEO takeaway:
- Phi-4 and Phi-4-mini are likely better as cheap, fast subagents than as the one flagship CEO model.

## Cross-model feature patterns worth copying into CEO

### 1. Hybrid reasoning budgets

Strong systems no longer assume every task deserves the same amount of thought.

Patterns seen in:
- OpenAI GPT-5 routing
- Claude adaptive/extended thinking
- Gemini Deep Think
- Qwen3 thinking and non-thinking modes
- Grok think variants

CEO implication:
- We should expose at least three effort levels: quick, balanced, deep.
- The model layer should be able to switch both provider and effort budget.

### 2. Context reuse is mandatory

Caching is no longer a niche optimization. It is a core design pattern.

Patterns seen in:
- Anthropic prompt caching with TTL
- Gemini implicit and explicit context caching
- OpenAI cached inputs and model pricing that rewards reuse
- MLX-LM prompt caching
- vLLM automatic prefix caching

CEO implication:
- Static system prompt, tool schemas, vault summaries, and repo summaries should be cacheable prefixes.
- Long-lived sessions should not repeatedly pay full prefill cost.

### 3. Memory should live outside the raw prompt

Patterns seen in:
- Claude memory files
- Claude context compaction
- enterprise doc-grounded workflows in Cohere and Anthropic

CEO implication:
- CEO should persist facts, preferences, repo summaries, and recent task state in explicit memory stores.
- Do not rely on ever-growing chat history.

### 4. Small specialist models matter

Patterns seen in:
- OpenAI mini/nano models
- DeepSeek distilled dense models
- Mistral Small and Devstral Small
- Phi family

CEO implication:
- Use smaller models for extraction, ranking, formatting, lightweight coding helpers, and triage.
- Reserve the stronger model for planning, synthesis, and hard coding tasks.

### 5. Tool use is the product, not just the model

Patterns seen in:
- GPT-4.1 tool support
- Claude 4 tool use and memory behavior
- Grok agent tools
- Cohere enterprise agents
- DeepSeek and Qwen OpenAI-compatible serving guidance

CEO implication:
- The model itself will not be the product moat.
- The moat is model routing + tools + memory + safety gates + task-specific evals.

### 6. Code-specific models are now worth separate evaluation

Patterns seen in:
- Claude Opus/Sonnet dominance in coding workflows
- OpenAI GPT-5.4 and GPT-5.5 emphasis on coding and agentic work
- Devstral 2 / Small 2
- Codestral

CEO implication:
- We should benchmark a general model and a coding-specialized model separately.
- It is plausible that CEO ends up with one general local model and one coding-focused local model.

## The efficiency strategy stack I would copy

If I were designing a local-first CEO stack from this research alone, I would copy these ideas in roughly this order:

1. Provider abstraction
- One interface for hosted and local models.

2. Hybrid reasoning control
- quick / balanced / deep modes
- model- and provider-specific mappings underneath

3. Prefix/context caching
- cache system prompt, tool registry, repo digest, and user profile

4. Memory store plus context compaction
- short-term rolling summary
- task memory
- repo memory
- user preference memory

5. Specialized model roles
- primary assistant
- coding specialist
- cheap extractor/ranker/subagent

6. Quantized local deployment first
- do not benchmark giant BF16 models first
- benchmark realistic local formats first

7. Strong eval loop
- real CEO tasks
- latency
- tool accuracy
- instruction following
- code quality
- hallucination rate

8. Safety gates around high-impact actions
- especially git, shell, file writes, external posting, and network side effects

## What CEO should do next

### Recommended local model shortlist for first benchmarks

General assistant candidates:
- Mistral Small 3.1
- Gemma 3 27B
- Qwen3-30B-A3B
- Qwen3-14B or 32B
- gpt-oss-20b

Coding candidates:
- Devstral Small 2
- gpt-oss-20b
- Qwen3-30B-A3B
- Phi-4 as a lightweight code helper or reviewer

Reasoning/distill candidates:
- DeepSeek-R1-Distill variants
- Qwen3 with thinking enabled

Models to learn from but not benchmark first on a Mac mini style node:
- DeepSeek-V3 full model
- DeepSeek-R1 full model
- Llama 4 Maverick full model
- gpt-oss-120b
- Devstral 2 123B

### Recommended runtime shortlist

For Mac-first local work:
- MLX-LM for Apple Silicon-native loading, quantization, and possible fine-tuning
- Ollama for the fastest API-based local benchmarking loop
- llama.cpp for broad GGUF support and OpenAI-compatible local APIs

For larger NVIDIA server experiments later:
- vLLM for prefix caching and scalable serving
- SGLang if we need stronger support for Qwen/DeepSeek-style reasoning deployments

### Recommended benchmark metrics

Measure these before making architecture decisions:
- first-token latency
- tokens/sec sustained generation
- memory footprint / RAM pressure
- tool-call correctness
- long-context retrieval quality
- code-fix success on repo tasks
- overall answer preference on real CEO tasks
- power / thermal stability for 24/7 operation

### Biggest mistakes to avoid

- Trying to train a new frontier model from scratch.
- Confusing benchmark fame with local deployability.
- Using full giant MoE models as the first local target.
- Shipping without a real eval set.
- Letting the model mutate git or the filesystem without explicit safety gates.

## Practical hypothesis for CEO right now

My current best guess is:
- the best first local general assistant for CEO will come from Qwen3, Gemma 3, or Mistral Small 3.1
- the best first local coding model for CEO will likely be Devstral Small 2 or gpt-oss-20b
- the final system will probably use at least two local models, not one
- MLX-LM plus Ollama or llama.cpp is the most sensible Apple Silicon path

That is a working hypothesis, not a conclusion. We should prove it with benchmarks.

## Resume checklist

When we continue implementation work, do this:
1. Add a provider abstraction to the backend.
2. Keep Gemini as the current hosted provider.
3. Add Ollama as the first local provider.
4. Add benchmark scripts for the shortlist above.
5. Record results in this research folder before committing to one model family.

## Sources checked

Closed models:
- OpenAI GPT-5.5: https://openai.com/index/introducing-gpt-5-5/
- OpenAI GPT-5.4: https://openai.com/index/introducing-gpt-5-4/
- OpenAI GPT-5: https://openai.com/index/introducing-gpt-5
- OpenAI GPT-4.1 API docs: https://developers.openai.com/api/docs/models/gpt-4.1
- Anthropic Claude 4: https://www.anthropic.com/news/claude-4
- Anthropic Claude Sonnet 4.6: https://www.anthropic.com/news/claude-sonnet-4-6
- Anthropic Claude Opus 4.7: https://www.anthropic.com/news/claude-opus-4-7
- Anthropic prompt caching docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Google Gemini 3: https://blog.google/products-and-platforms/products/gemini/gemini-3/
- Gemini context caching docs: https://ai.google.dev/gemini-api/docs/caching/
- xAI Grok 3: https://x.ai/blog/grok-3
- xAI docs overview: https://docs.x.ai/
- Cohere Command A: https://docs.cohere.com/v1/docs/command-a

Open/open-weight models:
- OpenAI gpt-oss release: https://openai.com/index/introducing-gpt-oss/
- OpenAI gpt-oss model docs: https://developers.openai.com/api/docs/models/gpt-oss-120b
- Meta Llama 4 Maverick model card: https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Original
- Meta Llama 4 Scout model card: https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Original
- Qwen3 release: https://qwenlm.github.io/blog/qwen3/
- DeepSeek-V3 repo: https://github.com/deepseek-ai/deepseek-v3
- DeepSeek-R1 model card: https://huggingface.co/deepseek-ai/DeepSeek-R1
- Gemma 3 release: https://blog.google/innovation-and-ai/technology/developers-tools/gemma-3/
- Mistral Small 3.1: https://mistral.ai/news/mistral-small-3-1
- Devstral 2: https://mistral.ai/news/devstral-2-vibe-cli
- Microsoft Phi-4 model card: https://huggingface.co/microsoft/phi-4
- Microsoft Phi family overview: https://azure.microsoft.com/products/phi/

Local serving and efficiency tooling:
- Ollama API introduction: https://docs.ollama.com/api/introduction
- llama.cpp server docs: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- MLX-LM: https://github.com/ml-explore/mlx-lm
- vLLM automatic prefix caching: https://docs.vllm.ai/design/prefix_caching.html

