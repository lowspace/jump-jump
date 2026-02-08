# Planning & Design Skills (Plan Mode)

This skills file governs how planning and design discussions work in this repository.
It should be loaded and followed whenever Claude is in **plan mode**.

## Core Principles

- **Planning is about design, not code.** Never write or suggest actual code during planning phases. Focus on design decisions, trade-offs, potential technical approaches, workflows, and architecture.
- **Human controls the pace.** Only the human decides when to move from one planning level to the next. Never jump ahead or skip levels.
- **Stay at the current level.** Until the human explicitly says to move on, remain focused on the current planning level. Drill deeper within that level if needed, but do not escalate or descend to another level on your own.

## Planning Levels (Top-Down)

### Level 1: Overall Blueprint
- What problem are we solving? Why does this project exist?
- What are the high-level goals and non-goals?
- Who are the users or consumers?
- What are the key constraints (time, resources, dependencies, scale)?
- What is the expected end-to-end workflow from the user's perspective?

### Level 2: Overall Architecture
- What are the major components/services/layers?
- How do they relate to each other? (data flow, control flow, dependencies)
- What are the technology choices and why? (frameworks, databases, protocols, etc.)
- What are the trade-offs between alternative architectures?
- How does the system handle cross-cutting concerns? (error handling, logging, config, auth, etc.)

### Level 3: Module Architecture
- What modules/packages/classes make up each major component?
- What is each module's single responsibility?
- How do modules communicate? (interfaces, events, shared state, etc.)
- What are the internal vs. external boundaries?
- What design patterns apply and why?

### Level 4: Detailed Design
- What are the specific inputs and outputs of each function/method?
- What are the function signatures and data structures?
- How do functions correlate and call each other?
- What are the edge cases, error conditions, and validation rules?
- What are the expected behaviors and invariants?
- What testing strategies apply at this level?

## How a Planning Session Works

1. **Start at Level 1** unless the human specifies otherwise.
2. At each level, Claude should:
   - Ask clarifying questions to understand the human's intent.
   - Propose options with clear trade-offs (pros, cons, risks).
   - Summarize decisions made so far before moving on.
   - Flag potential issues or blind spots proactively.
3. **Wait for human approval** before descending to the next level.
4. If the human wants to revisit a higher level, follow them back up without resistance.
5. Keep a running summary of decisions and open questions at each level.

## What Belongs in Planning

- Design diagrams (described in text/markdown)
- Trade-off analyses
- Technology comparisons
- Workflow descriptions
- Responsibility assignments (which module owns what)
- Interface contracts (inputs, outputs, protocols)
- Risk identification and mitigation strategies
- Open questions and assumptions

## Documentation Output

### Folder & Naming Convention
- All level summaries are saved to `code_plan/` at the project root.
- File naming: `{nn}-{descriptive-words}.md` where `nn` is the zero-padded level number.
  - `01-overall-blueprint.md`
  - `02-overall-architecture.md`
  - `03-module-architecture.md`
  - `04-detailed-design.md`

### Workflow
- When the human confirms a level is complete and ready to move on, Claude produces a markdown summary of that level's discussion **before** proceeding to the next level.
- The summary captures:
  - Decisions made
  - Trade-offs considered
  - Open questions resolved
  - Remaining assumptions
- The file is saved to `code_plan/` using the naming convention above.
- These files serve as implementation references — future coding sessions should consult them.

## What Does NOT Belong in Planning

- Actual source code or implementation snippets
- Specific syntax or language-level details
- Debugging or runtime concerns
