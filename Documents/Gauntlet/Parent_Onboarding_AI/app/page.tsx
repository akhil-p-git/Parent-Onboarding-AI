export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
      <div className="container text-center">
        <h1 className="text-4xl font-bold mb-4 text-gray-900">
          Office Hours Matching Tool
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl">
          AI-powered mentor-mentee matching platform for Capital Factory
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="p-6 bg-white rounded-lg shadow-md border border-gray-200">
            <h2 className="text-xl font-semibold mb-2">For Founders</h2>
            <p className="text-gray-600 mb-4">
              Get matched with mentors who have the expertise you need
            </p>
            <a href="/auth/signin" className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Get Started
            </a>
          </div>

          <div className="p-6 bg-white rounded-lg shadow-md border border-gray-200">
            <h2 className="text-xl font-semibold mb-2">For Mentors</h2>
            <p className="text-gray-600 mb-4">
              Share your expertise and make an impact on startup founders
            </p>
            <a href="/auth/signin" className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Join as Mentor
            </a>
          </div>

          <div className="p-6 bg-white rounded-lg shadow-md border border-gray-200">
            <h2 className="text-xl font-semibold mb-2">For Admins</h2>
            <p className="text-gray-600 mb-4">
              Monitor platform analytics and manage matches
            </p>
            <a href="/auth/signin" className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Admin Portal
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
