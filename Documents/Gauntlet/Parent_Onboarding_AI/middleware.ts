import { getToken } from 'next-auth/jwt';
import { NextRequest, NextResponse } from 'next/server';

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*', '/mentor/:path*', '/founder/:path*'],
};

export async function middleware(request: NextRequest) {
  const token = await getToken({ req: request });
  const pathname = request.nextUrl.pathname;

  // Require authentication
  if (!token) {
    return NextResponse.redirect(new URL('/auth/signin', request.url));
  }

  // Admin routes
  if (pathname.startsWith('/admin')) {
    if (token.role !== 'admin' && token.role !== 'program_manager') {
      return NextResponse.redirect(new URL('/auth/unauthorized', request.url));
    }
  }

  // Mentor routes
  if (pathname.startsWith('/mentor')) {
    if (token.role !== 'mentor') {
      return NextResponse.redirect(new URL('/auth/unauthorized', request.url));
    }
  }

  // Founder routes
  if (pathname.startsWith('/founder')) {
    if (token.role !== 'founder') {
      return NextResponse.redirect(new URL('/auth/unauthorized', request.url));
    }
  }

  return NextResponse.next();
}
