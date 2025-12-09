import { Navigate, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";
import useAuth from "../hooks/useAuth";

const RequireAuth = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, initializing, isRefreshing } = useAuth();

  if (initializing || isRefreshing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center rounded-full bg-white px-4 py-2 shadow">
            <Loader2 className="w-4 h-4 mr-2 animate-spin text-primary-600" />
            <span className="text-sm font-semibold text-gray-700">
              Restoring your teaching workspace...
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            One moment while we verify your classroom session.
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
};

export default RequireAuth;
