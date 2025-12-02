'use client';

import { useSession as useNextAuthSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function useSession() {
  const session = useNextAuthSession();
  const router = useRouter();

  useEffect(() => {
    if (session?.status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [session?.status, router]);

  return session;
}

export function useRequireRole(role: string | string[]) {
  const session = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session?.status === 'authenticated') {
      const roles = Array.isArray(role) ? role : [role];
      if (!roles.includes(session.data?.user?.role as string)) {
        router.push('/auth/unauthorized');
      }
    }
  }, [session?.status, session?.data?.user?.role, role, router]);

  return session;
}
