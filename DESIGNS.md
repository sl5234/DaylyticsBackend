# Daylytics Backend - High-Level Design

## Overview

Daylytics Backend is a Python FastAPI application that analyzes time tracking data from Toggl Track, categorizes activities, and emits metrics for monitoring and analysis. The system provides a REST API endpoint to trigger daily analysis workflows.

## Architecture

The application follows a layered architecture pattern:

```
┌─────────────────────────────────────────┐
│         API Layer (Routes)             │
│      POST /analysis                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Service Layer (Orchestration)      │
│      analysis_service.py                │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│ Toggl │ │ Categ │ │Metric │
│Service│ │Service│ │Service│
└───────┘ └───────┘ └───────┘
```

## Request Flow

### CreateAnalysis API Flow

1. **Request Received**
   - Client sends `POST /analysis` with date and optional `use_llm` flag
   - Route handler validates request using Pydantic models

2. **Data Retrieval**
   - `toggl_service` calls Toggl Track API to fetch time entries for the specified date
   - Returns structured `TogglDailyLogs` containing time entries with descriptions, durations, projects, etc.

3. **Categorization**
   - `categorization_service` processes time entries
   - **Rule-based**: Uses predefined rules/keywords to assign categories
   - **LLM-based**: Optionally calls `llm_service` to use AI for intelligent categorization
   - Returns mapping of entry IDs to category names

4. **Metrics Preparation**
   - Aggregates categorized entries into metrics:
     - Total hours per category
     - Overall time distribution
     - Metadata and timestamps

5. **Metrics Emission**
   - `metrics_service` emits metrics to configured backend:
     - **CloudWatch**: Sends metrics to AWS CloudWatch for monitoring/dashboards
     - **CSV**: Writes metrics to local CSV file for analysis
   - Backend selection controlled by `METRICS_BACKEND` configuration

6. **Response**
   - Returns analysis results including:
     - Status
     - Date analyzed
     - Metrics data
     - Category mappings

## Components

### Routes (`app/routes/`)
- **analysis.py**: HTTP endpoint handlers
  - `POST /analysis`: Main analysis endpoint

### Services (`app/services/`)
- **analysis_service.py**: Orchestrates the entire workflow
- **toggl_service.py**: Toggl Track API integration
- **categorization_service.py**: Categorization logic (rules + LLM routing)
- **llm_service.py**: LLM API integration for intelligent categorization
- **metrics_service.py**: Metrics emission (CloudWatch/CSV)

### Models (`app/models/`)
- **analysis.py**: Request/response models for API
- **toggl.py**: Data models for Toggl API responses
- **metrics.py**: Metrics data structures

### Configuration (`app/config.py`)
- Centralized settings via Pydantic Settings
- Environment variable support via `.env` file
- Configurable:
  - Toggl API credentials
  - LLM provider and API keys
  - Metrics backend (CloudWatch vs CSV)
  - CloudWatch region/namespace
  - CSV file paths

## Data Flow

```
User Request
    ↓
[POST /analysis] {date, use_llm}
    ↓
analysis_service.create_analysis()
    ↓
┌─────────────────────────────────────┐
│ 1. toggl_service.get_daily_logs()  │ → Toggl Track API
│    Returns: TogglDailyLogs          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. categorization_service           │
│    - categorize_entries()           │
│    - Routes to rule-based or LLM    │
│    Returns: {entry_id: category}    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. _prepare_metrics_data()          │
│    Aggregates: categories → metrics │
│    Returns: MetricsData              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. metrics_service.emit_metrics()   │
│    Routes to:                        │
│    - emit_to_cloudwatch() OR         │
│    - emit_to_csv()                   │
└─────────────────────────────────────┘
    ↓
Response: {status, date, metrics, categories}
```

## Key Design Decisions

1. **Separation of Concerns**: Each service handles one responsibility (Toggl, categorization, metrics)

2. **Strategy Pattern**: Metrics backend is configurable (CloudWatch vs CSV) without changing service code

3. **Conditional LLM Usage**: LLM categorization is optional, allowing cost control and fallback to rules

4. **Pydantic Models**: Type-safe request/response validation and data structures

5. **Configuration-Driven**: Behavior controlled via environment variables for flexibility

## Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **HTTP Client**: httpx (for external API calls)
- **LLM**: OpenAI SDK (configurable to other providers)
- **Cloud Metrics**: boto3 (AWS SDK for CloudWatch)
- **Configuration**: pydantic-settings (type-safe config management)

