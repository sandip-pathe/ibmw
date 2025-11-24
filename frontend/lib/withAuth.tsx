import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function withAuth<T>(Component: React.ComponentType<T>) {
  return function Protected(props: T) {
    const router = useRouter();
    useEffect(() => {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("access_token")
          : null;
      if (!token) {
        router.replace("/auth/signin");
      }
    }, [router]);
    return <Component {...props} />;
  };
}
