# Cloud Architecture Mapping

This document maps each component of the local development setup to its cloud equivalent and explains why each service is appropriate for a production deployment.

---

## 1. Raw Candle Storage — In-Memory → AWS S3 / Azure Blob Storage

Locally, fetched OHLCV candles exist only in memory for the duration of a request. There is no persistence between calls, which means every analysis re-fetches 200 candles from the Binance API. In a production environment this is wasteful and fragile. Moving to object storage — AWS S3 or Azure Blob Storage — would allow candles to be written as Parquet or JSON files partitioned by symbol and interval. Subsequent requests within a short window (e.g. five minutes) could read from the cache instead of hitting Binance, reducing latency and respecting rate limits. Both S3 and Blob Storage are cost-effective for this access pattern: writes are infrequent, reads are small, and neither requires a running compute instance to serve the data.

## 2. Backend Compute — Uvicorn on Localhost → AWS EC2 / Azure VM

The FastAPI application currently runs via `uvicorn` on a developer's machine. In production, the application would be containerised (a `Dockerfile` is already present in the repo) and deployed on a compute instance. An AWS EC2 instance (e.g. `t3.small`) or an Azure Virtual Machine running the Docker container behind a load balancer would provide a stable, addressable endpoint. This mapping is straightforward because the application is already stateless — any instance can serve any request. For better scaling behaviour, the container could instead be deployed to AWS ECS Fargate or Azure Container Apps, which remove the need to manage the underlying VM.

## 3. Signal History Database — None Currently → AWS RDS PostgreSQL / Azure SQL Database

The system currently has no persistence for previously generated signals. Adding a relational database would enable trend analysis, backtesting against stored signals, and audit trails for the LLM decisions. AWS RDS PostgreSQL or Azure SQL Database are natural fits: both are managed services that handle backups, patching, and failover automatically. The schema would be simple — one table for `analysis_results` keyed by `(symbol, interval, timestamp)` — so a small `db.t3.micro` RDS instance would be more than sufficient. The Pydantic models already in `models/signal.py` map cleanly to relational columns, so the migration from in-memory to persisted results would require minimal schema design work.

## 4. Scheduled Re-analysis — Manual Trigger → AWS Lambda + EventBridge / Azure Functions + Timer Trigger

Currently, analysis only runs when a user visits the frontend and the browser makes a request. There is no background refresh. For a production system, periodic re-analysis of a watchlist (e.g. BTC, ETH, BNB every hour) would keep the UI current without user interaction. AWS Lambda functions triggered by EventBridge Scheduler rules (cron expressions) would invoke the analysis pipeline on a schedule and write results to RDS and S3. The equivalent on Azure is a Timer-triggered Azure Function. Both approaches are serverless, meaning there is no compute cost between invocations — the function runs for a few seconds per symbol and then terminates.

## 5. Frontend Hosting — npm run dev → AWS Amplify / Azure Static Web Apps

The Vite/React frontend is currently served by the Vite development server on `localhost:5173`. In production, the built static assets (`npm run build`) would be deployed to a static hosting service. AWS Amplify and Azure Static Web Apps both offer CDN-backed hosting with automatic deployments from a Git branch, custom domain support, and HTTPS out of the box. Because the frontend is entirely static after the build step, there is no server to maintain — assets are served from edge locations globally, giving low latency to any user regardless of geography.

---

## Why Serverless Is Preferable to EC2 for This Use Case

Signal generation is an on-demand, infrequent workload. A user requests an analysis, the pipeline runs for roughly one to two seconds, and then the system is idle. Running a continuously provisioned EC2 instance to serve this pattern means paying for compute around the clock even when no analysis is happening. A serverless architecture — Lambda for the analysis pipeline, S3 for candle storage, and Amplify for the frontend — eliminates idle cost entirely. Each Lambda invocation is billed only for the milliseconds it runs, and S3 charges only for storage and request volume. For a university demonstration or low-traffic signal tool, this maps directly to near-zero running costs between active sessions. Serverless also removes operational overhead: there are no instances to patch, no autoscaling groups to configure, and no load balancers to manage. The trade-off is cold-start latency on the first invocation after an idle period, but for a signal tool where a one-second delay is acceptable this is not a meaningful concern.
