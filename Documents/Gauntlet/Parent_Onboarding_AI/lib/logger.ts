type LogLevel = 'info' | 'warn' | 'error' | 'debug';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
}

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development';

  private formatEntry(level: LogLevel, message: string, context?: Record<string, any>): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
    };
  }

  info(message: string, context?: Record<string, any>) {
    const entry = this.formatEntry('info', message, context);
    console.log(JSON.stringify(entry));
  }

  warn(message: string, context?: Record<string, any>) {
    const entry = this.formatEntry('warn', message, context);
    console.warn(JSON.stringify(entry));
  }

  error(message: string, context?: Record<string, any>) {
    const entry = this.formatEntry('error', message, context);
    console.error(JSON.stringify(entry));
  }

  debug(message: string, context?: Record<string, any>) {
    if (this.isDevelopment) {
      const entry = this.formatEntry('debug', message, context);
      console.debug(JSON.stringify(entry));
    }
  }

  logEvent(eventName: string, data?: Record<string, any>) {
    this.info(`Event: ${eventName}`, data);
  }
}

export const logger = new Logger();
