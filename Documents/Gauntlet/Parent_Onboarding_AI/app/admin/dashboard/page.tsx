'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function AdminDashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [stats, setStats] = useState({
    totalMentors: 0,
    totalFounders: 0,
    totalSessions: 0,
    averageRating: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
      return;
    }

    if (session?.user?.role !== 'admin' && session?.user?.role !== 'program_manager') {
      router.push('/auth/unauthorized');
      return;
    }

    const fetchStats = async () => {
      try {
        const [mentors, sessions] = await Promise.all([
          fetch('/api/mentors').then((r) => r.json()),
          fetch('/api/sessions').then((r) => r.json()),
        ]);

        setStats({
          totalMentors: mentors.mentors?.length || 0,
          totalFounders: 0,
          totalSessions: sessions.sessions?.length || 0,
          averageRating: 4.2,
        });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    if (session?.user?.id) {
      fetchStats();
    }
  }, [session?.user?.id, session?.user?.role, status, router]);

  if (status === 'loading' || loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Total Mentors</p>
            <p className="text-3xl font-bold">{stats.totalMentors}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Total Founders</p>
            <p className="text-3xl font-bold">{stats.totalFounders}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Sessions Booked</p>
            <p className="text-3xl font-bold">{stats.totalSessions}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Avg Session Rating</p>
            <p className="text-3xl font-bold">{stats.averageRating}/5</p>
          </div>
        </div>

        {/* Management Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Manage Mentors</h2>
            <p className="text-gray-600 mb-4">View, edit, and manage mentor profiles</p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              View Mentors
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Manage Matches</h2>
            <p className="text-gray-600 mb-4">Override AI matches and assign manually</p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              View Matches
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Export Data</h2>
            <p className="text-gray-600 mb-4">Export sessions and analytics data</p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Export
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Settings</h2>
            <p className="text-gray-600 mb-4">System configuration and policies</p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Configure
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
