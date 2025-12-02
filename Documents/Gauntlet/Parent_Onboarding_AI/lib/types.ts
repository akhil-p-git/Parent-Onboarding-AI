// User roles
export type UserRole = 'founder' | 'mentor' | 'admin' | 'program_manager';

// User session
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  createdAt: Date;
  updatedAt: Date;
}

// Mentor profile
export interface MentorProfile {
  id: string;
  userId: string;
  expertise: string[];
  industryFocus: string[];
  stages: ('idea' | 'mvp' | 'growth' | 'scaling')[];
  bio: string;
  yearsOfExperience: number;
  availability: TimeSlot[];
  currentLoad: number;
  maxCapacity: number;
  rating: number;
  reviewCount: number;
  createdAt: Date;
  updatedAt: Date;
}

// Founder profile
export interface FounderProfile {
  id: string;
  userId: string;
  companyName: string;
  stage: 'idea' | 'mvp' | 'growth' | 'scaling';
  industryFocus: string;
  description: string;
  targetExpertise: string[];
  createdAt: Date;
  updatedAt: Date;
}

// Time slot
export interface TimeSlot {
  id: string;
  mentorId: string;
  startTime: Date;
  endTime: Date;
  isBooked: boolean;
  createdAt: Date;
}

// Session
export interface Session {
  id: string;
  mentorId: string;
  founderId: string;
  startTime: Date;
  endTime: Date;
  status: 'scheduled' | 'completed' | 'cancelled';
  notes?: string;
  meetingLink?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Feedback
export interface Feedback {
  id: string;
  sessionId: string;
  mentorId: string;
  founderId: string;
  score: number;
  comment: string;
  createdAt: Date;
}

// Matching score
export interface MatchingScore {
  mentorId: string;
  founderId: string;
  overallScore: number;
  expertiseScore: number;
  industryScore: number;
  stageScore: number;
  availabilityScore: number;
  loadScore: number;
  explanation?: string;
  rank?: number;
}
