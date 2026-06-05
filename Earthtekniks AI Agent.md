# Earthtekniks AI Agent

---

## 1) Product Vision

Build an AI-driven Industrial Product Intelligence System that helps engineers and industrial users identify, validate, and select technically appropriate products for their applications.

The system combines:

- Natural language understanding
    
- Requirement discovery
    
- Formula-driven engineering reasoning
    
- Deterministic calculations
    
- Engineering validation
    
- Product database retrieval
    
- Explainable recommendations
    

The objective is not merely to retrieve products, but to determine which products satisfy the engineering requirements of a given application.

---

### Vision Statement

Enable users to move from:

```text
Application Need
↓
Engineering Requirements
↓
Validated Constraints
↓
Recommended Products
```

without requiring deep expertise in every underlying engineering discipline.

The system should act as an engineering decision-support platform capable of guiding users through the product selection process while maintaining transparency and technical correctness.

---

### Initial Domain

The first implementation targets:

```text
Industrial Cameras
```

including applications such as:

- Defect inspection
    
- Barcode reading
    
- Presence detection
    
- Dimensional measurement
    
- High-speed inspection
    
- PCB inspection
    
- Packaging inspection
    

The camera domain serves as the initial proving ground for the architecture.

---

### Long-Term Expandability

The architecture must remain domain-agnostic and support future expansion into additional industrial product categories.

Potential domains include:

- Lenses
    
- Lighting
    
- Frame Grabbers
    
- Industrial Sensors
    
- Motion Systems
    
- Robotics
    
- Vision Controllers
    
- Optics
    
- Automation Components
    

Future domains should be integrated by adding:

- Domain knowledge
    
- Formula metadata
    
- Engineering calculation tools
    
- Product databases
    

without requiring changes to the core architecture.

---

### System Capabilities

The system should be capable of:

#### Requirement Discovery

Transform vague user requests into structured engineering requirements.

Example:

> Need a camera for inspecting moving bottles.

↓

```json
{
  "application": "bottle_inspection",
  "object_speed": 1000,
  "feature_size": 0.05
}
```

---

#### Engineering Analysis

Determine:

- What engineering problems exist
    
- Which formulas apply
    
- Which calculations are required
    
- Whether requirements are technically feasible
    

Example:

```json
{
  "required_resolution_mp": 12,
  "minimum_fps": 120
}
```

---

#### Product Retrieval

Identify products satisfying engineering constraints.

Example:

```json
{
  "resolution_mp": {
    "$gte": 12
  },
  "fps": {
    "$gte": 120
  }
}
```

↓

```json
[
  {
    "model": "Camera A"
  },
  {
    "model": "Camera B"
  }
]
```

---

#### Recommendation Generation

Explain why a product is suitable.

Example:

> Camera A is recommended because it satisfies the required resolution, exceeds the required frame rate, and provides additional performance margin for future expansion.

---

### Design Goals

The system must be:

#### Deterministic

Engineering calculations should be tool-driven and reproducible.

The same inputs should always produce the same engineering outputs.

---

#### Explainable

Every recommendation should be traceable.

The system should be able to explain:

- Why a product was selected
    
- Which calculations were performed
    
- Which requirements were used
    
- Which constraints eliminated alternatives
    

---

#### Human-in-the-Loop

The system should actively identify missing information and request clarification when necessary.

It should prefer:

```text
Ask
↓
Calculate
```

over:

```text
Assume
↓
Calculate
```

---

#### Extensible

New product domains should be added without redesigning the architecture.

The Router, State, and capability-agent model should remain unchanged as the system grows.

---

#### Auditable

All important decisions should be stored in State.

At any point the system should be able to reconstruct:

```text
User Request
↓
Requirements
↓
Engineering Problems
↓
Formula Selection
↓
Calculations
↓
Constraints
↓
Products
↓
Recommendation
```

---

### What This System Is Not

This system is not:

- A generic chatbot
    
- A product catalog browser
    
- A keyword search engine
    
- A pure LLM recommendation system
    

Those approaches either lack engineering reasoning or lack deterministic validation.

---

### What This System Is

This system is an engineering decision-support platform built around:

- Router-controlled workflows
    
- Shared-state architecture
    
- Formula-driven requirement discovery
    
- Deterministic engineering calculations
    
- Read-only product intelligence
    
- Explainable recommendations
    

Its purpose is to help users move from incomplete application requirements to technically justified product recommendations through a transparent and auditable engineering workflow.

---
## 2) Core Problem

Industrial product selection is fundamentally different from consumer product search.

In consumer search, users typically know what they want.

Examples:

- iPhone 16 Pro
    
- 55-inch TV
    
- Gaming laptop under $1000
    

The search problem is primarily retrieval.

Industrial engineering problems are different.

Users often know their application but do not know the technical specifications required to solve it.

Example:

> “I need a cheap camera to capture fast moving small bottles.”

This statement is not sufficient for product selection.

Important engineering information is missing:

- What inspection task is being performed?
    
- What is the object speed?
    
- What is the smallest feature that must be detected?
    
- What field of view is required?
    
- What level of image quality is acceptable?
    

Without these details, selecting a product becomes guesswork.

---

### Why Traditional Search Fails

Traditional search systems rely on explicit specifications.

Example:

```text
5 MP Camera
120 FPS
Global Shutter
```

These systems perform well when the user already knows the required specifications.

However, most industrial users begin with application requirements rather than technical specifications.

Example:

> Detect scratches on moving bottles.

A search engine cannot determine:

- Required resolution
    
- Required frame rate
    
- Required exposure time
    
- Required sensor characteristics
    

because these values must first be calculated.

---

### Why Pure Database Systems Fail

A database can retrieve products.

It cannot determine what products should be retrieved.

Example:

```text
SELECT *
FROM cameras
WHERE resolution_mp >= 5
```

The database can execute the query.

The database cannot determine:

- Why 5 MP is required
    
- Whether 5 MP is sufficient
    
- Which formula should be used
    
- What engineering assumptions are involved
    

Databases retrieve information.

They do not perform engineering reasoning.

---

### Why Pure LLM Systems Fail

Large Language Models can reason about engineering concepts.

However, they are not deterministic engineering systems.

Example:

User:

> Need a camera to detect a 0.05 mm defect across a 500 mm field of view.

A pure LLM may:

- Estimate requirements
    
- Invent specifications
    
- Apply incorrect formulas
    
- Produce inconsistent outputs
    

The same question may produce different answers across executions.

For engineering decisions, this behavior is unacceptable.

Engineering calculations must be:

- Deterministic
    
- Reproducible
    
- Verifiable
    
- Traceable
    

---

### The Real Problem

The real challenge is not finding products.

The real challenge is transforming vague application requirements into validated engineering constraints.

The system must:

```text
Application Need
↓
Requirement Discovery
↓
Engineering Problem Identification
↓
Formula Selection
↓
Input Collection
↓
Engineering Calculation
↓
Constraint Generation
↓
Product Search
↓
Recommendation
```

Only after engineering constraints are known can product selection begin.

---

### Example Workflow

User:

> Need a camera for detecting scratches on bottles moving at 1 m/s.

Requirement Agent:

```json
{
  "engineering_problem": [
    "motion_blur",
    "resolution_requirement"
  ]
}
```

Requirement Agent determines:

```json
{
  "required_inputs": [
    "feature_size",
    "field_of_view",
    "object_speed"
  ]
}
```

After collecting inputs:

Domain Agent calculates:

```json
{
  "required_resolution_mp": 12,
  "minimum_fps": 120,
  "maximum_exposure_us": 50
}
```

SQL Agent retrieves products satisfying those constraints.

General Agent explains the recommendation.

The recommendation is therefore based on engineering requirements rather than guesses.

---

### System Approach

The system combines:

- AI-driven requirement understanding
    
- Formula-driven engineering calculations
    
- Deterministic validation
    
- Database-backed product retrieval
    
- Explainable recommendations
    

Each capability solves a different part of the problem:

|Problem|Capability|
|---|---|
|Understand user requirements|Requirement Agent (RU)|
|Perform engineering reasoning|Domain Agent (DA)|
|Retrieve products|SQL Agent (SQA)|
|Explain results|General Agent (GA)|
|Orchestrate workflow|Router / Supervisor Agent (SA)|

---

### Goal

The goal of the system is not to answer questions.

The goal is to guide users from incomplete application requirements to validated engineering constraints and ultimately to technically justified product recommendations.

The system acts as an engineering decision-support platform rather than a traditional chatbot or search engine.

---
## 3) Design Philosophy

The MVP follows a **Router-Centric Architecture**.

The Router / Supervisor Agent (SA) is the only orchestration authority in the system.

Every other component is a specialized capability agent.

The Router decides:

- What the user is trying to achieve
    
- Which capability should execute next
    
- Whether execution should continue
    
- Whether execution should pause
    
- Whether recovery is required
    
- When a workflow is complete
    

All business logic is executed by capability agents, but all workflow decisions remain with the Router.

---

### Core Principles

#### 3.1 Single Decision Maker

The Router is the only component allowed to make workflow decisions.

Example:

```text
User Request
↓
Router
↓
Requirement Agent
↓
Router
↓
Domain Agent
↓
Router
↓
SQL Agent
↓
Router
↓
General Agent
↓
Router
↓
User
```

This creates a single source of orchestration truth.

---

#### 3.2 Specialized Capability Agents

Each capability agent owns exactly one domain of responsibility.

|Agent|Responsibility|
|---|---|
|Requirement Agent (RU)|Requirement extraction and formula discovery|
|Domain Agent (DA)|Engineering reasoning and calculations|
|SQL Agent (SQA)|Product retrieval from external databases|
|General Agent (GA)|Communication, ranking, and explanations|

Each agent should be independently understandable and testable.

---

#### 3.3 Shared State Architecture

State is the communication layer of the system.

Agents do not communicate directly.

Instead:

```text
Agent
↓
State Update
↓
Router
↓
Next Agent
```

This ensures that all information is visible, traceable, and recoverable.

---

#### 3.4 No Agent-to-Agent Communication

Capability agents are prohibited from calling other capability agents.

Invalid:

```text
RU
↓
DA
```

Invalid:

```text
DA
↓
SQA
```

Valid:

```text
RU
↓
Router
↓
DA
```

Valid:

```text
DA
↓
Router
↓
SQA
```

This prevents hidden workflows and implicit dependencies.

---

#### 3.5 Clear Ownership

Every important responsibility must have a single owner.

Examples:

```text
Requirement Discovery
↓
RU
```

```text
Formula Execution
↓
DA
```

```text
Database Access
↓
SQA
```

```text
User Communication
↓
GA
```

```text
Workflow Decisions
↓
Router
```

No responsibility should be shared between multiple agents unless explicitly required.

---

#### 3.6 Deterministic Engineering

Engineering decisions should be driven by formulas, metadata, and calculation tools rather than free-form language generation.

Example:

```text
Requirements
↓
Formula Selection
↓
Calculation Tool
↓
Engineering Constraints
```

This reduces hallucinations and improves explainability.

---

#### 3.7 Human-In-The-Loop First

The system should prefer asking for missing information over making unsupported assumptions.

Example:

```text
Missing Input
↓
Router
↓
GA Generates Question
↓
Router
↓
User
```

Assumptions should be explicit and traceable when introduced.

---

#### 3.8 Explainability by Design

Every decision should be recoverable from State.

The system should always be able to answer:

- What information was provided?
    
- Which formula was used?
    
- What calculation was performed?
    
- Why was a product selected?
    
- Why was a product rejected?
    

No important decision should exist only inside prompts or agent memory.

---

#### 3.9 Read-Only Product Intelligence

For the MVP, the system is a recommendation platform, not a database management platform.

The SQL Agent is restricted to:

```text
SELECT
FILTER
SORT
AGGREGATE
```

The system never modifies product data.

This reduces risk and simplifies auditing.

---

#### 3.10 Fail-Safe Execution

When uncertainty is detected, execution should stop and request clarification.

Examples:

```text
Missing Information
↓
Pause
```

```text
Contradictory Requirements
↓
Pause
```

```text
Formula Ambiguity
↓
Clarify
```

```text
Database Failure
↓
Recover
```

The system should prefer safe interruption over incorrect recommendations.

---

### Architectural Flow

```text
User
↓
Router
↓
Capability Agent
↓
State Update
↓
Router
↓
Capability Agent
↓
State Update
↓
Router
↓
General Agent
↓
State Update
↓
Router
↓
User
```

The architecture is intentionally designed around:

- Centralized orchestration
    
- Specialized capabilities
    
- Shared state communication
    
- Deterministic engineering logic
    
- Explainable decision making
    
- Human-in-the-loop execution
    

This keeps the MVP simple, debuggable, extensible, and suitable for engineering decision-support workflows.

---
## 4) High-Level Architecture

```text
                    User
                      ↑
                      ↓
        Router / Supervisor Agent (SA)
                      ↕
                    State

    ├── Requirement Understanding Agent (RU)
    │       • Requirement Extraction
    │       • Engineering Problem Detection
    │       • Formula Selection
    │       • Missing Input Detection
    │
    ├── Domain Agent (DA)
    │       • Domain Knowledge RAG
    │       • Calculation Tools
    │       • Engineering Validation
    │       • Constraint Generation
    │
    ├── SQL Agent (SQA)
    │       • Schema Knowledge
    │       • SQL Generation
    │       • Read-Only Database Access
    │       • Product Retrieval
    │
    └── General Agent (GA)
            • Recommendation Ranking
            • Explanation Generation
            • HITL Message Generation
            • Error Explanation
            • User-Friendly Formatting
```

### External Resources

```text
Requirement Agent
        ↓
Formula Metadata Registry

Domain Agent
        ↓
Domain Knowledge RAG
Calculation Tools

SQL Agent
        ↓
External Database
(PostgreSQL / Supabase / MySQL)

General Agent
        ↓
Response Templates
Communication Rules
```

### Capability Boundaries

**Requirement Understanding Agent (RU)**

Owns:

- Requirement extraction
    
- Formula identification
    
- Required input discovery
    
- Missing input detection
    
- Requirement updates
    
- Contradiction detection
    

Does not:

- Execute formulas
    
- Search databases
    
- Rank products
    

---

**Domain Agent (DA)**

Owns:

- Domain knowledge retrieval
    
- Formula execution
    
- Engineering calculations
    
- Feasibility validation
    
- Search constraint generation
    

Does not:

- Determine missing inputs
    
- Ask users questions
    
- Search databases
    

---

**SQL Agent (SQA)**

Owns:

- SQL generation
    
- Query validation
    
- Read-only database access
    
- Product retrieval
    

Does not:

- Perform engineering reasoning
    
- Rank products
    
- Generate explanations
    

---

**General Agent (GA)**

Owns:

- Product ranking
    
- Recommendation explanations
    
- HITL message generation
    
- Error explanations
    
- User-facing formatting
    
- General conversational responses
    

Does not:

- Perform calculations
    
- Access databases
    
- Make routing decisions
    

---

### Communication Model

```text
User
 ↓
Router
 ↓
Agent
 ↓
State Update
 ↓
Router
 ↓
Next Agent
 ↓
State Update
 ↓
Router
 ↓
General Agent
 ↓
Router
 ↓
User
```

No agent communicates directly with another agent.

No agent communicates directly with the user.

The Router is the only orchestration and communication authority in the system.

### MVP Capability Set

The MVP is complete with only four capability agents:

1. Requirement Understanding Agent (RU)
    
2. Domain Agent (DA)
    
3. SQL Agent (SQA)
    
4. General Agent (GA)
    

coordinated by a single Router / Supervisor Agent and a shared State.

---
## 5) Global State

### Purpose

The State is the single source of truth for the entire system.

Every capability:

- Reads from State
    
- Writes to State
    
- Returns control to the Router
    

No capability communicates directly with another capability.

No important information exists outside State.

This ensures:

- Traceability
    
- Debuggability
    
- Reproducibility
    
- Explainability
    

At any moment, the entire workflow should be reconstructable from State alone.

---

### State Structure

```json
{
  "user_input": "",

  "domain": "camera",

  "intent": null,

  "requirements": {},

  "engineering_problem": [],

  "candidate_formulas": [],

  "required_inputs": [],

  "missing_inputs": [],

  "updates": {},

  "conflicts": [],

  "engineering": {},

  "filters": {},

  "products": [],

  "ranked_products": [],

  "response": "",

  "workflow_status": "",

  "errors": []
}
```

---

### State Sections

#### 5.1 User Context

Stores the latest user request.

Example:

```json
{
  "user_input": "Need a camera for bottle inspection"
}
```

---

#### 5.2 Intent

Stores the Router's understanding of the user's objective.

Example:

```json
{
  "intent": "recommendation"
}
```

Future:

```json
{
  "intents": [
    "recommendation",
    "concept_explanation"
  ]
}
```

---

#### 5.3 Requirements

Stores structured information extracted by the Requirement Agent.

Example:

```json
{
  "requirements": {
    "application": "bottle_inspection",
    "feature_size_mm": 0.05,
    "object_speed_mm_s": 1000,
    "budget": "low"
  }
}
```

These are user-supplied or confirmed values.

---

#### 5.4 Engineering Problem

Stores the engineering objectives identified by RU.

Example:

```json
{
  "engineering_problem": [
    "motion_blur",
    "resolution_requirement"
  ]
}
```

---

#### 5.5 Candidate Formulas

Stores formulas selected by RU.

Example:

```json
{
  "candidate_formulas": [
    "required_sensor_resolution",
    "maximum_exposure_time"
  ]
}
```

These are selected but not yet executed.

---

#### 5.6 Required Inputs

Stores all inputs required by the selected formulas.

Example:

```json
{
  "required_inputs": [
    "field_of_view_mm",
    "feature_size_mm",
    "object_speed_mm_s"
  ]
}
```

---

#### 5.7 Missing Inputs

Stores inputs still required before calculations can proceed.

Example:

```json
{
  "missing_inputs": [
    "object_speed_mm_s"
  ]
}
```

The Router uses this to determine whether HITL interaction is required.

---

#### 5.8 Requirement Updates

Stores detected corrections to existing requirements.

Example:

```json
{
  "updates": {
    "object_speed_mm_s": {
      "old": 1000,
      "new": 2000
    }
  }
}
```

Used for confirmation workflows.

---

#### 5.9 Conflicts

Stores contradictory information detected by RU or the Router.

Example:

```json
{
  "conflicts": [
    {
      "field": "object_speed_mm_s",
      "values": [
        1000,
        2000
      ]
    }
  ]
}
```

Execution pauses until resolved.

---

#### 5.10 Engineering Outputs

Stores results generated by the Domain Agent.

Example:

```json
{
  "engineering": {
    "required_resolution_mp": 5,
    "minimum_fps": 120,
    "maximum_exposure_us": 50,
    "feasible": true
  }
}
```

These are authoritative engineering constraints.

---

#### 5.11 Database Filters

Stores search constraints generated by the Domain Agent.

Example:

```json
{
  "filters": {
    "resolution_mp": {
      "$gte": 5
    },
    "fps": {
      "$gte": 120
    }
  }
}
```

These are passed to the SQL Agent.

---

#### 5.12 Product Results

Stores products returned by the SQL Agent.

Example:

```json
{
  "products": [
    {
      "id": 101,
      "model_name": "Camera A",
      "resolution_mp": 8
    },
    {
      "id": 102,
      "model_name": "Camera B",
      "resolution_mp": 12
    }
  ]
}
```

Raw database results are stored here.

---

#### 5.13 Ranked Products

Stores recommendation results generated by the General Agent.

Example:

```json
{
  "ranked_products": [
    {
      "model_name": "Camera B",
      "score": 94
    },
    {
      "model_name": "Camera A",
      "score": 88
    }
  ]
}
```

These represent recommendation outputs.

---

#### 5.14 Response

Stores the final user-facing response generated by the General Agent.

Example:

```json
{
  "response": "Camera B is recommended because..."
}
```

The Router ultimately sends this to the user.

---

#### 5.15 Workflow Status

Tracks the current execution state.

Example values:

```json
{
  "workflow_status": "collecting_requirements"
}
```

```json
{
  "workflow_status": "awaiting_user_input"
}
```

```json
{
  "workflow_status": "performing_calculations"
}
```

```json
{
  "workflow_status": "searching_products"
}
```

```json
{
  "workflow_status": "completed"
}
```

This allows the Router to resume workflows safely.

---

#### 5.16 Errors

Stores all recoverable system errors.

Example:

```json
{
  "errors": [
    {
      "source": "DA",
      "error_type": "calculation_failure"
    },
    {
      "source": "SQA",
      "error_type": "connection_failure"
    }
  ]
}
```

Errors are never lost and remain available for recovery logic.

---

### State Ownership

```text
Router / Supervisor Agent
    ↓
intent
workflow_status

Requirement Understanding Agent
    ↓
requirements
engineering_problem
candidate_formulas
required_inputs
missing_inputs
updates
conflicts

Domain Agent
    ↓
engineering
filters

SQL Agent
    ↓
products

General Agent
    ↓
ranked_products
response
```

Every state field has a clear owner, preventing ambiguity and accidental overwrites.

---

### State Lifecycle

```text
User Input
↓
Intent
↓
Requirements
↓
Engineering Problems
↓
Formula Selection
↓
Required Inputs
↓
Engineering Outputs
↓
Search Filters
↓
Products
↓
Ranked Products
↓
Response
```

The State represents the complete execution history of the recommendation workflow and acts as the backbone of the entire system.

---
## 6) Router / Supervisor Agent (SA)

### Purpose

The Router is the orchestration layer of the system.

It is responsible for deciding:

- What the user is trying to achieve
    
- What information is currently available
    
- What capability should execute next
    
- Whether execution should continue, pause, recover, or terminate
    

The Router does not perform domain work.

It never:

- Performs engineering calculations
    
- Executes formulas
    
- Searches databases
    
- Ranks products
    
- Explains recommendations
    

Its only responsibility is workflow management.

---

### Responsibilities

#### 6.1 Understand Intent

Determine the user's objective.

Possible intents include:

- Product recommendation
    
- Product search
    
- Engineering validation
    
- Concept explanation
    
- Requirement update
    
- Requirement correction
    
- Workflow continuation
    

Examples:

**Recommendation**

> Need a camera for bottle inspection

```json
{
  "intent": "recommendation"
}
```

**Concept Question**

> What is motion blur?

```json
{
  "intent": "concept_explanation"
}
```

**Engineering Validation**

> Can a 2 MP camera detect a 0.05 mm defect?

```json
{
  "intent": "engineering_validation"
}
```

**Requirement Update**

> Actually the conveyor speed is 2000 mm/s

```json
{
  "intent": "requirement_update"
}
```

The Router determines the intent before selecting any capability.

---

#### 6.2 Detect Context Switching

The Router must determine whether a user message is:

- Answering a pending question
    
- Updating an existing requirement
    
- Asking a new question
    
- Starting a completely new task
    

Example:

System:

> What is the smallest defect size?

User:

> 0.1 mm

Router:

```json
{
  "message_type": "answer"
}
```

Example:

System:

> What is the smallest defect size?

User:

> What is a line scan camera?

Router:

```json
{
  "message_type": "new_request"
}
```

The Router must prevent unrelated messages from accidentally modifying an active workflow.

---

#### 6.3 Inspect State

The Router continuously evaluates State.

It determines:

- What is known
    
- What is unknown
    
- What is confirmed
    
- What requires validation
    
- What capability should execute next
    

Example:

```json
{
  "application": "bottle_inspection",
  "object_speed": 1000,
  "feature_size": null
}
```

Router determines:

```json
{
  "missing": [
    "feature_size"
  ]
}
```

Execution cannot proceed.

The Router routes back to RU.

---

#### 6.4 Evaluate Workflow Status

The Router determines whether the workflow is:

- Collecting requirements
    
- Ready for calculation
    
- Ready for database search
    
- Ready for recommendation
    
- Waiting for user input
    
- Completed
    
- Failed
    

Example:

```json
{
  "missing": []
}
```

and

```json
{
  "required_inputs_available": true
}
```

Router concludes:

```json
{
  "next_step": "EL"
}
```

---

#### 6.5 Route Execution

The Router selects the next capability.

Examples:

**Concept Question**

```text
Router
↓
EL
```

**Recommendation Request**

```text
Router
↓
RU
```

**Product Search**

```text
Router
↓
DB
```

**Recommendation Explanation**

```text
Router
↓
EX
```

The Router does not execute capability logic itself.

It only delegates work.

---

#### 6.6 Manage HITL Interruptions

When required information is missing, the Router pauses execution.

Example:

```json
{
  "missing": [
    "object_speed",
    "feature_size"
  ]
}
```

Router:

```text
Pause Workflow
↓
Ask User
↓
Wait
```

Execution resumes only after user input is received.

This prevents calculations from being performed with incomplete data.

---

#### 6.7 Handle Requirement Updates

The Router must detect when users modify previously supplied information.

Example:

Current State:

```json
{
  "object_speed": 1000
}
```

User:

> Actually it's 2000 mm/s

Router routes to RU.

RU returns:

```json
{
  "updates": {
    "object_speed": {
      "old": 1000,
      "new": 2000
    }
  }
}
```

Router decides whether:

- Confirmation is required
    
- State should be updated
    
- Downstream calculations must be recomputed
    

---

#### 6.8 Handle Contradictions

The Router detects conflicting information.

Example:

```json
{
  "object_speed": 1000
}
```

Later:

```json
{
  "object_speed": 0.1
}
```

The Router must stop execution.

Example:

```text
Conflict Detected
↓
Ask User
↓
Resolve Conflict
↓
Resume Workflow
```

Engineering calculations must not proceed using contradictory values.

---

#### 6.9 Handle Formula Ambiguity

A user request may map to multiple engineering objectives.

Example:

> Need a lens for a large field of view

Possible formula groups:

```json
[
  "lens_selection",
  "working_distance_geometry",
  "sensor_geometry"
]
```

The Router requests clarification before allowing EL execution.

Example:

> Are you selecting a lens, selecting a camera, or designing a complete imaging setup?

After clarification:

```text
Router
↓
RU
↓
EL
```

---

#### 6.10 Handle Multi-Intent Requests

A single message may contain multiple intents.

Example:

> Recommend a camera and explain line scan cameras

Router output:

```json
{
  "intents": [
    "recommendation",
    "concept_explanation"
  ]
}
```

The Router determines whether:

- Both intents can be processed independently
    
- One intent depends on another
    
- User clarification is required
    

For MVP, independent intents may be executed sequentially.

---

#### 6.11 Handle Recovery

The Router is responsible for recovery decisions.

Examples:

**Database Failure**

```text
DB Error
↓
Retry
```

**No Products Found**

```text
DB
↓
0 Results
↓
EL
↓
Identify Limiting Constraint
↓
User
```

**Missing Information**

```text
EL Cannot Execute
↓
RU
↓
Ask User
```

The Router always determines the recovery path.

---

#### 6.12 Determine Completion

The Router determines when the workflow is complete.

Completion occurs when:

- Required information has been collected
    
- Engineering calculations are complete
    
- Product search is complete
    
- Recommendations have been generated
    
- Explanations have been generated
    

Example:

```json
{
  "requirements_complete": true,
  "engineering_complete": true,
  "products_found": true,
  "recommendation_generated": true
}
```

Router:

```text
Return Final Response
↓
Mark Workflow Complete
```

---

### Router Decision Hierarchy

For every message the Router follows the same process:

```text
User Message
↓
Intent Detection
↓
Context-Switch Detection
↓
State Inspection
↓
Workflow Status Evaluation
↓
Select Next Capability
↓
Execute Capability
↓
Inspect Result
↓
Continue
Pause
Recover
or Complete
```

The Router remains the single orchestration authority for the entire system.

---
## 7) Requirement Understanding (RU)

### Purpose

Convert user language into structured engineering requirements by identifying the engineering problem and the formulas required to solve it.

This is the interface between human language and engineering reasoning.

RU does **not perform calculations**.

RU determines:

- What engineering objective exists
    
- Which formula family is relevant
    
- Which inputs are required by those formulas
    
- Which inputs are still missing
    

Actual calculations remain the responsibility of Engineering Logic (EL).

---

### Responsibilities

#### 7.1 Extract Requirements

Example:

User:

> “Need a camera for PCB inspection”

Output:

```json
{
  "application": "pcb_inspection"
}
```

---

#### 7.2 Identify Engineering Problem

RU maps the user request to one or more engineering objectives.

Example:

User:

> “Need a camera for fast moving bottles”

RU:

```json
{
  "application": "bottle_inspection",
  "engineering_problem": [
    "motion_blur"
  ]
}
```

Another example:

User:

> “Need a camera to inspect 0.05 mm defects”

RU:

```json
{
  "engineering_problem": [
    "resolution_requirement"
  ]
}
```

---

#### 7.3 Formula Selection

Using engineering metadata, RU determines which formulas may be required.

Example:

```json
{
  "engineering_problem": "motion_blur",
  "candidate_formulas": [
    "maximum_exposure_time"
  ]
}
```

Another example:

```json
{
  "engineering_problem": "small_defect_detection",
  "candidate_formulas": [
    "required_pixel_density",
    "required_sensor_resolution"
  ]
}
```

RU does not execute formulas.

RU only identifies them.

---

#### 7.4 Determine Required Inputs

Each formula contains metadata describing its required inputs.

Example:

```json
{
  "formula": "maximum_exposure_time",
  "required_inputs": [
    "object_speed",
    "allowable_blur"
  ]
}
```

Example:

```json
{
  "formula": "required_sensor_resolution",
  "required_inputs": [
    "field_of_view",
    "feature_size"
  ]
}
```

RU uses this metadata to determine what information must be collected.

---

#### 7.5 Detect Missing Inputs

RU compares:

```text
Known Inputs
vs
Required Inputs
```

and produces:

```json
{
  "missing": [
    "object_speed",
    "allowable_blur"
  ]
}
```

Only inputs required by the selected formulas are considered missing.

This prevents collecting unnecessary information.

---

#### 7.6 Generate User-Friendly Questions

Missing inputs must be translated into questions understandable by engineers and non-engineers.

Example:

```text
feature_size
↓
What is the smallest defect that must be detected?
```

Example:

```text
object_speed
↓
How fast is the object moving?
```

Example:

```text
field_of_view
↓
What area must be visible in a single image?
```

---

### Formula-Centric Requirement Collection

The system does not maintain a fixed list of required fields.

Instead:

```text
User Request
↓
Engineering Problem Detection
↓
Formula Selection
↓
Required Inputs
↓
Missing Inputs
↓
Questions
```

This ensures that requirement collection is driven directly by engineering calculations.

---

### Example

User:

> “Need cheap camera capture fast moving small bottles”

RU may produce:

```json
{
  "application": "bottle_inspection",
  "budget": "low",
  "engineering_problem": [
    "motion_blur"
  ],
  "candidate_formulas": [
    "maximum_exposure_time"
  ],
  "required_inputs": [
    "object_speed",
    "allowable_blur"
  ],
  "missing": [
    "object_speed",
    "allowable_blur"
  ]
}
```

Router then asks:

> How fast are the bottles moving?

> What is the smallest feature or defect that must remain clearly visible?

---

### Example 2

User:

> “Need camera to detect 0.05 mm scratches on a 500 mm wide object”

RU may produce:

```json
{
  "engineering_problem": [
    "resolution_requirement"
  ],
  "candidate_formulas": [
    "required_pixel_density",
    "required_sensor_resolution"
  ],
  "required_inputs": [
    "field_of_view",
    "feature_size"
  ],
  "known_inputs": {
    "field_of_view": 500,
    "feature_size": 0.05
  },
  "missing": []
}
```

Since all required inputs are available:

```text
Router
↓
Engineering Logic
```

---
## 8) Domain Agent (DA)

### Purpose

The Domain Agent is the engineering execution layer of the system.

It owns:

- Domain knowledge retrieval
    
- Formula execution
    
- Engineering calculations
    
- Engineering validation
    
- Constraint generation
    

The Domain Agent does **not** determine what information is required.

The Domain Agent assumes the Requirement Agent has already:

- Identified the engineering problem
    
- Selected the appropriate formula(s)
    
- Collected required inputs
    
- Resolved missing information
    

Its responsibility is to execute engineering logic using the inputs provided.

---

### Responsibilities

#### 8.1 Conceptual Knowledge

Answer engineering and domain-specific questions using domain knowledge.

Examples:

- What is motion blur?
    
- What is field of view?
    
- What is global shutter?
    
- Difference between CCD and CMOS?
    
- What is a line scan camera?
    
- What is telecentricity?
    

Example:

User:

> What is motion blur?

Router:

```text
Router
↓
DA
```

DA retrieves information from Domain Knowledge and returns an explanation.

No calculations are required.

No database access is required.

---

#### 8.2 Input Validation

Before executing a calculation, the Domain Agent verifies that all required inputs are available and usable.

Example:

Input:

```json
{
  "formula": "required_sensor_resolution",
  "inputs": {
    "field_of_view": 500,
    "feature_size": 0.05
  }
}
```

Validation:

```json
{
  "status": "ready"
}
```

Example:

```json
{
  "formula": "required_sensor_resolution",
  "inputs": {
    "field_of_view": 500,
    "feature_size": null
  }
}
```

Output:

```json
{
  "status": "error",
  "error_type": "missing_input",
  "missing": [
    "feature_size"
  ]
}
```

The Router decides how to recover.

---

#### 8.3 Formula Execution

Execute engineering formulas using the inputs provided by the Requirement Agent.

Example:

Input:

```json
{
  "formula": "required_sensor_resolution",
  "inputs": {
    "field_of_view": 500,
    "feature_size": 0.05
  }
}
```

DA invokes the Calculation Tool.

Output:

```json
{
  "required_resolution_mp": 12
}
```

The Domain Agent is the only capability allowed to execute engineering formulas.

---

#### 8.4 Engineering Calculations

Convert validated requirements into measurable engineering thresholds.

Example:

Input:

```json
{
  "object_speed_mm_s": 1000,
  "allowable_blur_mm": 0.05
}
```

Output:

```json
{
  "maximum_exposure_us": 50
}
```

Another example:

Input:

```json
{
  "field_of_view_mm": 300,
  "feature_size_mm": 0.1
}
```

Output:

```json
{
  "required_resolution_mp": 5
}
```

These outputs become engineering requirements for product selection.

---

#### 8.5 Calculation Error Handling

The Domain Agent handles failures during calculation execution.

Example:

Input:

```json
{
  "field_of_view": 0
}
```

Calculation Tool:

```text
Division by Zero
```

DA returns:

```json
{
  "status": "error",
  "error_type": "calculation_failure",
  "message": "Invalid input values"
}
```

The Router determines the recovery strategy.

---

#### 8.6 Engineering Validation

After calculations are complete, the Domain Agent evaluates whether the requirements are technically feasible.

Example:

Input:

```json
{
  "required_resolution_mp": 150,
  "working_distance_mm": 10000
}
```

Output:

```json
{
  "feasible": false,
  "reason": "Required imaging performance exceeds practical industry limits."
}
```

This prevents impossible solutions from reaching database search.

---

#### 8.7 Constraint Validation

Verify that calculated requirements are logically consistent.

Example:

```json
{
  "required_resolution_mp": 12,
  "selected_camera_resolution_mp": 2
}
```

Output:

```json
{
  "valid": false,
  "reason": "Selected camera does not satisfy required resolution."
}
```

Constraint validation ensures engineering consistency before recommendation.

---

#### 8.8 Constraint Generation

Convert engineering outputs into searchable database filters.

Example:

Engineering Output:

```json
{
  "required_resolution_mp": 5
}
```

Generated Filter:

```json
{
  "resolution_mp": {
    "$gte": 5
  }
}
```

Example:

Engineering Output:

```json
{
  "minimum_fps": 120
}
```

Generated Filter:

```json
{
  "fps": {
    "$gte": 120
  }
}
```

These filters are written to State and later used by the Database Agent.

---

#### 8.9 No-Result Analysis

When the Database Agent returns no products, the Domain Agent determines the limiting engineering constraint.

Example:

Database Result:

```json
{
  "products": []
}
```

DA Analysis:

```json
{
  "limiting_constraint": "required_resolution_mp",
  "required": 150
}
```

Example response:

> No products satisfy the requested resolution requirement.

This provides engineering insight instead of a generic failure message.

---

#### 8.10 State Updates

The Domain Agent writes engineering outputs back to State.

Example:

```json
{
  "engineering": {
    "required_resolution_mp": 5,
    "minimum_fps": 120,
    "maximum_exposure_us": 50
  }
}
```

Example:

```json
{
  "filters": {
    "resolution_mp": {
      "$gte": 5
    },
    "fps": {
      "$gte": 120
    }
  }
}
```

These become the authoritative engineering constraints for downstream processing.

---

### Domain Agent Execution Flow

```text
Receive Formula(s) + Inputs
↓
Validate Inputs
↓
Execute Calculation Tool
↓
Generate Engineering Outputs
↓
Validate Feasibility
↓
Generate Search Constraints
↓
Write Results To State
↓
Return Control To Router
```

The Domain Agent is the sole owner of engineering knowledge and formula execution within the system.

---
## 9) SQL Agent (SQA)

### Purpose

The SQL Agent is the data retrieval layer of the system.

Its responsibility is to retrieve products that satisfy engineering constraints generated by the Domain Agent.

The SQL Agent does not perform engineering reasoning.

It does not:

- Execute formulas
    
- Validate engineering feasibility
    
- Select formulas
    
- Rank products
    
- Explain recommendations
    

It only retrieves data from external databases.

For the MVP, the SQL Agent is **read-only** and limited to DQL (Data Query Language) operations.

Supported operations:

- SELECT
    
- Filtering
    
- Sorting
    
- Aggregation (if required)
    

Unsupported operations:

- INSERT
    
- UPDATE
    
- DELETE
    
- Schema modifications
    

The SQL Agent connects to external databases such as:

- PostgreSQL
    
- Supabase
    
- MySQL
    
- Other SQL-compatible systems
    

---

### Responsibilities

#### 9.1 Database Schema Understanding

The SQL Agent understands the product database schema.

Example:

```sql
cameras
```

|Column|Type|
|---|---|
|id|integer|
|model_name|text|
|resolution_mp|float|
|fps|integer|
|sensor_type|text|
|shutter_type|text|
|price|float|

The SQL Agent uses schema knowledge to construct valid queries.

Engineering interpretation remains the responsibility of the Domain Agent.

---

#### 9.2 Query Generation

Convert engineering filters into database queries.

Input:

```json
{
  "resolution_mp": {
    "$gte": 5
  },
  "fps": {
    "$gte": 120
  }
}
```

Generated Query:

```sql
SELECT *
FROM cameras
WHERE resolution_mp >= 5
AND fps >= 120
```

The SQL Agent translates structured filters into executable SQL.

---

#### 9.3 Query Validation

Before execution, the SQL Agent validates generated queries.

Checks include:

- Table existence
    
- Column existence
    
- SQL syntax validity
    
- Read-only compliance
    

Example:

```sql
SELECT resolution
FROM cameras
```

If the column does not exist:

```json
{
  "status": "error",
  "error_type": "invalid_column",
  "column": "resolution"
}
```

Execution is blocked.

---

#### 9.4 Query Execution

Execute validated queries against the external database.

Example:

```sql
SELECT *
FROM cameras
WHERE resolution_mp >= 5
```

Example Output:

```json
[
  {
    "model_name": "Camera A",
    "resolution_mp": 8
  },
  {
    "model_name": "Camera B",
    "resolution_mp": 12
  }
]
```

The SQL Agent returns raw product data.

No ranking or recommendation logic is performed.

---

#### 9.5 Result Normalization

Convert database-specific results into a consistent internal format.

Example:

Database Output:

```json
[
  {
    "model_name": "Camera A",
    "resolution_mp": 8
  }
]
```

Normalized Output:

```json
{
  "products": [
    {
      "name": "Camera A",
      "resolution_mp": 8
    }
  ]
}
```

This ensures downstream components receive a predictable structure.

---

#### 9.6 Empty Result Detection

Detect when no products satisfy the requested constraints.

Example:

```json
{
  "products": []
}
```

Output:

```json
{
  "status": "no_results"
}
```

The Router determines the recovery path.

Typically:

```text
Router
↓
DA
↓
Identify Limiting Constraint
```

---

#### 9.7 Database Error Handling

Capture failures occurring during query execution.

Examples:

- Connection failures
    
- Authentication failures
    
- Timeout errors
    
- Query execution errors
    

Example:

```json
{
  "status": "error",
  "error_type": "connection_failure"
}
```

The Router determines whether to:

- Retry
    
- Escalate
    
- Notify the user
    

---

#### 9.8 Read-Only Enforcement

The SQL Agent must enforce read-only database access.

Allowed:

```sql
SELECT *
FROM cameras
```

Blocked:

```sql
DELETE FROM cameras
```

Blocked:

```sql
UPDATE cameras
SET price = 0
```

Blocked:

```sql
DROP TABLE cameras
```

Only retrieval operations are permitted.

---

#### 9.9 State Updates

The SQL Agent writes retrieved products back to State.

Example:

```json
{
  "products": [
    {
      "model_name": "Camera A",
      "resolution_mp": 8
    },
    {
      "model_name": "Camera B",
      "resolution_mp": 12
    }
  ]
}
```

The SQL Agent does not modify:

```json
{
  "requirements": {},
  "engineering": {},
  "filters": {}
}
```

Its responsibility is limited to product retrieval.

---

### SQL Agent Execution Flow

```text
Receive Search Filters
↓
Validate Filters
↓
Generate SQL Query
↓
Validate Query
↓
Execute Against External Database
↓
Normalize Results
↓
Write Products To State
↓
Return Control To Router
```

The SQL Agent is the sole owner of database access and product retrieval within the system. It provides a controlled, read-only interface between the engineering system and external product databases.

---
## 10) General Agent (GA)

### Purpose

The General Agent is the communication and presentation layer of the system.

Its responsibility is to transform system outputs into human-understandable responses.

The General Agent handles:

- Greetings and conversational messages
    
- Product recommendation explanations
    
- Engineering result explanations
    
- Error explanations
    
- Missing information questions
    
- HITL communication generation
    
- User-facing formatting
    

The General Agent does not perform engineering calculations.

It does not:

- Execute formulas
    
- Search databases
    
- Select products
    
- Determine workflow routing
    
- Modify system state decisions
    

The General Agent generates communication only.

The Router remains the only component allowed to interact with the user.

---

### Responsibilities

#### 10.1 General Conversation Handling

Handle simple non-technical interactions.

Examples:

User:

> Hi

Output:

> Hello. How can I help you today?

User:

> Thank you

Output:

> You're welcome.

These interactions do not require engineering or database capabilities.

---

#### 10.2 Product Ranking

Rank retrieved products using deterministic scoring criteria.

Possible factors:

- Requirement fit
    
- Engineering margin
    
- Cost
    
- Availability
    
- Performance headroom
    

Example:

```json
{
  "camera_a_score": 92,
  "camera_b_score": 81
}
```

Output:

```json
{
  "ranked_products": [
    "Camera A",
    "Camera B"
  ]
}
```

The ranking process must remain transparent and explainable.

---

#### 10.3 Recommendation Explanation

Convert engineering outputs and ranking decisions into understandable recommendations.

Example:

Input:

```json
{
  "required_resolution_mp": 5,
  "required_fps": 120
}
```

Product:

```json
{
  "name": "Camera A",
  "resolution_mp": 12,
  "fps": 160
}
```

Output:

> Camera A is recommended because it exceeds the required resolution, supports the required frame rate, and remains within the budget constraint.

The user should always understand why a product was selected.

---

#### 10.4 Engineering Explanation

Translate engineering calculations into plain language.

Example:

Input:

```json
{
  "required_resolution_mp": 12
}
```

Output:

> A minimum resolution of 12 MP is required to reliably detect the specified defect size across the requested field of view.

The explanation should focus on engineering reasoning rather than formulas.

---

#### 10.5 Missing Information Communication

When the Router determines that information is missing, the General Agent generates user-friendly questions.

Input:

```json
{
  "missing": [
    "object_speed_mm_s"
  ]
}
```

Output:

> How fast is the object moving?

Input:

```json
{
  "missing": [
    "feature_size_mm"
  ]
}
```

Output:

> What is the smallest defect or feature that must be visible?

The General Agent converts technical field names into understandable language.

---

#### 10.6 Error Explanation

Convert system errors into user-friendly explanations.

Example:

Input:

```json
{
  "error_type": "calculation_failure"
}
```

Output:

> I could not complete the engineering calculation because one or more input values are invalid.

Example:

```json
{
  "error_type": "database_connection_failure"
}
```

Output:

> The product database is currently unavailable. Please try again later.

The user should never see raw system errors.

---

#### 10.7 Contradiction Resolution Messages

Generate clarification requests when conflicting information exists.

Input:

```json
{
  "field": "object_speed",
  "values": [
    1000,
    2000
  ]
}
```

Output:

> I have two different values recorded for object speed: 1000 mm/s and 2000 mm/s. Which value should I use?

The General Agent generates the clarification.

The Router decides whether clarification is required.

---

#### 10.8 Requirement Update Confirmation

Generate confirmation messages when existing requirements are modified.

Input:

```json
{
  "field": "object_speed",
  "old": 1000,
  "new": 2000
}
```

Output:

> I currently have 1000 mm/s recorded for object speed. Should I update it to 2000 mm/s?

The Router determines whether confirmation is necessary.

The General Agent generates the message.

---

#### 10.9 No-Result Explanations

Convert engineering bottlenecks into understandable explanations.

Input:

```json
{
  "limiting_constraint": "required_resolution_mp",
  "required": 150
}
```

Output:

> No available cameras satisfy the required resolution. The requested inspection task requires approximately 150 MP, which exceeds the capabilities of currently available products.

This provides actionable information instead of a generic failure message.

---

#### 10.10 HITL Communication Generation

The General Agent supports Human-In-The-Loop workflows.

It generates:

- Missing information questions
    
- Clarification requests
    
- Confirmation requests
    
- Contradiction resolution prompts
    
- Recovery prompts
    

Example:

Input:

```json
{
  "action": "request_missing_information",
  "field": "working_distance"
}
```

Output:

> What is the distance between the camera and the object?

The General Agent prepares the communication.

The Router decides when and whether it should be sent.

---

#### 10.11 Response Formatting

Convert internal system outputs into clean user-facing responses.

Input:

```json
{
  "products": [...],
  "engineering": {...},
  "explanations": [...]
}
```

Output:

```text
Recommended Product: Camera A

Why it was selected:
• Meets the resolution requirement
• Exceeds the frame-rate requirement
• Fits within the budget

Alternative Options:
• Camera B
• Camera C
```

The General Agent controls presentation quality and readability.

---

### Router Interaction Rule

The General Agent never communicates directly with the user.

Workflow:

```text
GA
↓
Generated Response
↓
Router
↓
User
```

All user interaction remains controlled by the Router.

This ensures a single communication path throughout the system.

---

### General Agent Execution Flow

```text
Receive Structured Output
↓
Determine Communication Type
↓
Generate User-Friendly Explanation
↓
Format Response
↓
Return Response To Router
↓
Router Decides Whether To Send
```

The General Agent is the sole owner of user-facing communication, explanation generation, recommendation presentation, and HITL message generation within the system. The Router remains the only component responsible for interacting with the user.

---
