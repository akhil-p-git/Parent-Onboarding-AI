import { logger } from './logger';

export class SecurityManager {
  // GDPR: Export user data
  async exportUserData(userId: string): Promise<Record<string, any>> {
    try {
      logger.logEvent('user_data_export', { userId });

      return {
        userId,
        exportDate: new Date().toISOString(),
        dataIncluded: ['profile', 'sessions', 'feedback'],
        note: 'Data exported per GDPR request',
      };
    } catch (error) {
      logger.error('Failed to export user data', { userId, error: String(error) });
      throw error;
    }
  }

  // GDPR: Delete user data
  async deleteUserData(userId: string): Promise<void> {
    try {
      logger.logEvent('user_data_deletion_initiated', { userId });

      // In production, this would:
      // 1. Anonymize user records
      // 2. Delete personal information
      // 3. Keep transaction history for compliance
      // 4. Archive deleted data for retention period

      logger.logEvent('user_data_deleted', { userId });
    } catch (error) {
      logger.error('Failed to delete user data', { userId, error: String(error) });
      throw error;
    }
  }

  // Validate input to prevent injection attacks
  sanitizeInput(input: string): string {
    return input
      .replace(/[<>]/g, '')
      .replace(/javascript:/gi, '')
      .trim();
  }

  // Log security events
  logSecurityEvent(event: string, context: Record<string, any>): void {
    logger.info(`SECURITY: ${event}`, context);
  }

  // Validate role permissions
  hasPermission(role: string, action: string): boolean {
    const permissions: Record<string, string[]> = {
      founder: ['view_own_profile', 'book_sessions', 'submit_feedback'],
      mentor: ['view_own_profile', 'view_sessions', 'update_availability'],
      program_manager: ['view_all_profiles', 'override_matches', 'export_data'],
      admin: ['view_all_profiles', 'manage_system', 'export_data', 'delete_data'],
    };

    return (permissions[role] || []).includes(action);
  }
}

export const securityManager = new SecurityManager();
