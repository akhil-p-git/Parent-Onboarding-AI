import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';
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
      const prompt = `You are a mentor-mentee matching expert. Provide a brief, professional explanation (1-2 sentences) for why ${mentor.name} is a good match for ${founder.companyName}.

Match Details:
- Mentor expertise: ${mentor.expertise.join(', ')}
- Mentor industry focus: ${mentor.industryFocus.join(', ')}
- Mentor experience: ${mentor.yearsOfExperience} years
- Mentor rating: ${mentor.rating}/5

Founder Details:
- Company: ${founder.companyName}
- Stage: ${founder.stage}
- Industry: ${founder.industryFocus}
- Seeking expertise in: ${founder.targetExpertise.join(', ')}

Match Scores:
- Overall: ${match.overallScore}%
- Expertise: ${match.expertiseScore}%
- Industry: ${match.industryScore}%
- Stage: ${match.stageScore}%

Provide a concise explanation focusing on the strongest match reasons.`;

      const { text } = await generateText({
        model: openai('gpt-3.5-turbo'),
        prompt,
        maxTokens: 100,
      });

      logger.info('Generated explanation', { mentorId: match.mentorId, founderId: match.founderId });
      return text;
    } catch (error) {
      logger.warn('AI explanation failed, using fallback', { error: String(error) });
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
    founder: FounderInfo
  ): Promise<MatchingScore[]> {
    try {
      if (matches.length === 0) return matches;

      const prompt = `Re-rank the following mentor matches for ${founder.companyName} (${founder.stage} stage startup in ${founder.industryFocus} seeking ${founder.targetExpertise.join(', ')}).

Matches (format: id|score):
${matches.map((m) => `${m.mentorId}|${m.overallScore}`).join('\n')}

Return only the re-ranked IDs in order of relevance, one per line, considering:
1. How well expertise aligns with founder's needs
2. Whether mentor has relevant industry experience
3. Experience with companies at this stage
4. Overall fit for meaningful mentorship

Return as JSON array of mentor IDs in best-fit order.`;

      const { text } = await generateText({
        model: openai('gpt-3.5-turbo'),
        prompt,
        maxTokens: 200,
      });

      try {
        const rankedIds = JSON.parse(text);
        const reRanked = rankedIds
          .map((id: string) => matches.find((m) => m.mentorId === id))
          .filter(Boolean) as MatchingScore[];

        logger.info('Re-ranked matches', { founderId: founder.companyName, count: reRanked.length });
        return reRanked.length > 0 ? reRanked : matches;
      } catch {
        logger.warn('Failed to parse re-ranked results');
        return matches;
      }
    } catch (error) {
      logger.warn('Re-ranking failed, using original order', { error: String(error) });
      return matches;
    }
  }
}

export const aiExplainer = new AIExplainer();
