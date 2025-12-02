# Office Hours Matching Tool

An AI-powered mentor-mentee matching platform for Capital Factory built with Next.js, TypeScript, and modern web technologies.

## 📋 Project Status

### Completed ✅
1. **Next.js TypeScript Project Setup** - Project scaffolded with Tailwind CSS and ESLint configuration
2. **Authentication** - NextAuth.js with role-based access control (founder, mentor, admin)
3. **Airtable Integration** - API client for CRUD operations on mentors, founders, and sessions

### In Progress / Pending
4-20. Additional features (matching engine, UI components, database, etc.)

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Airtable account with base set up
- AWS account (for SES)

### Installation

```bash
npm install
```

### Environment Setup

Create `.env.local` with the following variables:

```env
# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here

# Airtable
AIRTABLE_API_KEY=your-api-key
AIRTABLE_BASE_ID=your-base-id

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SES_REGION=us-east-1
AWS_SES_FROM_EMAIL=noreply@capitalfactory.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/office_hours_db

# AI
OPENAI_API_KEY=your-openai-api-key

# Application
NEXT_PUBLIC_API_URL=http://localhost:3000
NODE_ENV=development
```

### Development

```bash
npm run dev
```

Visit http://localhost:3000

### Demo Credentials

Use the following test accounts:

- **Founder**: founder@example.com / password
- **Mentor**: mentor@example.com / password
- **Admin**: admin@example.com / password

## 📁 Project Structure

```
.
├── app/
│   ├── api/                    # Next.js API routes
│   │   ├── auth/              # Authentication endpoints
│   │   ├── mentors/           # Mentor management
│   │   └── sessions/          # Session management
│   ├── auth/                  # Authentication pages
│   ├── dashboard/             # Dashboard pages
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Home page
│   └── globals.css            # Global styles
├── lib/
│   ├── airtable.ts            # Airtable client
│   ├── auth.ts                # NextAuth configuration
│   ├── logger.ts              # Logging utility
│   ├── types.ts               # TypeScript type definitions
│   └── hooks/                 # React hooks
├── middleware.ts              # Next.js middleware
├── types/                     # Global type definitions
├── middleware.ts              # Next.js middleware
├── package.json
├── tsconfig.json
└── README.md
```

## 🔐 Authentication & Authorization

The application uses NextAuth.js with JWT strategy:

- **Middleware-based protection** - Routes protected at middleware level
- **Role-based access control** - Different UIs/endpoints for founder, mentor, and admin
- **Session management** - 30-day session duration

Protected Routes:
- `/admin/*` - Admin/Program Manager only
- `/mentor/*` - Mentor only
- `/founder/*` - Founder only
- `/dashboard` - All authenticated users

## 🔗 API Endpoints

### Mentors
- `GET /api/mentors` - List all mentors
- `GET /api/mentors/:id` - Get mentor details
- `PUT /api/mentors/:id` - Update mentor profile

### Sessions
- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create new session
- `PUT /api/sessions/:id` - Update session
- `DELETE /api/sessions/:id` - Cancel session

## 📊 Airtable Integration

The application syncs with Airtable tables:

- **Mentors** - Mentor profiles, expertise, availability
- **Founders** - Startup profiles, needs
- **Sessions** - Booked sessions and metadata
- **Availability** - Mentor time slots
- **Feedback** - Post-session ratings and comments

## 🛠 Technology Stack

- **Frontend**: React 18, Next.js 14, TypeScript
- **Styling**: Tailwind CSS, Headless UI
- **Authentication**: NextAuth.js
- **Backend**: Next.js API Routes, Node.js
- **Database**: Airtable (operational), PostgreSQL (analytics)
- **AI**: Vercel AI SDK, OpenAI
- **Cloud**: Vercel (hosting), AWS SES (email)

## 📝 Development Notes

### Adding New API Routes

Create new route files in `app/api/`:

```typescript
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { NextResponse } from 'next/server';

export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Your logic here
  return NextResponse.json({ data: {} });
}
```

### Accessing Airtable

```typescript
import { airtableClient } from '@/lib/airtable';

const mentors = await airtableClient.getMentors();
const mentor = await airtableClient.getMentorById(mentorId);
await airtableClient.updateMentor(mentorId, { Name: 'New Name' });
```

### Logging Events

```typescript
import { logger } from '@/lib/logger';

logger.info('User logged in', { userId: user.id });
logger.error('Database error', { error: err.message });
logger.logEvent('session_created', { sessionId: id });
```

## 🚧 Next Steps (Priority Order)

### P0: Critical
4. Design and implement AI matching engine core logic
5. Integrate Vercel AI SDK for match ranking and explanations
6. Build booking flow UI for founders
7. Build mentor profile management UI
8. Implement session management features
9. Set up email notifications with AWS SES
11. Set up PostgreSQL analytics database
16. Implement security and GDPR compliance

### P1: Important
10. Build feedback collection system
12. Build admin dashboard
13. Implement manual override tools
14. Build export functionality
15. Implement observability and logging
17. Implement Airtable rate limiting

### P2: Optional
18. Calendar integrations (Google/Outlook)
19. Automatic meeting link generation
20. SMS notifications

## 📖 Documentation

- [Airtable Schema](./docs/airtable-schema.md) - Table structures and relationships
- [API Documentation](./docs/api.md) - Detailed endpoint documentation
- [Architecture](./docs/architecture.md) - System design overview

## 🤝 Contributing

Follow the coding standards in the repository:

- Use TypeScript for all new code
- Follow ESLint and Prettier configurations
- Write unit tests for new features
- Update documentation when adding features

## 📄 License

Proprietary - Capital Factory
