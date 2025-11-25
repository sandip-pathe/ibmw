import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const session = request.cookies.get("stackframe_user_id");
  const isProtected = ["/dashboard", "/repos", "/regulations"].some((path) =>
    request.nextUrl.pathname.startsWith(path)
  );

  // Redirect unauthenticated users from protected routes
  if (!session && isProtected) {
    return NextResponse.redirect(new URL("/handler/sign-in", request.url));
  }

  // Set SSR header for hydration
  const response = NextResponse.next();
  if (session) {
    response.headers.set("x-stackframe-auth", "true");
  } else {
    response.headers.set("x-stackframe-auth", "false");
  }
  return response;
}

export const config = {
  matcher: ["/dashboard", "/repos/:path*", "/regulations/:path*", "/"],
};
