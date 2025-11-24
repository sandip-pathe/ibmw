# Frontend - Fintech Compliance Engine

Next.js frontend for AI-powered compliance automation.

## Tech Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS
- Stack Auth (authentication)
- Shadcn/UI components
- Lucide React icons

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Configure `.env.local`:
```env
NEXT_PUBLIC_STACK_PROJECT_ID=d79111d8-58fc-431f-b4f5-521556f9cd59
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GITHUB_CLIENT_ID=Iv1.d64f7b80f1f0a9c2
NEXT_PUBLIC_GITHUB_REDIRECT_URI=http://localhost:3000/auth/github/callback
```

3. Start dev server:
```bash
npm run dev
```

Visit http://localhost:3000

## Pages

- `/` - Landing page
- `/auth/signin` - Sign in (email/GitHub)
- `/auth/signup` - Create account
- `/dashboard` - Main dashboard
- `/repos/select` - Select repos to analyze
- `/repos/status` - Indexing status

## User Flow

1. Sign up with email or GitHub OAuth
2. Connect GitHub account in dashboard
3. Select repositories to analyze
4. View indexing progress
5. Get compliance reports

## API Client

Located at `/lib/api-client.ts`:
- GitHub OAuth flow
- Repository management
- Indexing operations
