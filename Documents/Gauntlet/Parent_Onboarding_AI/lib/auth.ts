import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { logger } from './logger';

// This is a basic implementation. In production, integrate with your user database
const users = new Map([
  ['founder@example.com', { id: '1', email: 'founder@example.com', role: 'founder', name: 'John Founder' }],
  ['mentor@example.com', { id: '2', email: 'mentor@example.com', role: 'mentor', name: 'Jane Mentor' }],
  ['admin@example.com', { id: '3', email: 'admin@example.com', role: 'admin', name: 'Admin User' }],
]);

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          logger.warn('Login attempt with missing credentials');
          return null;
        }

        const user = users.get(credentials.email);

        if (!user) {
          logger.warn('Login attempt with non-existent user', { email: credentials.email });
          return null;
        }

        // In production, verify password hash
        if (credentials.password !== 'password') {
          logger.warn('Login attempt with incorrect password', { email: credentials.email });
          return null;
        }

        logger.info('User logged in', { email: credentials.email, role: user.role });
        return user;
      },
    }),
  ],
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    },
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
};
