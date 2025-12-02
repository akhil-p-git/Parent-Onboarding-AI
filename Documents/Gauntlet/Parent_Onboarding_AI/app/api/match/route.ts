import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { matchingEngine } from '@/lib/matching';
import { airtableClient } from '@/lib/airtable';
import { logger } from '@/lib/logger';
import { NextResponse } from 'next/server';

export async function POST(requestBody: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { founderId } = await requestBody.json();

    if (!founderId) {
      return NextResponse.json({ error: 'Founder ID required' }, { status: 400 });
    }

    logger.info('Finding matches', { founderId, userId: session.user?.id });

    // Fetch founder data
    const founder = await airtableClient.getFounderById(founderId);
    if (!founder) {
      return NextResponse.json({ error: 'Founder not found' }, { status: 404 });
    }

    // Fetch all mentors
    const mentors = await airtableClient.getMentors();
    if (!mentors || mentors.length === 0) {
      return NextResponse.json({ error: 'No mentors available' }, { status: 404 });
    }

    // Fetch availability for all mentors
    const availabilityMap = new Map();
    for (const mentor of mentors) {
      const availability = await airtableClient.getAvailability(mentor.id);
      const availableSlots = availability.filter((a: any) => !a.isBooked).length;
      availabilityMap.set(mentor.id, { mentorId: mentor.id, availableSlots });
    }

    // Run matching algorithm
    const matches = matchingEngine.getTopMatches(founder, mentors, availabilityMap, 10);

    logger.logEvent('matches_found', { founderId, matchCount: matches.length });

    return NextResponse.json({ matches }, { status: 200 });
  } catch (error) {
    logger.error('Matching error', { error: String(error) });
    return NextResponse.json({ error: 'Matching failed' }, { status: 500 });
  }
}
