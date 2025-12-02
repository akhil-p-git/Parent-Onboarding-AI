import Airtable from 'airtable';
import { logger } from './logger';

function getBase() {
  if (!process.env.AIRTABLE_API_KEY || !process.env.AIRTABLE_BASE_ID) {
    throw new Error('Airtable credentials not configured');
  }
  return new Airtable({
    apiKey: process.env.AIRTABLE_API_KEY,
  }).base(process.env.AIRTABLE_BASE_ID);
}

export const airtableClient = {
  // Mentors table operations
  async getMentors() {
    try {
      const base = getBase();
      const mentors: any[] = [];
      await base('Mentors').select().eachPage((records, fetchNextPage) => {
        records.forEach((record) => {
          mentors.push({
            id: record.id,
            ...record.fields,
          });
        });
        fetchNextPage();
      });
      logger.info('Fetched mentors from Airtable', { count: mentors.length });
      return mentors;
    } catch (error) {
      logger.error('Failed to fetch mentors', { error: String(error) });
      throw error;
    }
  },

  async getMentorById(id: string) {
    try {
      const base = getBase();
      const record = await base('Mentors').find(id);
      logger.info('Fetched mentor', { mentorId: id });
      return { id: record.id, ...record.fields };
    } catch (error) {
      logger.error('Failed to fetch mentor', { mentorId: id, error: String(error) });
      throw error;
    }
  },

  async updateMentor(id: string, fields: Record<string, any>) {
    try {
      const base = getBase();
      const updated = await base('Mentors').update(id, fields);
      logger.info('Updated mentor', { mentorId: id });
      return { id: updated.id, ...updated.fields };
    } catch (error) {
      logger.error('Failed to update mentor', { mentorId: id, error: String(error) });
      throw error;
    }
  },

  // Founders table operations
  async getFounders() {
    try {
      const base = getBase();
      const founders: any[] = [];
      await base('Founders').select().eachPage((records, fetchNextPage) => {
        records.forEach((record) => {
          founders.push({
            id: record.id,
            ...record.fields,
          });
        });
        fetchNextPage();
      });
      logger.info('Fetched founders from Airtable', { count: founders.length });
      return founders;
    } catch (error) {
      logger.error('Failed to fetch founders', { error: String(error) });
      throw error;
    }
  },

  async getFounderById(id: string) {
    try {
      const base = getBase();
      const record = await base('Founders').find(id);
      logger.info('Fetched founder', { founderId: id });
      return { id: record.id, ...record.fields };
    } catch (error) {
      logger.error('Failed to fetch founder', { founderId: id, error: String(error) });
      throw error;
    }
  },

  // Sessions table operations
  async getSessions() {
    try {
      const base = getBase();
      const sessions: any[] = [];
      await base('Sessions').select().eachPage((records, fetchNextPage) => {
        records.forEach((record) => {
          sessions.push({
            id: record.id,
            ...record.fields,
          });
        });
        fetchNextPage();
      });
      logger.info('Fetched sessions from Airtable', { count: sessions.length });
      return sessions;
    } catch (error) {
      logger.error('Failed to fetch sessions', { error: String(error) });
      throw error;
    }
  },

  async createSession(fields: Record<string, any>) {
    try {
      const base = getBase();
      const created = await base('Sessions').create(fields);
      logger.info('Created session', { sessionId: created.id });
      return { id: created.id, ...created.fields };
    } catch (error) {
      logger.error('Failed to create session', { error: String(error) });
      throw error;
    }
  },

  async updateSession(id: string, fields: Record<string, any>) {
    try {
      const base = getBase();
      const updated = await base('Sessions').update(id, fields);
      logger.info('Updated session', { sessionId: id });
      return { id: updated.id, ...updated.fields };
    } catch (error) {
      logger.error('Failed to update session', { sessionId: id, error: String(error) });
      throw error;
    }
  },

  async deleteSession(id: string) {
    try {
      const base = getBase();
      await base('Sessions').destroy(id);
      logger.info('Deleted session', { sessionId: id });
    } catch (error) {
      logger.error('Failed to delete session', { sessionId: id, error: String(error) });
      throw error;
    }
  },

  // Availability table operations
  async getAvailability(mentorId: string) {
    try {
      const base = getBase();
      const availability: any[] = [];
      await base('Availability')
        .select({ filterByFormula: `{Mentor ID} = '${mentorId}'` })
        .eachPage((records, fetchNextPage) => {
          records.forEach((record) => {
            availability.push({
              id: record.id,
              ...record.fields,
            });
          });
          fetchNextPage();
        });
      logger.info('Fetched availability', { mentorId, count: availability.length });
      return availability;
    } catch (error) {
      logger.error('Failed to fetch availability', { mentorId, error: String(error) });
      throw error;
    }
  },
};
