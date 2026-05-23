# Paper Outline

## 1. Proposed title

1. **Code Without Authority: Event-Sourced Behavior Drafts for Auditable LLM Self-Modification**
2. **Behavior Drafts as Event-Sourced Self-Modification**
3. **From Self-Modification to Code Promotion: Auditable Capability Addition in Event-Sourced Agents**

**Recommended title:** *Code Without Authority: Event-Sourced Behavior Drafts for Auditable LLM Self-Modification*.

Rationale: it foregrounds the key novelty (authority separation), the mechanism (event-sourced BehaviorDraft lifecycle), and the paper’s scope (auditable, gated self-modification rather than open-ended autonomy).

## 2. One-paragraph thesis

This paper argues that in an event-sourced agent runtime, generated behavior code can be treated as *proposals without authority* until it passes explicit verification gates. In our design, code is first represented as an inert `BehaviorDraft`, then validated by static checks, executed in a forked sandbox, compared against goal-specific semantic diffs, and only promoted when all checks pass. Promoted behavior runs through the same constrained runtime surface used during sandboxing—`behavior(event, graph, ctx)` with read-only graph access and emit-only action context—so authority remains scoped and auditable. Across deterministic A/B/C lifecycle runs, adversarial containment tests, and a narrow two-goal live LLM smoke test, results support lifecycle correctness and containment claims while intentionally not claiming broad reliability, secure arbitrary code execution, or open-ended recursive self-improvement.

## 3. Abstract draft

Event-sourced agent systems provide strong auditability for state transitions, but typical “self-modification” mechanisms in these systems are graph-native and bounded: they can rebind behavior and mutate graph state, yet do not safely authorize new code. We present a BehaviorDraft lifecycle for ActiveGraph that separates code authorship from runtime authority. Candidate behavior is first captured as inert draft data, then passed through static analysis, executed in a forked sandbox, and validated by semantic diff checks against goal-level expectations. Only then can it be promoted to live scoped behavior. Crucially, promoted execution preserves interface parity with sandbox validation: both use `behavior(event, graph, ctx)` with read-only graph access and emit-only context capabilities.

In deterministic lifecycle evaluation (6 runs across conditions A/B/C), we observe the expected progression: no behavior addition in graph-only baseline (A), inert draft validation without live authority (B), and successful gated promotion with matching-event firing, nonmatching silence, and disable semantics (C). In adversarial containment evaluation (29 hand-authored cases), all cases match expected outcomes with 0 unexpected passes, 0 unexpected failures, and 0 live graph violations. In a narrow live LLM authorship smoke test (model: `gpt-4o-mini`, 2 goals), both attempts parse, pass gates, match semantic diffs, and promote successfully. We frame these results as evidence for lifecycle containment and auditable authority transfer, not as evidence of broad model reliability, secure arbitrary code execution, or open-ended recursive self-improvement.

## 4. Contributions

1. **BehaviorDraft abstraction for inert generated code** in an event-sourced runtime.
2. **Explicit separation of authorship and authority**, where generated code remains non-executable in live runtime until gated promotion.
3. **A staged verification lifecycle** combining static analysis, forked sandbox execution, and semantic diff validation before promotion.
4. **Sandbox-to-live runtime parity** via the same callable interface and boundary (`behavior(event, graph, ctx)`, `ReadOnlyGraphView`, `EmitOnlyBehaviorContext`).
5. **Adversarial containment evaluation frame** with categorized rejection paths (static, sandbox/budget, semantic).
6. **A paper-ready measurement scaffold for bounded self-modification**, including deterministic baselines and live authorship smoke-test metrics.

## 5. Paper outline

### 1. Introduction
- Motivate why “code generation” and “code authority” must be decoupled in agent runtimes.
- Identify gap between graph-native self-change and safe code promotion.
- State the paper’s central claim: code without authority until gates pass.
- Preview empirical evidence: deterministic lifecycle, adversarial containment, live smoke test.
- Clarify bounded scope and explicit non-claims.

### 2. Background: ActiveGraph and selfgraph
- Briefly describe ActiveGraph event-sourced architecture and replay/audit properties.
- Explain current selfgraph capability: graph-native self-change and behavior binding.
- Explain limitation: selfgraph is not code authoring authority.
- Define why this limitation is desirable for safety/traceability.

### 3. Design: BehaviorDrafts and code without authority
- Define `BehaviorDraft` object model and lifecycle states.
- Formalize authoring-vs-authority split.
- Describe gating pipeline and failure semantics.
- Explain authority boundary: proposal path vs live execution path.
- Map lifecycle states to auditable events.

### 4. Implementation
- Runtime components: draft storage, static analyzer, sandbox executor, semantic diff validator, promoter.
- Execution contract: `behavior(event, graph, ctx)` callable.
- Capability constraints: `ReadOnlyGraphView`, `EmitOnlyBehaviorContext`.
- Provenance metadata injection and disable behavior.
- Deterministic harness and reproducibility notes.

### 5. Experiments
- Deterministic A/B/C lifecycle design and goals.
- Adversarial corpus design and category definitions.
- Runtime parity checks between sandbox and promoted paths.
- Live LLM smoke test setup (two-goal, narrow scope).
- Metrics collected and pass/fail criteria.

### 6. Results
- A/B/C outcomes showing staged authority progression.
- Gate-wise success/rejection accounting.
- Adversarial containment totals and zero-violation result.
- Runtime parity evidence.
- Live smoke test outcomes and confidence boundaries.

### 7. Discussion
- Interpret results as containment/auditability evidence.
- Practical implications for agent architectures with generated code.
- Why parity matters for trust transfer from sandbox to live runtime.
- What this enables for incremental capability addition.

### 8. Limitations
- Small deterministic corpus and hand-authored adversarial set.
- Pattern-based static analysis limitations.
- Sandbox limitations (not capability-secure/process-isolated).
- Limited live LLM evidence (2 goals).
- No general task-performance claims.

### 9. Related work
- Safe code generation / policy-gated execution systems.
- Event-sourcing and auditable runtime design.
- Sandboxing and capability-based execution literature.
- Agent self-modification frameworks and differences in authority model.

### 10. Conclusion
- Reiterate code-without-authority framing.
- Summarize evidence for bounded, auditable promotion.
- Reaffirm non-claims.
- Point to next experiments for stronger external validity.

## 6. Results section draft

### 6.1 Deterministic lifecycle baseline

We evaluate a 6-run deterministic baseline spanning three conditions (A/B/C) over two goals. Condition **A** (graph-only baseline) demonstrates that without draft/sandbox/promotion, the system does not add new executable behavior. This establishes that baseline graph-native mechanisms alone do not confer code-authoring authority. Condition **B** (draft and sandbox enabled, no promotion) demonstrates that drafts can be created, statically validated, and sandbox-executed while remaining inert with respect to live behavior. Condition **C** (full gated promotion) demonstrates that validated drafts can be promoted into scoped live behavior, fire on matching events, remain silent on nonmatching events, and be disabled back to silence. Together, A/B/C isolate the exact role of each lifecycle stage: no authority (A), validated but inert proposals (B), and bounded authority transfer after gates (C).

### 6.2 Behavior-draft lifecycle gates

The lifecycle enforces a fixed gate sequence: **draft → static analysis → sandbox execution → semantic diff → promotion → disable**. Draft creation captures candidate source as inert data. Static analysis rejects policy-violating code patterns before execution. Sandbox execution runs candidate behavior under constrained interfaces and budgets. Semantic diff validation compares produced graph deltas against goal-specific expected effects, rejecting nonconforming behavior even if syntactically valid and executable. Promotion is only allowed after all prior gates pass; promoted behavior then executes under the same scoped interfaces and can later be disabled. This sequence provides an auditable chain from proposal to authority grant and eventual authority revocation.

### 6.3 Adversarial containment

Adversarial evaluation includes **29 cases**, with **29/29 matching expectation**, **0 unexpected passes**, **0 unexpected failures**, and **0 live graph violations**. Rejections distribute across three containment categories: static-analysis rejection, sandbox/budget rejection, and semantic-diff rejection; benign controls validate that acceptable drafts still pass the pipeline. This distribution is important: containment is not a single gate artifact but layered across policy, execution, and outcome semantics. Observed outcomes support the claim that unauthorized or semantically off-target drafts can be blocked before live authority, while allowed behaviors can still proceed through the same audited lifecycle.

### 6.4 Promoted-runtime parity

A key design requirement is parity between sandbox validation and promoted execution. In this system, both paths use the same callable form `behavior(event, graph, ctx)`, the same `ReadOnlyGraphView` abstraction for graph access, and the same `EmitOnlyBehaviorContext` for action emission. Promoted execution additionally preserves provenance metadata injection and supports explicit disable behavior, preserving audit continuity across lifecycle stages. This parity strengthens the interpretation of sandbox results: promotion does not switch to a broader authority surface than the one validated pre-promotion.

### 6.5 Live LLM authorship smoke test

We include a narrow live authorship smoke test using **`gpt-4o-mini`** over **2 goals**. Outcomes are: **2 attempts**, **2 parsed**, **2 static-analysis passed**, **2 sandbox passed**, **2 semantic diff matched**, **2 promoted**, with **0 parse failures**, **0 static failures**, **0 sandbox failures**, and **0 semantic-diff failures**. Matching-event firing, nonmatching silence, and disable checks also succeed in both promoted runs. We interpret this strictly as a feasibility smoke test for integrating model-authored drafts into the same gated lifecycle; it is not evidence of broad live LLM reliability across tasks, prompts, models, or adversarial prompt conditions.

## 7. Tables to include

### Table 1: Deterministic lifecycle baseline
- **Source artifact:** `results/paper_tables.md` (Table 1), derived from `results/summary.json`.
- **Supports claim:** A/B/C progression cleanly separates no-authority baseline, inert validated drafts, and gated promotion into scoped live behavior.
- **Does not prove:** general utility across broad tasks or model robustness.

### Table 2: Behavior-draft lifecycle gates
- **Source artifact:** `results/paper_tables.md` (Table 2), integrating deterministic and adversarial categories.
- **Supports claim:** gate-by-gate accounting is measurable and auditable.
- **Does not prove:** formal completeness of the gate set against all possible malicious strategies.

### Table 3: Adversarial containment
- **Source artifact:** `results/adversarial_summary.json` and `results/paper_tables.md` (Table 3).
- **Supports claim:** current adversarial corpus is fully contained as expected, with no live graph violations.
- **Does not prove:** security against arbitrary, unseen, or heavily obfuscated attack classes.

### Table 4: Runtime parity / authority boundary
- **Source artifact:** `results/paper_tables.md` (Table 4), backed by parity fields in `results/summary.json`.
- **Supports claim:** sandbox and promoted runtime share constrained source interface and capability boundary.
- **Does not prove:** OS-level isolation or capability-secure execution of arbitrary Python.

### Table 5: Live LLM Authorship Run
- **Source artifact:** `results/live_llm_summary.json` when available; otherwise reported run metrics from current local live run logs/summary.
- **Supports claim:** end-to-end feasibility of model-authored draft passing through gates into scoped promotion for two goals.
- **Does not prove:** broad live LLM reliability, stability across models, or long-horizon behavior quality.

## 8. Figures to include

1. **BehaviorDraft lifecycle diagram**: `goal → draft → static analysis → forked sandbox → semantic diff → promotion → live scoped behavior → disable`.
2. **Authority boundary diagram**: LLM/code authoring outside authority boundary; promotion gate grants scoped runtime authority.
3. **Sandbox vs promoted runtime parity diagram**: shared callable and capability boundary (`behavior(event, graph, ctx)`, read-only graph, emit-only context).
4. **Adversarial containment funnel**: counts rejected at static, sandbox/budget, semantic stages plus benign controls.
5. **Live LLM smoke-test path**: model output to parsed draft to gates to promoted behavior outcomes.

## 9. Claims and non-claims

| Claim | Supported by | Caveat |
|---|---|---|
| Generated behavior can be represented as inert drafts without immediate runtime authority. | Deterministic A/B/C baseline and lifecycle events. | Demonstrated on current harness/goal set only. |
| Multi-gate lifecycle can block policy-violating or semantically invalid drafts before promotion. | 29-case adversarial containment with 29/29 expected outcomes. | Adversarial set is finite and hand-authored. |
| Promoted behavior can run under the same constrained interface used in sandbox validation. | Runtime parity checks and promoted-run fields. | Not a proof of full sandbox/process security. |
| Gated promotion can preserve matching-event fire, nonmatching silence, and disable semantics. | Condition C deterministic runs and benign controls. | Evaluated on limited behaviors/goals. |
| Live model-authored drafts can pass the lifecycle in a narrow smoke test. | Two-goal live `gpt-4o-mini` run with full pass. | Too small to support broad reliability claims. |

### Non-claims
- No claim of open-ended recursive self-improvement.
- No claim of secure arbitrary code execution.
- No claim of full Python sandbox security or strong process isolation.
- No claim of broad task-performance improvements.
- No claim of broad live LLM reliability across models/prompts/domains.

## 10. Limitations

- Live LLM measurement is only two goals.
- Deterministic goal corpus is small.
- Adversarial corpus is hand-authored and finite.
- Static analysis is pattern-based and not formally complete.
- Python sandbox is not capability-secure or process-isolated.
- No broad task-performance benchmark is provided.
- No open-ended recursive self-improvement setting is evaluated.
- Current evidence validates lifecycle correctness and containment, not usefulness at production scale.

## 11. Next experiments needed

### A. Expanded goal corpus
- **Strengthens claim:** external validity of lifecycle correctness across more behavior classes.
- Increase deterministic goals and expected semantic diff templates.

### B. Prompt/schema reliability tuning across more models
- **Strengthens claim:** portability of draft-authoring interface and parse/gate success rates across model families.
- Add per-model parse/static/sandbox/diff pass metrics.

### C. Stronger sandbox isolation
- **Strengthens claim:** containment rigor for execution-stage threats.
- Move toward stricter process isolation/capability controls.

### D. More adversarial obfuscation tests
- **Strengthens claim:** resilience of layered gates against evasive patterns.
- Add metamorphic/obfuscated variants of known attack intents.

### E. Repeated live LLM runs across seeds/models
- **Strengthens claim:** stability and variance characterization for end-to-end live authoring outcomes.
- Track confidence intervals and failure mode taxonomy.

## 12. Recommended next step

**Recommended immediate next step: A. Expanded goal corpus.**

Rationale: the strongest near-term paper improvement is increased external validity of the core lifecycle claim without changing architecture or introducing new safety claims. Expanding deterministic goals with predeclared semantic expectations will stress the same gating pipeline, produce stronger tables, and keep the paper’s central argument focused on bounded, auditable authority transfer.
