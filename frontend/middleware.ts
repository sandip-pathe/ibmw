import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public paths that don't require auth
  const publicPaths = [
    "/",
    "/auth/signin",
    "/auth/signup",
    "/handler",
    "/auth/github/callback",
  ];

  // Check if the current path is public
  if (publicPaths.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  // For Stack Auth, the session is often handled via cookies/headers that the client lib manages.
  // However, for simple edge protection, we verify if the stack token cookie exists.
  // Note: The actual robust check happens in the layout/component via useUser()

  const hasSession = request.cookies.has("stack-auth-token"); // Standard Stack cookie name

  if (!hasSession && !pathname.startsWith("/auth")) {
    const url = request.nextUrl.clone();
    url.pathname = "/auth/signin";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|public).*)",
  ],
};
