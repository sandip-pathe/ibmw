import React, { createContext, useContext, useState, ReactNode } from "react";

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  loading: true,
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const getInitialAuth = () => {
    if (typeof window === "undefined") return false;
    const match = document.cookie.match(/(?:^|; )stackframe_user_id=([^;]*)/);
    return !!(match && match[1]);
  };
  const [isAuthenticated] = useState(getInitialAuth());
  const [loading] = useState(false);

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
