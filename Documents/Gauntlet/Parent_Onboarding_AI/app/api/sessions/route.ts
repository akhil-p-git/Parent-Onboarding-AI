import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { airtableClient } from '@/lib/airtable';
import { logger } from '@/lib/logger';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    logger.info('Fetching sessions', { userId: session.user?.id });

    const sessions = await airtableClient.getSessions();

    return NextResponse.json({ sessions }, { status: 200 });
  } catch (error) {
    logger.error('Failed to fetch sessions', { error: String(error) });
    return NextResponse.json({ error: 'Failed to fetch sessions' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();

    logger.info('Creating session', { userId: session.user?.id, body });

    const newSession = await airtableClient.createSession(body);

    logger.logEvent('session_created', { sessionId: newSession.id, userId: session.user?.id });

    return NextResponse.json({ session: newSession }, { status: 201 });
  } catch (error) {
    logger.error('Failed to create session', { error: String(error) });
    return NextResponse.json({ error: 'Failed to create session' }, { status: 500 });
  }
}
