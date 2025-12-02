import { MatchingScore } from './types';
import { logger } from './logger';

interface MentorData {
  id: string;
  expertise: string[];
  industryFocus: string[];
  stages: string[];
  currentLoad: number;
  maxCapacity: number;
  rating: number;
}

interface FounderData {
  id: string;
  targetExpertise: string[];
  industryFocus: string;
  stage: string;
}

interface AvailabilityData {
  mentorId: string;
  availableSlots: number;
}

export class MatchingEngine {
  // Score expertise match (0-100)
  private scoreExpertise(founder: FounderData, mentor: MentorData): number {
    if (!founder.targetExpertise || founder.targetExpertise.length === 0) {
      return 50;
    }

    const matches = founder.targetExpertise.filter((skill) =>
      mentor.expertise.some((m) => m.toLowerCase() === skill.toLowerCase())
    ).length;

    return Math.min(100, (matches / founder.targetExpertise.length) * 100);
  }

  // Score industry match (0-100)
  private scoreIndustry(founder: FounderData, mentor: MentorData): number {
    if (!founder.industryFocus || !mentor.industryFocus || mentor.industryFocus.length === 0) {
      return 50;
    }

    const hasMatch = mentor.industryFocus.some(
      (ind) => ind.toLowerCase() === founder.industryFocus.toLowerCase()
    );

    return hasMatch ? 100 : 30;
  }

  // Score stage match (0-100)
  private scoreStage(founder: FounderData, mentor: MentorData): number {
    if (!founder.stage || !mentor.stages || mentor.stages.length === 0) {
      return 50;
    }

    const hasMatch = mentor.stages.some((s) => s.toLowerCase() === founder.stage.toLowerCase());
    return hasMatch ? 100 : 40;
  }

  // Score availability (0-100)
  private scoreAvailability(availability: AvailabilityData | undefined): number {
    if (!availability || availability.availableSlots === 0) {
      return 0;
    }

    return Math.min(100, availability.availableSlots * 20);
  }

  // Score load balancing (0-100) - prefer mentors with lower load
  private scoreLoad(mentor: MentorData): number {
    if (mentor.maxCapacity === 0) {
      return 0;
    }

    const utilization = mentor.currentLoad / mentor.maxCapacity;
    return Math.max(0, 100 - utilization * 100);
  }

  // Score mentor reputation (0-100)
  private scoreReputation(mentor: MentorData): number {
    // Scale 0-5 rating to 0-100
    return Math.min(100, (mentor.rating / 5) * 100);
  }

  // Calculate weighted overall score
  private calculateOverallScore(
    expertise: number,
    industry: number,
    stage: number,
    availability: number,
    load: number,
    reputation: number
  ): number {
    // Weights: expertise (30%), industry (20%), stage (20%), availability (15%), load (10%), reputation (5%)
    const weights = {
      expertise: 0.3,
      industry: 0.2,
      stage: 0.2,
      availability: 0.15,
      load: 0.1,
      reputation: 0.05,
    };

    return (
      expertise * weights.expertise +
      industry * weights.industry +
      stage * weights.stage +
      availability * weights.availability +
      load * weights.load +
      reputation * weights.reputation
    );
  }

  // Main matching function
  public findMatches(
    founder: FounderData,
    mentors: MentorData[],
    availabilityMap: Map<string, AvailabilityData>
  ): MatchingScore[] {
    try {
      const matches: MatchingScore[] = mentors
        .map((mentor) => {
          const expertiseScore = this.scoreExpertise(founder, mentor);
          const industryScore = this.scoreIndustry(founder, mentor);
          const stageScore = this.scoreStage(founder, mentor);
          const availabilityScore = this.scoreAvailability(availabilityMap.get(mentor.id));
          const loadScore = this.scoreLoad(mentor);
          const reputationScore = this.scoreReputation(mentor);

          const overallScore = this.calculateOverallScore(
            expertiseScore,
            industryScore,
            stageScore,
            availabilityScore,
            loadScore,
            reputationScore
          );

          return {
            mentorId: mentor.id,
            founderId: founder.id,
            overallScore: Math.round(overallScore),
            expertiseScore: Math.round(expertiseScore),
            industryScore: Math.round(industryScore),
            stageScore: Math.round(stageScore),
            availabilityScore: Math.round(availabilityScore),
            loadScore: Math.round(loadScore),
          };
        })
        .filter((match) => match.overallScore > 0)
        .sort((a, b) => b.overallScore - a.overallScore);

      logger.info('Matching complete', {
        founderId: founder.id,
        matchCount: matches.length,
        topScore: matches[0]?.overallScore,
      });

      return matches;
    } catch (error) {
      logger.error('Matching error', { founderId: founder.id, error: String(error) });
      throw error;
    }
  }

  // Get top N matches
  public getTopMatches(
    founder: FounderData,
    mentors: MentorData[],
    availabilityMap: Map<string, AvailabilityData>,
    limit: number = 5
  ): MatchingScore[] {
    return this.findMatches(founder, mentors, availabilityMap).slice(0, limit);
  }
}

export const matchingEngine = new MatchingEngine();
