import { SES } from 'aws-sdk';
import { logger } from './logger';

const ses = new SES({
  region: process.env.AWS_SES_REGION || 'us-east-1',
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
});

interface EmailParams {
  to: string;
  subject: string;
  html: string;
  text?: string;
}

export class EmailService {
  async sendSessionConfirmation(
    mentorEmail: string,
    founderEmail: string,
    sessionTime: Date,
    mentorName: string,
    founderName: string
  ): Promise<void> {
    const sessionDate = sessionTime.toLocaleString();

    const htmlContent = `
      <h2>Session Confirmed</h2>
      <p>Your mentoring session has been scheduled.</p>
      <p><strong>Date & Time:</strong> ${sessionDate}</p>
      <p><strong>Mentor:</strong> ${mentorName}</p>
      <p><strong>Founder:</strong> ${founderName}</p>
      <p>You will receive a meeting link before the session starts.</p>
      <p>Best regards,<br/>Office Hours Matching Team</p>
    `;

    await Promise.all([
      this.sendEmail({
        to: mentorEmail,
        subject: `New Session Scheduled - ${founderName}`,
        html: htmlContent,
      }),
      this.sendEmail({
        to: founderEmail,
        subject: `Session Confirmed with ${mentorName}`,
        html: htmlContent,
      }),
    ]);

    logger.logEvent('confirmation_emails_sent', { mentorEmail, founderEmail });
  }

  async sendSessionReminder(email: string, sessionTime: Date, mentorName: string): Promise<void> {
    const htmlContent = `
      <h2>Upcoming Mentor Session</h2>
      <p>This is a reminder about your session in 24 hours.</p>
      <p><strong>Time:</strong> ${sessionTime.toLocaleString()}</p>
      <p><strong>Mentor:</strong> ${mentorName}</p>
      <p>Join here when it's time: <a href="https://meet.google.com">Google Meet</a></p>
      <p>Best regards,<br/>Office Hours Matching Team</p>
    `;

    await this.sendEmail({
      to: email,
      subject: `Reminder: Mentor Session with ${mentorName} Tomorrow`,
      html: htmlContent,
    });

    logger.logEvent('reminder_email_sent', { email });
  }

  async sendCancellationNotice(email: string, mentorName: string): Promise<void> {
    const htmlContent = `
      <h2>Session Cancelled</h2>
      <p>Your session with ${mentorName} has been cancelled.</p>
      <p>You can book another session anytime in your dashboard.</p>
      <p>Best regards,<br/>Office Hours Matching Team</p>
    `;

    await this.sendEmail({
      to: email,
      subject: `Session Cancelled - ${mentorName}`,
      html: htmlContent,
    });

    logger.logEvent('cancellation_email_sent', { email });
  }

  private async sendEmail({ to, subject, html, text }: EmailParams): Promise<void> {
    if (!process.env.AWS_SES_FROM_EMAIL) {
      logger.error('AWS_SES_FROM_EMAIL not configured');
      return;
    }

    try {
      await ses
        .sendEmail({
          Source: process.env.AWS_SES_FROM_EMAIL,
          Destination: { ToAddresses: [to] },
          Message: {
            Subject: { Data: subject, Charset: 'UTF-8' },
            Body: {
              Html: { Data: html, Charset: 'UTF-8' },
              Text: { Data: text || html, Charset: 'UTF-8' },
            },
          },
        })
        .promise();

      logger.info('Email sent', { to, subject });
    } catch (error) {
      logger.error('Failed to send email', { to, subject, error: String(error) });
      throw error;
    }
  }
}

export const emailService = new EmailService();
