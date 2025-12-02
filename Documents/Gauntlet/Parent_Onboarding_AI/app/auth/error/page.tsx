'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function ErrorContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error');

  const errorMessages: Record<string, string> = {
    AuthCallback: 'There was an error with the authentication callback.',
    OAuthSignin: 'There was an error signing in with OAuth.',
    OAuthCallback: 'There was an error with the OAuth callback.',
    EmailCreateAccount: 'Could not create user account.',
    EmailSignin: 'Check your email address.',
    AccessDenied: 'Access was denied.',
    Verification: 'The verification token was invalid or has expired.',
  };

  const message = errorMessages[error as string] || 'An unknown error occurred.';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Authentication Error</h1>
        <p className="text-gray-600 mb-6">{message}</p>
        <Link
          href="/auth/signin"
          className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Sign In
        </Link>
      </div>
    </div>
  );
}

export default function ErrorPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ErrorContent />
    </Suspense>
  );
}
