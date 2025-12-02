import type { Metadata } from 'next';
import '@/app/globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Office Hours Matching Tool',
  description: 'AI-powered mentor-mentee matching platform for Capital Factory',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
