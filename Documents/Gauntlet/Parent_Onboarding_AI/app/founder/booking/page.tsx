'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function BookingPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState<any>(null);
  const [selectedTime, setSelectedTime] = useState('');

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  const handleFindMatches = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ founderId: session?.user?.id }),
      });

      const data = await response.json();
      if (data.matches) {
        setMatches(data.matches);
        setStep(2);
      }
    } catch (error) {
      console.error('Failed to find matches:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMentor = (mentor: any) => {
    setSelectedMentor(mentor);
    setStep(3);
  };

  const handleBookSession = async () => {
    if (!selectedMentor || !selectedTime) return;

    setLoading(true);
    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mentorId: selectedMentor.mentorId,
          founderId: session?.user?.id,
          startTime: selectedTime,
          status: 'scheduled',
        }),
      });

      if (response.ok) {
        router.push('/founder/sessions');
      }
    } catch (error) {
      console.error('Failed to book session:', error);
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading') {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Book a Mentor Session</h1>

        {/* Step 1: Find Matches */}
        {step === 1 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Step 1: Find Mentors</h2>
            <p className="text-gray-600 mb-6">
              We&apos;ll find mentors that match your needs based on expertise, industry, and company stage.
            </p>
            <button
              onClick={handleFindMatches}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Finding matches...' : 'Find Mentors'}
            </button>
          </div>
        )}

        {/* Step 2: Select Mentor */}
        {step === 2 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Step 2: Select a Mentor</h2>
            {matches.length === 0 ? (
              <p className="text-gray-600">No mentors available. Try again later.</p>
            ) : (
              <div className="space-y-4">
                {matches.slice(0, 5).map((match) => (
                  <div key={match.mentorId} className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold">Mentor {match.mentorId}</h3>
                        <p className="text-sm text-gray-600">Overall Match: {match.overallScore}%</p>
                        <div className="mt-2 text-xs text-gray-500">
                          <p>Expertise: {match.expertiseScore}%</p>
                          <p>Industry: {match.industryScore}%</p>
                          <p>Stage: {match.stageScore}%</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleSelectMentor(match)}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Select
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Select Time */}
        {step === 3 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Step 3: Choose Time</h2>
            <p className="text-gray-600 mb-4">Select when you&apos;d like to meet (demo: selecting any date)</p>
            <input
              type="datetime-local"
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded mb-4"
            />
            <div className="flex gap-4">
              <button
                onClick={() => setStep(2)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={handleBookSession}
                disabled={loading || !selectedTime}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Booking...' : 'Confirm Booking'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
