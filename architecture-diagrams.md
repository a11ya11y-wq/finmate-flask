# FinMate System Diagrams

## 1. High-Level System Architecture

```mermaid
flowchart LR
    user((User))
    browser[Browser]
    user --> browser

    gateway[Nginx Gateway]
    browser -->|HTTPS| gateway

    subgraph Frontend
        fe[React/Vite UI]
    end

    subgraph Backend
        api[Flask API (api-main)]
        celery[Celery Worker]
        report[Report Service (NestJS Worker)]
    end

    subgraph DataStores
        db[(PostgreSQL)]
        redis[(Redis)]
    end

    subgraph External
        monobank[Monobank API]
        spaces[DO Spaces (S3)]
    end

    gateway -->|/| fe
    gateway -->|/api/v1/*| api

    fe -->|REST/JSON| api

    api --> db
    api --> redis

    api -->|background jobs| celery
    celery --> redis
    celery --> db
    celery --> monobank

    api -->|enqueue pdf_task_queue| redis
    report -->|BLPOP pdf_task_queue| redis
    report -->|report_result:*| redis
    report -->|upload PDF| spaces

    fe -->|download PDF| spaces
```

**Description:** The Nginx gateway routes browser traffic to the React frontend and the Flask API. The API handles auth, transactions, budgets, dashboards, monobank sync, and reports, persisting data in PostgreSQL and using Redis for caching, rate limiting, and async coordination. Celery workers execute long-running tasks (e.g., monobank sync) using Redis as broker/result store. The report-service is a separate NestJS worker that consumes report tasks from Redis, generates PDFs with Playwright/Handlebars, uploads them to DO Spaces, and stores the result back in Redis for the API to finalize.

## 2. Specific Data Flow: Report Generation (Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant FE as Frontend (Reports page)
    participant GW as Nginx Gateway
    participant API as Flask API
    participant DB as PostgreSQL
    participant R as Redis
    participant RS as Report Service
    participant S3 as DO Spaces

    U->>FE: Select date range, click "Generate"
    FE->>GW: POST /api/v1/report/generate-pdf
    GW->>API: Route request
    API->>DB: Validate user, create report (PENDING), fetch transactions
    API->>R: RPUSH pdf_task_queue {reportId, user, transactions}
    API-->>FE: 202 {id, status:PENDING}

    loop Poll status
        FE->>GW: GET /api/v1/report/generate-pdf/{id}/status
        GW->>API: Route request
        API->>R: GET report_result:{id}
        alt Not ready
            API-->>FE: 202 {status:PENDING}
        else Success
            API->>DB: Update report status + fileUrl + expire_at
            API-->>FE: 200 {status:PROCESSED, fileUrl}
        else Failed
            API->>DB: Update report status FAILED
            API-->>FE: 400 {status:FAILED, error}
        end
    end

    R->>RS: BLPOP pdf_task_queue
    RS->>RS: Render template + generate PDF (Playwright)
    RS->>S3: Upload PDF
    RS->>R: SETEX report_result:{id} {status, fileUrl}
```

**Description:** The frontend requests a report for a date range. The API validates input, creates a PENDING report record, and enqueues a task in Redis with the transaction payload. The report-service worker consumes the task, renders the PDF, uploads it to DO Spaces, and writes a result key to Redis. The frontend polls the API status endpoint; once the result exists, the API finalizes the report in PostgreSQL and returns the file URL, which the frontend opens directly from DO Spaces.
