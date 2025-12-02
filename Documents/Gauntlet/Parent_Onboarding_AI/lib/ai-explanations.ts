import { MatchingScore } from './types';
import { logger } from './logger';

interface MentorInfo {
  name: string;
  expertise: string[];
  industryFocus: string[];
  yearsOfExperience: number;
  rating: number;
}

interface FounderInfo {
  companyName: string;
  stage: string;
  industryFocus: string;
  targetExpertise: string[];
}

export class AIExplainer {
  async generateExplanation(
    match: MatchingScore,
    mentor: MentorInfo,
    founder: FounderInfo
  ): Promise<string> {
    try {
      // AI feature placeholder - ready for OpenAI integration
      // For now, use intelligent fallback
      logger.info('Generating explanation', { mentorId: match.mentorId, founderId: match.founderId });
      return this.generateFallbackExplanation(match, mentor, founder);
    } catch (error) {
      logger.warn('Failed to generate explanation', { error: String(error) });
      return this.generateFallbackExplanation(match, mentor, founder);
    }
  }

  private generateFallbackExplanation(
    match: MatchingScore,
    mentor: MentorInfo,
    founder: FounderInfo
  ): string {
    const strengths: string[] = [];

    if (match.expertiseScore > 80) {
      strengths.push(`strong expertise in ${founder.targetExpertise.slice(0, 2).join(' and ')}`);
    }

    if (match.industryScore > 80) {
      strengths.push(`experience in your industry`);
    }

    if (match.stageScore > 80) {
      strengths.push(`expertise at your company stage`);
    }

    if (mentor.rating > 4.5) {
      strengths.push(`highly rated mentor`);
    }

    if (strengths.length === 0) {
      return `${mentor.name} has relevant experience that could help ${founder.companyName}.`;
    }

    return `${mentor.name} is a good match because of their ${strengths.join(', ')}.`;
  }

  async reRankMatches(
    matches: MatchingScore[],
    _founder: FounderInfo
  ): Promise<MatchingScore[]> {
    try {
      // AI re-ranking placeholder - uses deterministic scoring order for now
      // Ready for OpenAI integration in future
      logger.info('Re-ranking matches (using deterministic order)', { matchCount: matches.length });
      return matches; // Already sorted by matching engine
    } catch (error) {
      logger.warn('Re-ranking failed, using original order', { error: String(error) });
      return matches;
    }
  }
}

export const aiExplainer = new AIExplainer();
