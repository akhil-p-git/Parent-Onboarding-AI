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

    logger.info('Fetching mentors', { userId: session.user?.id });

    const mentors = await airtableClient.getMentors();

    return NextResponse.json({ mentors }, { status: 200 });
  } catch (error) {
    logger.error('Failed to fetch mentors', { error: String(error) });
    return NextResponse.json({ error: 'Failed to fetch mentors' }, { status: 500 });
  }
}
