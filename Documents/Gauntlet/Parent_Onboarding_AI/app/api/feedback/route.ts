import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { logger } from '@/lib/logger';
import { NextResponse } from 'next/server';

export async function POST(requestBody: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { sessionId, score, comment } = await requestBody.json();

    logger.info('Feedback submitted', { sessionId, score, comment, userId: session.user?.id });

    logger.logEvent('feedback_submitted', { sessionId, score, comment, userId: session.user?.id });

    return NextResponse.json({ success: true }, { status: 201 });
  } catch (error) {
    logger.error('Failed to submit feedback', { error: String(error) });
    return NextResponse.json({ error: 'Failed to submit feedback' }, { status: 500 });
  }
}
