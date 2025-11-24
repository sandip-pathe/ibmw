"use client";

import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      {/* Logo */}
      <Link href="/" className="absolute top-6 left-6">
        <div className="w-8 h-8 flex items-center">
          <svg viewBox="0 0 76 65" fill="white">
            <path d="M37.5274 0L75.0548 65H0L37.5274 0Z" />
          </svg>
        </div>
      </Link>

      <div className="w-full max-w-[340px]">
        <h1 className="text-white text-[32px] font-semibold text-center mb-8">
          Log in to Anaya
        </h1>

        {/* Neon Auth (includes GitHub & Google) */}
        <Link href="/handler/sign-in" passHref legacyBehavior>
          <Button className="w-full h-12 mb-4 bg-[#00e599] hover:bg-[#00c47a] text-black font-medium rounded-md flex items-center justify-center gap-3">
            {/* Neon logo SVG */}
            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
              <circle cx="16" cy="16" r="16" fill="#00e599" />
              <path
                d="M10 16c0-3.314 2.686-6 6-6s6 2.686 6 6-2.686 6-6 6-6-2.686-6-6z"
                fill="#fff"
              />
            </svg>
            Continue with Neon, GitHub, or Google
          </Button>
        </Link>

        {/* Divider */}
        <div className="text-center text-gray-500 text-sm mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/auth/signup" className="text-white hover:underline">
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
}
