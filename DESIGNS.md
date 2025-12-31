# Daylytics Backend - High-Level Design

## Overview

Daylytics Backend is a Python FastAPI application that retrieves time tracking data from Toggl Track API and analyzes it. The system consists of three main components: Planning, Retriever, and Analysis.

## Architecture

The application follows an agent-based workflow architecture pattern:

```
┌──────────────▼──────────────────────────┐
│      Plan Agent                         │
│      Determines strategy and workflow   │
│      Returns Workflow with Steps        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Retriever API                      │
│      Fetches activity logs from Toggl   │
│      Returns List[TogglTimeEntry]       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Analyzer Agent                     │
│      Processes activity logs            │
│      Generates artifacts (METRIC/TABLE/TEXT)│
└─────────────────────────────────────────┘
```

## User Flow

### Planning, Retrieval, and Analysis Flow

1. **Plan Agent Determines Strategy**
   - Plan agent receives request parameters (e.g., date range)
   - Analyzes the request and determines the appropriate strategy
   - Returns a `Workflow` object containing:
     - `start`: Name of the first step to execute
     - `graph`: List of `Step` objects, each with:
       - `name`: Step identifier
       - `description`: What the step does
       - `tool`: Tool/API to call (e.g., "get_toggl_track_activity_logs", "create_analysis")
       - `next`: Name of the subsequent step (or None for end)

2. **Retriever API Executes**
   - Calls Toggl Track API to fetch activity logs
   - Returns `List[TogglTimeEntry]` objects

3. **Analyzer Agent Processes Data**
   - Analyzer agent receives activity logs
   - Processes `TogglTimeEntry` objects
   - Produces artifacts based on the analysis mode:
     - **METRIC**: Quantitative metrics (e.g., ActivityMetric objects)
     - **TABLE**: Structured tabular data
     - **TEXT**: Natural language summary or description

4. **Response**
   - Returns the final analysis results

## Components

### Agents (`app/agents/`)
- **planner_agent.py**: Plan agent that determines strategy and returns a Workflow
  - `handle_request()`: Takes request parameter (e.g. user prompt), returns Workflow with Steps
- **analyzers/**: Analyzer agents that process activity logs
  - **metric_generator.py**: Generates various activity metrics (sleep, workout, family, etc.)
  - **table_generator.py**: Generates structured table representations
  - **summarizer.py**: Generates natural language summaries

### Routes (`app/routes/`)
- **analysis.py**: HTTP endpoint handlers
  - `POST /analysis`: Analyze API endpoint - invokes analyzer agent to process activity logs

### Services (`app/services/`)
- **toggl_service.py**: Toggl Track API integration (Retriever)
  - `get_toggl_track_activity_logs()`: Retrieves activity logs from Toggl API
- **workflow_orchestrator.py**: Executes workflow steps in sequence

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
Plan Agent (planner_agent.handle_request)
    - Receives request parameters (user prompt, etc.)
    - Determines strategy
    - Returns Workflow with Steps
    ↓
Retriever API
    - Calls toggl_service.get_toggl_track_activity_logs()
    - Fetches activity logs from Toggl Track API
    - Returns List[TogglTimeEntry]
    ↓
Analyzer Agent
    - Receives List[TogglTimeEntry] from Retriever
    - Processes TogglTimeEntry objects
    - Generates artifacts based on mode:
      * METRIC: ActivityMetric objects
      * TABLE: Structured data tables
      * TEXT: Natural language summaries
    ↓
Response
    - Returns final analysis results
```

## Key Design Decisions

1. **Pydantic Models**: Type-safe request/response validation and data structures

## Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **HTTP Client**: httpx (for external API calls)
- **Configuration**: pydantic-settings (type-safe config management)

