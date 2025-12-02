'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function MentorProfilePage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState({
    expertise: '',
    industryFocus: '',
    stages: '',
    bio: '',
    yearsOfExperience: 0,
    maxCapacity: 5,
  });

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`/api/mentors/${session?.user?.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Expertise: profile.expertise.split(',').map((e) => e.trim()),
          'Industry Focus': profile.industryFocus.split(',').map((i) => i.trim()),
          Stages: profile.stages.split(',').map((s) => s.trim()),
          Bio: profile.bio,
          'Years of Experience': parseInt(String(profile.yearsOfExperience)),
          'Max Capacity': profile.maxCapacity,
        }),
      });

      if (response.ok) {
        alert('Profile updated successfully!');
      }
    } catch (error) {
      console.error('Failed to update profile:', error);
      alert('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading') {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold mb-6">My Mentor Profile</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Expertise (comma-separated)</label>
            <input
              type="text"
              value={profile.expertise}
              onChange={(e) => setProfile({ ...profile, expertise: e.target.value })}
              placeholder="e.g., Product Strategy, Growth Marketing, Fundraising"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Industry Focus (comma-separated)</label>
            <input
              type="text"
              value={profile.industryFocus}
              onChange={(e) => setProfile({ ...profile, industryFocus: e.target.value })}
              placeholder="e.g., SaaS, E-commerce, FinTech"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Company Stages (comma-separated)</label>
            <input
              type="text"
              value={profile.stages}
              onChange={(e) => setProfile({ ...profile, stages: e.target.value })}
              placeholder="e.g., idea, mvp, growth, scaling"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Bio</label>
            <textarea
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              placeholder="Tell founders about your background and how you can help..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Years of Experience</label>
              <input
                type="number"
                value={profile.yearsOfExperience}
                onChange={(e) => setProfile({ ...profile, yearsOfExperience: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Max Sessions per Month</label>
              <input
                type="number"
                value={profile.maxCapacity}
                onChange={(e) => setProfile({ ...profile, maxCapacity: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        </form>
      </div>
    </div>
  );
}
