# Daylytics Backend - High-Level Design

## Overview

Daylytics Backend is a Python FastAPI application that retrieves time tracking data from Toggl Track API. The system provides a REST API endpoint to fetch daily time entries for analysis.

## Architecture

The application follows an agent-based workflow architecture pattern:

```
┌─────────────────────────────────────────┐
│      Localhost Doc Page                │
│      User calls StartConversation       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Workflow Orchestrator             │
│      Executes workflow steps            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Plan Agent                         │
│      Determines strategy and workflow   │
│      Returns Workflow with Steps        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Execute Workflow Steps             │
│      - Retriever API (get activity logs)│
│      - Analyze API (analyzer agent)     │
│      - Other steps as defined           │
└─────────────────────────────────────────┘
```

## User Flow

### StartConversation Flow

1. **User Initiates Conversation**
   - User calls `StartConversation` endpoint from localhost documentation page
   - Provides prompt, start date, and end date

2. **Workflow Orchestration Begins**
   - Workflow orchestrator receives the request
   - Kicks off the workflow execution process

3. **Plan Agent Determines Strategy**
   - Calls plan agent with user's prompt and date range
   - Plan agent analyzes the request and determines the appropriate strategy
   - Plan agent returns a `Workflow` object containing:
     - `start`: Name of the first step to execute
     - `graph`: List of `Step` objects, each with:
       - `name`: Step identifier
       - `description`: What the step does
       - `tool`: Tool/API to call (e.g., "toggl_service.get_activity_logs", "analysis.create_analysis")
       - `next`: Name of the subsequent step (or None for end)

4. **Execute Workflow Steps**
   - Workflow orchestrator executes each step in sequence
   - Steps are executed based on the `next` field, starting from the `start` step
   - Common steps include:
     - **Retriever Step**: Calls Toggl Track API to fetch activity logs
     - **Analyze Step**: Calls Analyze API which invokes analyzer agent
       - Analyzer agent processes activity logs
       - Produces artifacts based on the analysis:
         - **TEXT**: Natural language summary or description
         - **TABLE**: Structured tabular data
         - **METRIC**: Quantitative metrics (e.g., ActivityMetric objects)
     - **Other Steps**: Additional steps as defined by the plan agent

5. **Response**
   - Returns the final results from the workflow execution to the user

## Components

### Agents (`app/agents/`)
- **planner_agent.py**: Plan agent that determines strategy and returns a Workflow
  - `handle_request()`: Takes user prompt and date range, returns Workflow with Steps
- **analyzers/**: Analyzer agents that process activity logs
  - **metric_generator.py**: Generates various activity metrics (sleep, workout, family, etc.)

### Routes (`app/routes/`)
- **conversation.py**: Conversation endpoint handlers
  - `POST /conversation/`: StartConversation endpoint - initiates workflow
- **analysis.py**: HTTP endpoint handlers
  - `POST /analysis`: Analyze API endpoint - called by workflow steps to invoke analyzer agent

### Services (`app/services/`)
- **analysis_service.py**: Orchestrates the workflow
- **toggl_service.py**: Toggl Track API integration (Retriever API)
  - `get_activity_logs()`: Retrieves activity logs from Toggl API

### Models (`app/models/`)
- **plan.py**: Workflow and step models
  - `Workflow`: Contains start step name and graph of Steps
  - `Step`: Individual workflow step with name, description, tool, and next step reference
- **analysis.py**: Request/response models for API
- **toggl.py**: Data models for Toggl API responses (`TogglTimeEntry`)
- **activity.py**: Activity metric models (`ActivityMetric`, `Period`, `Unit`)

### Configuration (`app/config.py`)
- Centralized settings via Pydantic Settings
- Environment variable support via `.env` file
- Configurable:
  - Toggl API credentials (encrypted via KMS)
  - AWS KMS key ARN

## Data Flow

```
User calls StartConversation (localhost doc page)
    ↓
Workflow Orchestrator
    ↓
Plan Agent (planner_agent.handle_request)
    - Analyzes user prompt and date range
    - Determines strategy
    - Returns Workflow with Steps
    ↓
Execute Workflow Steps (in sequence)
    ↓
Step 1: Retriever API
    - Calls toggl_service.get_activity_logs()
    - Fetches activity logs from Toggl Track API
    - Returns List[TogglTimeEntry]
    ↓
Step 2: Analyze API (almost definitely present)
    - Calls POST /analysis endpoint
    - Invokes analyzer agent
    - Analyzer processes TogglTimeEntry objects
    - Generates artifacts:
      * TEXT: Natural language summaries
      * TABLE: Structured data tables
      * METRIC: ActivityMetric objects
    ↓
Additional Steps (as defined by plan agent)
    ↓
Response to User
    - Returns final workflow results
```

## Key Design Decisions

1. **Separation of Concerns**: Each service handles one responsibility (Toggl API integration)

2. **Pydantic Models**: Type-safe request/response validation and data structures

3. **Configuration-Driven**: Behavior controlled via environment variables for flexibility

## Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **HTTP Client**: httpx (for external API calls)
- **Configuration**: pydantic-settings (type-safe config management)

