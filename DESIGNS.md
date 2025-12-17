# Daylytics Backend - High-Level Design

## Overview

Daylytics Backend is a Python FastAPI application that retrieves time tracking data from Toggl Track API. The system provides a REST API endpoint to fetch daily time entries for analysis.

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
┌──────────────▼──────────────────────────┐
│         Toggl Service                   │
│      toggl_service.py                   │
└─────────────────────────────────────────┘
```

## Request Flow

### CreateAnalysis API Flow

1. **Request Received**
   - Client sends `POST /analysis` with:
     - `StartDate`: Start date for analysis (string)
     - `EndDate`: End date for analysis (string)
     - `ResponseMode`: Output format (TEXT | TABLE | METRIC)
   - Route handler validates request using Pydantic models

2. **Data Retrieval & Processing**
   - `toggl_service` calls Toggl Track API to fetch time entries for the date range
   - Data is processed according to the specified `ResponseMode`
   - Analysis ID (AnalysisRid) is generated

3. **Response**
   - Returns analysis results including:
     - `AnalysisRid`: Unique identifier for the analysis
     - `OutputConfig`: Configuration with S3 output path
       - `S3OutputPath`: S3 path where analysis results are stored

## Components

### Routes (`app/routes/`)
- **analysis.py**: HTTP endpoint handlers
  - `POST /analysis`: Main analysis endpoint

### Services (`app/services/`)
- **analysis_service.py**: Orchestrates the workflow
- **toggl_service.py**: Toggl Track API integration

### Models (`app/models/`)
- **analysis.py**: Request/response models for API
- **toggl.py**: Data models for Toggl API responses

### Configuration (`app/config.py`)
- Centralized settings via Pydantic Settings
- Environment variable support via `.env` file
- Configurable:
  - Toggl API credentials

## Data Flow

```
User Request
    ↓
[POST /analysis] {StartDate, EndDate, ResponseMode}
    ↓
analysis_service.create_analysis()
    ↓
┌─────────────────────────────────────┐
│ toggl_service.get_daily_logs()     │ → Toggl Track API
│    (date range)                     │
│    Process by ResponseMode          │
└─────────────────────────────────────┘
    ↓
Generate AnalysisRid & S3OutputPath
    ↓
Response: {AnalysisRid, OutputConfig: {S3OutputPath}}
```

## Key Design Decisions

1. **Separation of Concerns**: Each service handles one responsibility (Toggl API integration)

2. **Pydantic Models**: Type-safe request/response validation and data structures

3. **Configuration-Driven**: Behavior controlled via environment variables for flexibility

## Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **HTTP Client**: httpx (for external API calls)
- **Configuration**: pydantic-settings (type-safe config management)

