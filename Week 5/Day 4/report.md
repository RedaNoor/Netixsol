# CrewAI Comparison Report

## Multi-Agent Collaboration, Roles & Task Delegation

## 1. Objective

The objective of this project was to compare three approaches for completing the same game-sales analysis task:

1. A single-agent workflow.
2. A CrewAI sequential multi-agent workflow.
3. A CrewAI hierarchical multi-agent workflow.

The comparison focuses on output quality, specialization, reliability, latency, token usage, API cost, and implementation complexity.

## 2. Business Task

The crew was designed around a game-sales analysis workflow.

The main task was to analyze game-sales data, identify the highest-performing genres and publishers by total `Global_Sales`, develop an interpretation or strategic angle from the findings, and produce a stakeholder-ready summary.

The workflow was divided into three specialized responsibilities:

```text
Sales Data Analyst
        ↓
Marketing Strategist
        ↓
Report Writer
```

## 3. Agent Roles

### Sales Data Analyst

**Goal:** Query the game-sales data and return accurate numerical findings.

**Responsibilities:**

- Query the game-sales tool.
- Calculate or retrieve total `Global_Sales`.
- Rank genres and publishers.
- Return raw results in a structured format.
- Avoid unsupported interpretation.

### Marketing Strategist

**Goal:** Interpret the validated sales findings and identify useful business or marketing implications.

**Responsibilities:**

- Review the analyst's results.
- Identify meaningful patterns.
- Convert numerical findings into marketing insights.
- Avoid unsupported claims.

### Report Writer

**Goal:** Convert the analysis and strategic findings into a concise stakeholder-ready report.

**Responsibilities:**

- Combine previous task outputs.
- Present findings clearly.
- Maintain a professional business tone.
- Separate factual findings from interpretation.

## 4. Why Multiple Agents?

Specialized agents can outperform one generalist when a workflow contains clearly separated stages such as data retrieval, interpretation, and reporting.

Each agent focuses on one responsibility, making intermediate outputs easier to inspect and reducing overlap.

However, multi-agent execution is not always better. For simple tasks, a single well-designed agent can produce the same result with fewer LLM calls, lower latency, lower token usage, and less implementation complexity.

## 5. Sequential CrewAI Workflow

The sequential workflow uses CrewAI's `Process.sequential`.

```text
Sales Data Analyst
        ↓
Marketing Strategist
        ↓
Report Writer
```

The strategist receives the analyst's output through task context, and the writer receives the outputs required for the final report.

### Advantages

- Clear execution order.
- Easy to understand and debug.
- Strong separation of responsibilities.
- Intermediate outputs can be inspected.
- Suitable for predictable workflows.

### Disadvantages

- Later tasks depend on earlier tasks.
- Poor output formatting can affect downstream tasks.
- Tasks cannot dynamically change the workflow.
- Multiple agents increase token usage compared with a single agent.

## 6. Hierarchical CrewAI Workflow

The hierarchical workflow introduces a manager agent.

```text
                 Manager
                /       \
               ↓         ↓
          Specialist  Specialist
                \       /
                 \     /
                  Review
                    ↓
                  Output
```

The manager delegates work to specialized agents and coordinates the overall execution.

### Advantages

- Dynamic delegation.
- Manager-level coordination.
- Better suited to complex workflows.
- Workers can focus on specialized tasks.
- Manager can review intermediate work.

### Disadvantages

- Higher token usage.
- Higher latency.
- More LLM calls.
- More implementation complexity.
- Additional manager behavior creates another potential failure point.

## 7. Single-Agent Workflow

The single-agent solution performs the complete workflow using one agent.

```text
User Request
     ↓
Single Agent
     ↓
Analysis
     ↓
Interpretation
     ↓
Final Report
```

### Advantages

- Lowest implementation complexity.
- Lowest expected token usage.
- Lowest latency.
- Easier debugging.
- Fewer API calls.

### Disadvantages

- No separation of responsibilities.
- The same agent performs analysis, reasoning, and writing.
- Errors in one stage can affect the final result.
- Less suitable for large workflows requiring independent specialists.

## 8. Comparison

| Approach | Quality | Cost | Latency | Reliability | Complexity | Best Use |
|---|---|---|---|---|---|---|
| Single Agent | Good | Lowest | Lowest | High | Low | Simple tasks |
| Sequential Crew | Very Good | Medium | Medium | High | Medium | Predictable multi-step tasks |
| Hierarchical Crew | Very Good | Highest | Highest | Medium | High | Complex delegated workflows |

## 9. Quality Comparison

| Criterion | Single Agent | Sequential | Hierarchical |
|---|---:|---:|---:|
| Factual grounding | Good | Very Good | Very Good |
| Completeness | Good | Very Good | Very Good |
| Output structure | Good | Very Good | Excellent |
| Role specialization | Low | High | High |
| Delegation | None | Fixed | Dynamic |
| Error isolation | Low | Good | Good |
| Maintainability | High | Good | Medium |

The sequential crew provides a strong balance because each stage has a defined responsibility while the execution flow remains predictable.

The hierarchical crew can provide stronger coordination for larger workflows, but that advantage comes with additional execution overhead.

## 10. Cost and Token Usage

Exact API cost depends on the selected provider, model, prompt size, completion size, and number of tool calls.

The expected relative resource usage is:

```text
Single Agent < Sequential Crew < Hierarchical Crew
```

The single-agent workflow requires the fewest model calls.

The sequential workflow adds specialist calls, while the hierarchical workflow adds manager and delegation calls.

For free-tier APIs, the direct financial cost can remain `$0`, but API quotas, rate limits, and token limits still represent practical resource costs.

## 11. Latency

Expected latency generally follows:

```text
Single Agent
      ↓
Sequential Crew
      ↓
Hierarchical Crew
```

The single-agent workflow has the fewest model interactions.

Sequential execution requires multiple dependent tasks.

Hierarchical execution adds manager delegation and review, increasing processing overhead.

## 12. Reliability

Reliability depends strongly on prompt design and output contracts.

The sequential workflow is reliable when every task clearly specifies the format expected by the next task.

The hierarchical workflow introduces additional coordination logic, so it has more moving parts that can fail.

The single-agent workflow has fewer orchestration components but less separation between stages.

## 13. Output Format Issue and Fix

A key multi-agent issue is that the output of one task may not match the input expectations of the next task.

For example, the data analyst may return a long explanation when the strategist needs structured numerical results.

The analyst prompt was therefore changed to require a predictable format:

```text
Genre Ranking:
1. Genre | Total Global_Sales
2. Genre | Total Global_Sales
3. Genre | Total Global_Sales

Publisher Ranking:
1. Publisher | Total Global_Sales
2. Publisher | Total Global_Sales
3. Publisher | Total Global_Sales

Return the raw numerical results only.
Do not add interpretation.
```

This creates a clearer contract between the analyst and downstream agent.

## 14. Evaluation Criteria

Three success criteria were used:

### Factual Grounding

The output must be based on the game-sales data and contain no unsupported numerical claims.

### Completeness

The final report must contain the required genre and publisher findings, interpretation, and stakeholder-ready summary.

### Tone and Clarity

The final output must use clear, professional language suitable for a business stakeholder.

## 15. Manual Evaluation

| Run | Factual Grounding | Completeness | Tone / Clarity | Overall |
|---|---:|---:|---:|---:|
| Run 1 | 5/5 | 4/5 | 5/5 | 4.7/5 |
| Run 2 | 5/5 | 4/5 | 5/5 | 4.7/5 |
| Run 3 | 4/5 | 5/5 | 5/5 | 4.7/5 |

The main variation between runs came from how agents formatted and interpreted intermediate results.

The explicit output format improved consistency between the analyst and downstream agents.

## 16. Sequential vs. Hierarchical

| Factor | Sequential | Hierarchical |
|---|---|---|
| Execution | Fixed order | Manager controlled |
| Delegation | Explicit in task design | Dynamic |
| Token usage | Medium | High |
| Latency | Medium | High |
| Debugging | Easier | More difficult |
| Control | High | Medium |
| Flexibility | Medium | High |
| Best for | Predictable workflows | Complex workflows |

Sequential execution is preferable when the correct order of operations is already known.

Hierarchical execution is preferable when the manager needs to decide which specialist should work next or when dynamic delegation and review are required.

## 17. Sequential vs. Single Agent

| Factor | Single Agent | Sequential Crew |
|---|---|---|
| Number of agents | 1 | 3 |
| Specialization | Low | High |
| Token usage | Lowest | Higher |
| Latency | Lowest | Higher |
| Implementation | Simple | Moderate |
| Debugging | Easy | Moderate |
| Output structure | Good | Very Good |
| Best use | Simple tasks | Multi-step tasks |

For the game-sales task, the single-agent approach is sufficient for producing a basic answer.

The sequential crew becomes useful when the goal is to demonstrate clear specialization between data analysis, strategy, and reporting.

## 18. Was Multi-Agent Worth the Added Cost?

For this specific task, the sequential multi-agent crew was worth the additional complexity because the workflow naturally separates into data analysis, strategic interpretation, and report writing.

The specialization improved structure and made each stage easier to inspect and evaluate.

The hierarchical approach added more overhead than the task required because the workflow already had a predictable execution order.

A single well-designed agent would be the better production choice if minimizing API usage, latency, and implementation complexity were the primary goals.

## 19. Final Recommendation

Use the following decision rule:

```text
Simple task
    ↓
Single Agent

Predictable multi-step task
    ↓
Sequential Crew

Complex task requiring dynamic delegation/review
    ↓
Hierarchical Crew
```

For the Week 5 Day 4 game-sales project, the recommended approach is **CrewAI Sequential**.

It demonstrates meaningful multi-agent specialization without the unnecessary cost and complexity of hierarchical delegation.

## 20. Conclusion

The comparison shows that more agents do not automatically produce better results.

A single agent provides the lowest cost and latency, while a sequential crew provides stronger specialization and clearer workflow separation.

A hierarchical crew provides the most flexible delegation model but also introduces the highest execution overhead.

For this task, **sequential CrewAI provides the best balance between quality, specialization, reliability, and resource usage**.
