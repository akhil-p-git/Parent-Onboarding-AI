import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { airtableClient } from '@/lib/airtable';
import { logger } from '@/lib/logger';
import { NextResponse } from 'next/server';

export async function GET(_request: Request, { params }: { params: { id: string } }) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const sessionData = await airtableClient.getSessions();
    const found = sessionData.find((s) => s.id === params.id);

    if (!found) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 });
    }

    return NextResponse.json({ session: found }, { status: 200 });
  } catch (error) {
    logger.error('Failed to fetch session', { error: String(error) });
    return NextResponse.json({ error: 'Failed to fetch session' }, { status: 500 });
  }
}

export async function PUT(requestBody: Request, { params }: { params: { id: string } }) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await requestBody.json();

    logger.info('Updating session', { sessionId: params.id, userId: session.user?.id });

    const updated = await airtableClient.updateSession(params.id, body);

    logger.logEvent('session_updated', { sessionId: params.id, userId: session.user?.id });

    return NextResponse.json({ session: updated }, { status: 200 });
  } catch (error) {
    logger.error('Failed to update session', { error: String(error) });
    return NextResponse.json({ error: 'Failed to update session' }, { status: 500 });
  }
}

export async function DELETE(_request: Request, { params }: { params: { id: string } }) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    logger.info('Deleting session', { sessionId: params.id, userId: session.user?.id });

    await airtableClient.deleteSession(params.id);

    logger.logEvent('session_deleted', { sessionId: params.id, userId: session.user?.id });

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    logger.error('Failed to delete session', { error: String(error) });
    return NextResponse.json({ error: 'Failed to delete session' }, { status: 500 });
  }
}
