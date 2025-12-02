# Product Requirements Document (PRD)
## Office Hours Matching Tool – AI-Powered Mentor-Mentee Platform

**Organization:** Capital Factory
**Project ID:** jcZVCmoXUgvC9nVOiJUZ_1762557598774

## Executive Summary

The Office Hours Matching Tool is an AI-powered mentor-mentee platform that streamlines and optimizes connections between startup founders and subject matter experts at Capital Factory. The product will be built as a full-stack web application using a TypeScript-first stack: Next.js on Vercel for the frontend and backend APIs, Vercel AI SDK for AI matching and reasoning, Airtable as the operational data source, and PostgreSQL for analytics and metrics. The platform aims to enhance user experience, increase mentor utilization, and improve the quality and efficiency of mentorship connections in direct support of Capital Factory's accelerator mission.

## Problem Statement

Capital Factory's current Union.vc platform requires manual profile creation, has no intelligent matching, relies on manual surveys for feedback, and underutilizes mentor availability. These issues result in suboptimal matches, low mentor utilization (<75%), and a fragmented user experience. An integrated, AI-enabled web platform is required to:

- Eliminate manual data entry by syncing with Airtable as a single source of truth for profiles and sessions.
- Implement an AI-driven matching engine that considers expertise, industry, stage, availability, and historical feedback.
- Provide passive reputation tracking (via feedback and utilization metrics) without burdensome workflows.
- Offer automated notifications, calendar integration (stretch), and an analytics dashboard for program managers.

## Goals & Success Metrics

### Mentor Utilization Rate
- Increase mentor time-slot utilization to above 90% within six months.

### Platform Activity
- Achieve a 30% increase in booked office hours sessions within six months.

### Engagement Distribution
- Achieve more even distribution of engagements across expertise areas, measured as no single expertise cluster accounting for more than a defined percentage of total sessions.

### Session Quality
- Raise average post-session feedback scores to ≥ 4.5 / 5.

### Adoption Rate
- Reach 70% adoption among existing mentors and mentees in the first quarter post-launch.

### System Reliability
- Maintain uptime of ≥ 99.5% for critical booking and matching workflows.

## Target Users & Personas

### Startup Founders (Mentees)
- Need quick access to mentors with relevant expertise, industry knowledge, and stage-specific experience.
- Prefer a guided, low-friction booking flow with AI-suggested mentors and times.

### Subject Matter Experts (Mentors)
- Want their limited availability matched with high-fit mentees.
- Need an at-a-glance view of upcoming sessions, utilization rates, and feedback.

### Program Managers
- Require a centralized dashboard to monitor platform usage, mentor utilization, session quality, and adoption metrics.
- Need tools to override or manually adjust matchings when needed.

## User Stories

- As a startup founder, I want to be automatically matched with mentors who have relevant expertise, industry background, and availability so that I can receive effective guidance quickly.
- As a mentor, I want my available slots filled with sessions that closely match my expertise and interests so that my time is effectively utilized.
- As a program manager, I want to analyze session data, utilization, and feedback trends so that I can refine the matching strategy and identify gaps in mentor coverage.
- As a mentor, I want to edit my profile and availability easily so the AI matching remains accurate and up to date.
- As a founder, I want to see "why this mentor" explanations so that I trust the recommendations provided by the AI.

## Functional Requirements

### P0: Must-have (Critical)

#### AI-driven Matching Engine
- Matching based on:
  - Mentor expertise and skills.
  - Industry focus.
  - Startup stage (idea, MVP, growth, scaling).
  - Real-time availability and load-balancing to prevent overscheduling specific mentors.
- Core algorithm implemented in TypeScript as deterministic scoring logic, optionally enhanced by an LLM via Vercel AI SDK for ranking and explanations.

#### Airtable Integration
- Airtable used as the operational database for mentor profiles, founder profiles, and session records.
- Secure integration via Airtable REST API using the official Node.js SDK (airtable npm package) in server-side routes.
- One-way and two-way sync patterns:
  - Pull mentor/mentee data and availability into the matching layer.
  - Push created or updated session bookings back to Airtable.

#### Web Application (Frontend + Backend)
- Built with Next.js (App Router) and TypeScript deployed on Vercel, providing:
  - Server-side rendered pages for dashboards and booking flows.
  - API routes (or server actions) for matching, integration, and notification logic.

#### Authentication & Authorization
- Role-based access (founder, mentor, program manager, admin).
- Session-based authentication using a standard library such as Auth.js/NextAuth with OAuth or email sign-in as appropriate.

#### Email Notifications & Reminders
- Transactional emails for:
  - Booking confirmations.
  - Upcoming session reminders.
  - Cancellations and reschedules.
- Delivered via AWS SES or a similar provider using the AWS SDK in Node.js.

#### Basic Session Management
- Create, reschedule, cancel, and view sessions from the web UI.
- Sync with Airtable to keep an authoritative record of sessions.

### P1: Should-have (Important)

#### Post-Session Feedback
- Simple feedback form for mentees (and optionally mentors) after sessions.
- Store scores and short comments in PostgreSQL for analytics and optionally in Airtable for visibility.

#### Admin & Program Manager Dashboard
- Built as authenticated Next.js pages with charts and tables for:
  - Mentor utilization rate.
  - Number of sessions per mentor and per expertise area.
  - Average feedback scores.
  - Weekly/monthly session volume and adoption metrics.
- Data sourced from PostgreSQL analytics store and Airtable where appropriate.

#### Export Capabilities
- Admins can export CSV reports from the analytics database (PostgreSQL) or Airtable-backed views for:
  - Session data.
  - Feedback and utilization metrics.

#### Manual Override & Curation
- Program managers can:
  - Override AI-suggested matches.
  - Assign mentors manually.
  - Flag mentors for priority or reduced load.

### P2: Nice-to-have (Optional)

#### Calendar Integrations
- Google Calendar and Outlook support via their official APIs to:
  - Create events when a session is booked.
  - Reflect mentor availability where appropriate.
- Two-way sync where possible (subject to permissions), implemented in Next.js API routes.

#### Automatic Meeting Invites
- Integration with Google Meet or other conferencing tools to automatically generate links and attach them to calendar events.

#### SMS Notifications
- SMS reminders for urgent or last-minute notifications via Twilio or AWS SNS (if desired), triggered from server-side functions.

## Non-Functional Requirements

### Performance
- System must support up to 1000 concurrent users for core operations (browsing mentors, booking sessions, viewing dashboards).
- Matching responses should be returned within a target of ≤ 2 seconds for filtered and scored recommendations.

### Security
- All traffic over HTTPS.
- Sensitive secrets (Airtable keys, AWS credentials, OAuth secrets) stored in secure environment configuration.
- Role-based access control for all API endpoints and pages.
- GDPR-aware data handling, including right-to-access and right-to-delete where required.

### Scalability
- Vercel serverless deployment for elastic scaling.
- Airtable API usage designed for rate-limit awareness and batched operations.
- Managed PostgreSQL (e.g., Supabase/Neon or AWS RDS) for analytics and logs.

### Compliance & Privacy
- Adherence to Capital Factory's data retention policies.
- Compliance with GDPR where applicable, including consent for storing feedback and analytics data.
- Logging and monitoring of access to sensitive data.

## User Experience & Design Considerations

### Interface
- Responsive, modern web UI built with React and Next.js, using a design system with Tailwind CSS and headless component libraries for accessibility.

### Booking Flow
- Guided, step-by-step booking wizard:
  - Capture founder context (stage, needs, goals).
  - Present AI-ranked mentor options with "why this mentor" explanations.
  - Show available time slots and confirm booking.

### Accessibility
- WCAG-aligned color contrast, keyboard navigation, and screen-reader-friendly components.

### Feedback & Trust
- Transparently surface high-level rationale for matches.
- Provide simple indicators of mentor experience, focus areas, and prior feedback.

## Technical Requirements

### Frontend
- Framework: Next.js (latest) with App Router.
- Language: TypeScript.
- Styling: Tailwind CSS plus a component library (e.g., Headless UI/Radix) for accessibility.

### Backend
- Runtime: Node.js on Vercel.
- Language: TypeScript (Next.js API routes or server actions for all business logic).
- Authentication: Auth.js/NextAuth or similar, integrated with Next.js.

### AI Framework
- Vercel AI SDK for:
  - Orchestrating AI-powered mentor matching agents.
  - Generating explanations and, optionally, re-ranking matches.

### Data & Integrations
- **Airtable:** Use Airtable REST API and Airtable Node.js SDK from server-side routes to read/write data.
- **Analytics Database:** PostgreSQL for storing feedback, utilization and session metrics, and derived data for dashboards.
- **Email:** AWS SES via AWS SDK for JavaScript in Node.js for transactional emails.
- **Optional Calendar & SMS:** Google Calendar API, Outlook calendar API, Twilio or AWS SNS for SMS.

### Cloud Platform
- Primary application hosting on Vercel for tight integration with Next.js and Vercel AI SDK.
- AWS for infrastructure services (SES for email, optional RDS/PostgreSQL, optional S3 for exports/logs).

## System Architecture Overview

### Client
- Next.js React SPA/SSR pages consumed in modern browsers.

### Server
- Next.js serverless functions on Vercel for:
  - Matching API endpoints.
  - Airtable sync endpoints.
  - Notification and calendar integration endpoints.

### Data Flow
- Airtable serves as the operational data store for mentors, founders, and sessions.
- PostgreSQL stores analytics, feedback, and derived metrics.

### Matching Engine
- Fetches candidate mentors from Airtable/DB.
- Applies deterministic scoring logic in TypeScript.
- Optionally calls AI models through Vercel AI SDK for ranking and explanations.

### Observability
- Logging of key events (matches, bookings, errors).
- Basic dashboards for error rates and latency via Vercel and/or AWS tools.

## Dependencies & Assumptions

- **Airtable:** Airtable API is available, stable, and provides sufficient rate limits for the expected usage.
- **Email:** AWS SES is configured with verified sending domains and appropriate quotas.
- **Authentication:** OAuth or email-based authentication providers are available and approved by Capital Factory.
- **Calendars:** Users grant necessary permissions for Google/Outlook integrations (P2).
- **AI Models:** Access to compatible LLMs via providers supported by Vercel AI SDK.

## Out of Scope

- Native mobile applications (iOS/Android).
- Direct integration with social media platforms.
- Advanced AI features beyond intelligent matching and explanation (e.g., sentiment analysis, automated note-taking).
- Complex HR/CRM workflows beyond mentoring and office hours.
