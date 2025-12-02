'use client';

import { signOut, useSession } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Office Hours Matching</h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">{session?.user?.email}</span>
            <button
              onClick={() => signOut()}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Welcome, {session?.user?.name}!</h2>
          <p className="text-gray-600 mb-4">Role: <span className="font-semibold capitalize">{session?.user?.role}</span></p>

          {session?.user?.role === 'founder' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link href="/founder/booking" className="block p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100">
                <h3 className="font-bold text-blue-900">Book a Session</h3>
                <p className="text-sm text-blue-700">Find and book mentors</p>
              </Link>
              <Link href="/founder/sessions" className="block p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100">
                <h3 className="font-bold text-green-900">My Sessions</h3>
                <p className="text-sm text-green-700">View your scheduled sessions</p>
              </Link>
            </div>
          )}

          {session?.user?.role === 'mentor' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link href="/mentor/profile" className="block p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100">
                <h3 className="font-bold text-blue-900">My Profile</h3>
                <p className="text-sm text-blue-700">Edit your profile and availability</p>
              </Link>
              <Link href="/mentor/sessions" className="block p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100">
                <h3 className="font-bold text-green-900">My Sessions</h3>
                <p className="text-sm text-green-700">View your scheduled sessions</p>
              </Link>
            </div>
          )}

          {(session?.user?.role === 'admin' || session?.user?.role === 'program_manager') && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link href="/admin/dashboard" className="block p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100">
                <h3 className="font-bold text-blue-900">Analytics</h3>
                <p className="text-sm text-blue-700">View platform metrics</p>
              </Link>
              <Link href="/admin/matches" className="block p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100">
                <h3 className="font-bold text-green-900">Manage Matches</h3>
                <p className="text-sm text-green-700">Override and curate matches</p>
              </Link>
              <Link href="/admin/settings" className="block p-4 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100">
                <h3 className="font-bold text-purple-900">Settings</h3>
                <p className="text-sm text-purple-700">System configuration</p>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
