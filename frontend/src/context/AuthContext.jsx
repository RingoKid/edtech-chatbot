import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { auth as authApi } from "../api";
import { setAccessToken, clearAccessToken } from "../api/client";

const TOKEN_KEY = "access_token";

const getStoredToken = () => {
  if (typeof window === "undefined") {
    return { token: null, storage: null };
  }
  const localToken = window.localStorage.getItem(TOKEN_KEY);
  if (localToken) {
    return { token: localToken, storage: "local" };
  }
  const sessionToken = window.sessionStorage.getItem(TOKEN_KEY);
  if (sessionToken) {
    return { token: sessionToken, storage: "session" };
  }
  return { token: null, storage: null };
};

export const authContext = createContext(undefined);

export const AuthProvider = ({ children }) => {
  const [tokenState, setTokenState] = useState(() => getStoredToken());
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [authError, setAuthError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const persistToken = useCallback((value, storagePreference = "local") => {
    if (typeof window === "undefined") {
      return;
    }

    if (!value) {
      window.localStorage.removeItem(TOKEN_KEY);
      window.sessionStorage.removeItem(TOKEN_KEY);
      clearAccessToken();
      setTokenState({ token: null, storage: null });
      return;
    }

    if (storagePreference === "session") {
      window.sessionStorage.setItem(TOKEN_KEY, value);
      window.localStorage.removeItem(TOKEN_KEY);
    } else {
      window.localStorage.setItem(TOKEN_KEY, value);
      window.sessionStorage.removeItem(TOKEN_KEY);
      storagePreference = "local";
    }

    setAccessToken(value);
    setTokenState({ token: value, storage: storagePreference });
  }, []);

  const dropSession = useCallback(() => {
    persistToken(null);
    setUser(null);
  }, [persistToken]);

  useEffect(() => {
    if (tokenState.token) {
      setAccessToken(tokenState.token);
    } else {
      clearAccessToken();
    }
  }, [tokenState.token]);

  const fetchProfile = useCallback(async () => {
    const profile = await authApi.me();
    setUser(profile);
    setAuthError(null);
    return profile;
  }, []);

  const refreshSession = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const response = await authApi.refresh();
      const storagePreference = tokenState.storage ?? "local";
      persistToken(response.access_token, storagePreference);
      return await fetchProfile();
    } catch (error) {
      dropSession();
      setAuthError(error);
      throw error;
    } finally {
      setIsRefreshing(false);
    }
  }, [dropSession, fetchProfile, persistToken, tokenState.storage]);

  useEffect(() => {
    const bootstrap = async () => {
      if (!tokenState.token) {
        setInitializing(false);
        return;
      }

      try {
        await fetchProfile();
      } catch (error) {
        try {
          await refreshSession();
        } catch (refreshError) {
          dropSession();
          setAuthError(refreshError);
        }
      } finally {
        setInitializing(false);
      }
    };

    bootstrap();
  }, [dropSession, fetchProfile, refreshSession, tokenState.token]);

  const login = useCallback(
    async ({ email, password, remember = true }) => {
      setAuthError(null);
      const { access_token: accessTokenResponse } = await authApi.login({
        email,
        password,
      });
      persistToken(accessTokenResponse, remember ? "local" : "session");
      return await fetchProfile();
    },
    [fetchProfile, persistToken]
  );

  const signup = useCallback(
    async ({ fullName, email, password, role, remember = true }) => {
      setAuthError(null);
      await authApi.signup({
        email,
        password,
        full_name: fullName,
        role,
      });
      return await login({ email, password, remember });
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // Swallow network/auth errors so the UI can still reset
    } finally {
      dropSession();
    }
  }, [dropSession]);

  const value = useMemo(
    () => ({
      user,
      initializing,
      authError,
      isRefreshing,
      accessToken: tokenState.token,
      isAuthenticated: Boolean(user),
      login,
      signup,
      logout,
      refreshSession,
      setUser,
    }),
    [
      authError,
      initializing,
      isRefreshing,
      login,
      logout,
      refreshSession,
      signup,
      tokenState.token,
      user,
    ]
  );

  return <authContext.Provider value={value}>{children}</authContext.Provider>;
};
