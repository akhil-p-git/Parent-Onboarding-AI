import { logger } from './logger';

interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
}

class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private config: RateLimitConfig;

  constructor(config: RateLimitConfig = { maxRequests: 100, windowMs: 60000 }) {
    this.config = config;
  }

  isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;

    let requestTimes = this.requests.get(key) || [];
    requestTimes = requestTimes.filter((time) => time > windowStart);

    if (requestTimes.length >= this.config.maxRequests) {
      logger.warn('Rate limit exceeded', { key, requests: requestTimes.length });
      return false;
    }

    requestTimes.push(now);
    this.requests.set(key, requestTimes);

    return true;
  }

  reset(key: string): void {
    this.requests.delete(key);
  }
}

export const airtableRateLimiter = new RateLimiter({ maxRequests: 300, windowMs: 60000 });
export const apiRateLimiter = new RateLimiter({ maxRequests: 1000, windowMs: 60000 });
