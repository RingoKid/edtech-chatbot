# Frontend Integration Guide - JWT Authentication System

## Overview

This guide provides a comprehensive walkthrough for integrating the JWT authentication system into the frontend application. The authentication system uses a **dual-token approach** with access tokens and refresh tokens to provide secure, stateless authentication.

### How the Authentication System Works

The authentication system implements the following security features:

1. **Access Tokens (JWT)**: Short-lived tokens (30 minutes) sent in `Authorization` headers
2. **Refresh Tokens**: Long-lived tokens (7 days) stored as httpOnly cookies for security
3. **Token Rotation**: New refresh tokens are issued on each refresh to prevent replay attacks
4. **Token Revocation**: Refresh tokens are tracked in DynamoDB and can be revoked (logout)
5. **Role-Based Access**: Tokens include user roles (USER/ADMIN) for authorization

**Security Benefits:**
- Access tokens are short-lived, limiting exposure if compromised
- Refresh tokens are httpOnly cookies, preventing XSS attacks
- Tokens are stored in DynamoDB for revocation tracking
- Automatic token cleanup via DynamoDB TTL

---

## Prerequisites

### 1. Initialize the Database

**IMPORTANT:** Before using the authentication system, you **MUST** initialize the DynamoDB tables. Run this command from the project root:

```bash
docker compose exec backend python scripts/init_db.py
```

This creates two tables:
- **EdTechChatbotTable-local** - Stores user profiles and refresh tokens with GSI1 for email lookups
- **EdTechChatbotCheckpoints-local** - Stores LangGraph conversation checkpoints

Expected output:
```
✅ Loaded environment from .env.local
🚀 Initializing DynamoDB tables for environment: AppEnv.LOCAL
⏳ Creating table EdTechChatbotTable-local...
✅ Table EdTechChatbotTable-local created successfully with GSI1 and TTL enabled
⏳ Creating checkpoint table EdTechChatbotCheckpoints-local...
✅ Checkpoint table EdTechChatbotCheckpoints-local created successfully

✨ Database initialization complete!
📊 Main table: EdTechChatbotTable-local
📊 Checkpoint table: EdTechChatbotCheckpoints-local
```

If tables already exist, the script will detect them and skip creation.

---

## API Endpoints Overview

All authentication endpoints are under the `/auth` prefix. The backend API runs on `http://localhost:8000`.

### Authentication Flow Order

**1. Sign Up (New User Registration)**
```
POST /auth/signup
```

**2. Login (Get Tokens)**
```
POST /auth/login
```

**3. Access Protected Routes (Using Access Token)**
```
GET /auth/me
Authorization: Bearer <access_token>
```

**4. Refresh Access Token (When Expired)**
```
POST /auth/refresh
Cookie: refresh_token=<refresh_token>
```

**5. Logout (Revoke Current Token)**
```
POST /auth/logout
Authorization: Bearer <access_token>
Cookie: refresh_token=<refresh_token>
```

**6. Logout All Devices (Revoke All Tokens)**
```
POST /auth/logout-all
Authorization: Bearer <access_token>
```

---

## Detailed API Usage with Examples

### 1. Sign Up - `POST /auth/signup`

Create a new user account.

**Request:**
```json
POST http://localhost:8000/auth/signup
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "role": "USER"
}
```

**Response (201 Created):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@example.com",
  "full_name": "John Doe",
  "role": "USER",
  "created_at": "2025-11-10T14:30:00.000000+00:00"
}
```

**Error Response (409 Conflict - Email Already Exists):**
```json
{
  "detail": "Email already registered"
}
```

**Validation Rules:**
- Email must be valid format
- Password minimum 8 characters
- Role must be "USER" or "ADMIN" (defaults to "USER")
- Full name required (min 1 character)

---

### 2. Login - `POST /auth/login`

Authenticate user and receive access token.

**Request (OAuth2 Form Format):**
```
POST http://localhost:8000/auth/login
Content-Type: application/x-www-form-urlencoded

username=student@example.com&password=securepassword123
```

**Note:** The OAuth2 spec uses `username` field, but we accept email addresses in this field.

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Additionally, a httpOnly cookie is set:**
```
Set-Cookie: refresh_token=<jwt_token>; HttpOnly; SameSite=Lax; Max-Age=604800; Path=/
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Incorrect email or password"
}
```

**JavaScript/Fetch Example:**
```javascript
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'student@example.com',
    password: 'securepassword123'
  }),
  credentials: 'include' // IMPORTANT: Include cookies
});

const data = await response.json();
// Store access_token in memory or state management
localStorage.setItem('access_token', data.access_token);
```

---

### 3. Get Current User - `GET /auth/me`

Retrieve authenticated user's information.

**Request:**
```
GET http://localhost:8000/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@example.com",
  "full_name": "John Doe",
  "role": "USER",
  "created_at": "2025-11-10T14:30:00.000000+00:00"
}
```

**Error Response (401 Unauthorized - Invalid/Expired Token):**
```json
{
  "detail": "Could not validate credentials"
}
```

**JavaScript/Fetch Example:**
```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const user = await response.json();
```

---

### 4. Refresh Token - `POST /auth/refresh`

Get a new access token using the refresh token (automatic token rotation).

**Request:**
```
POST http://localhost:8000/auth/refresh
Cookie: refresh_token=<jwt_token>
```

**Note:** The refresh token is automatically sent from the httpOnly cookie. No manual header needed.

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Additionally, a NEW httpOnly cookie is set (token rotation):**
```
Set-Cookie: refresh_token=<new_jwt_token>; HttpOnly; SameSite=Lax; Max-Age=604800; Path=/
```

**Error Response (401 Unauthorized - No Refresh Token):**
```json
{
  "detail": "No refresh token provided"
}
```

**Error Response (401 Unauthorized - Invalid/Revoked Token):**
```json
{
  "detail": "Refresh token revoked or expired"
}
```

**JavaScript/Fetch Example:**
```javascript
const response = await fetch('http://localhost:8000/auth/refresh', {
  method: 'POST',
  credentials: 'include' // IMPORTANT: Include cookies
});

if (response.ok) {
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
} else {
  // Redirect to login if refresh fails
  window.location.href = '/login';
}
```

---

### 5. Logout - `POST /auth/logout`

Logout from current device by revoking the refresh token.

**Request:**
```
POST http://localhost:8000/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Cookie: refresh_token=<jwt_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**The httpOnly cookie is cleared:**
```
Set-Cookie: refresh_token=; HttpOnly; Max-Age=0; Path=/
```

**JavaScript/Fetch Example:**
```javascript
const accessToken = localStorage.getItem('access_token');

await fetch('http://localhost:8000/auth/logout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  credentials: 'include' // IMPORTANT: Include cookies
});

// Clear local token
localStorage.removeItem('access_token');
window.location.href = '/login';
```

---

### 6. Logout All Devices - `POST /auth/logout-all`

Logout from all devices by revoking all refresh tokens for the user.

**Request:**
```
POST http://localhost:8000/auth/logout-all
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "Logged out from 3 device(s)"
}
```

**Use Cases:**
- Password change
- Security concern (suspected compromise)
- Account cleanup

**JavaScript/Fetch Example:**
```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/auth/logout-all', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
alert(data.message); // "Logged out from 3 device(s)"

// Clear local token and redirect
localStorage.removeItem('access_token');
window.location.href = '/login';
```

---

## Frontend Integration TODO (React + Vite)

### Step 1: Install Required Dependencies

```bash
npm install axios jwt-decode
```

### Step 2: Create Authentication Context

Create `src/contexts/AuthContext.jsx`:

```javascript
import { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(localStorage.getItem('access_token'));

  // Configure axios defaults
  const api = axios.create({
    baseURL: 'http://localhost:8000',
    withCredentials: true, // Important: Send cookies
  });

  // Add access token to requests
  api.interceptors.request.use((config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  });

  // Handle 401 errors with token refresh
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      // If 401 and haven't retried, try to refresh token
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const { data } = await axios.post(
            'http://localhost:8000/auth/refresh',
            {},
            { withCredentials: true }
          );

          setAccessToken(data.access_token);
          localStorage.setItem('access_token', data.access_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout user
          logout();
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  // Load user on mount
  useEffect(() => {
    const loadUser = async () => {
      if (accessToken) {
        try {
          const { data } = await api.get('/auth/me');
          setUser(data);
        } catch (error) {
          console.error('Failed to load user:', error);
          setAccessToken(null);
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [accessToken]);

  const signup = async (email, password, fullName, role = 'USER') => {
    const { data } = await api.post('/auth/signup', {
      email,
      password,
      full_name: fullName,
      role,
    });
    return data;
  };

  const login = async (email, password) => {
    const { data } = await axios.post(
      'http://localhost:8000/auth/login',
      new URLSearchParams({ username: email, password }),
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        withCredentials: true,
      }
    );

    setAccessToken(data.access_token);
    localStorage.setItem('access_token', data.access_token);

    // Load user info
    const userResponse = await api.get('/auth/me');
    setUser(userResponse.data);

    return data;
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setAccessToken(null);
      setUser(null);
      localStorage.removeItem('access_token');
    }
  };

  const logoutAll = async () => {
    await api.post('/auth/logout-all');
    setAccessToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signup,
        login,
        logout,
        logoutAll,
        api, // Expose configured axios instance
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Step 3: Wrap Your App with AuthProvider

Update `src/main.jsx`:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
```

### Step 4: Create Protected Route Component

Create `src/components/ProtectedRoute.jsx`:

```javascript
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};
```

### Step 5: Create Login Component Example

Create `src/pages/Login.jsx`:

```javascript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <button type="submit">Login</button>
    </form>
  );
};
```

### Step 6: Use Protected Routes in App

Update `src/App.jsx`:

```javascript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { ProtectedRoute } from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="ADMIN">
              <AdminPanel />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

### Step 7: Making API Calls to Protected Endpoints

Use the `api` instance from `useAuth()` for automatic token handling:

```javascript
import { useAuth } from '../contexts/AuthContext';

function SomeComponent() {
  const { api } = useAuth();

  const fetchProtectedData = async () => {
    try {
      const { data } = await api.get('/some-protected-endpoint');
      console.log(data);
    } catch (error) {
      console.error('API call failed:', error);
    }
  };

  return <button onClick={fetchProtectedData}>Fetch Data</button>;
}
```

### Step 8: Additional Recommendations

**1. Token Expiry Handling**
- Access tokens expire after 30 minutes
- The axios interceptor automatically refreshes tokens on 401 errors
- Refresh tokens expire after 7 days (requires re-login)

**2. Security Best Practices**
- Never store tokens in localStorage in production (use memory/state only for access tokens)
- Always use `credentials: 'include'` for cookie handling
- Enable CORS properly on backend for production
- Use HTTPS in production (refresh tokens will have `secure: true`)

**3. Error Handling**
- Show user-friendly messages for 401 (authentication failed)
- Show user-friendly messages for 409 (email already exists)
- Implement retry logic for network failures

**4. User Experience**
- Show loading states during authentication
- Implement "Remember me" functionality (optional)
- Add password strength indicator on signup
- Implement email verification (future enhancement)

---

## Testing the Integration

### Manual Testing Steps

1. **Initialize Database**
   ```bash
   docker compose exec backend python scripts/init_db.py
   ```

2. **Start Backend (if not running)**
   ```bash
   docker compose up -d backend
   ```

3. **Test Signup**
   ```bash
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123","full_name":"Test User","role":"USER"}'
   ```

4. **Test Login**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=password123" \
     -c cookies.txt
   ```

5. **Test Protected Endpoint**
   ```bash
   # Extract access_token from login response, then:
   curl -X GET http://localhost:8000/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```

6. **Test Refresh**
   ```bash
   curl -X POST http://localhost:8000/auth/refresh \
     -b cookies.txt -c cookies.txt
   ```

---

## Troubleshooting

### Issue: "No refresh token provided"
**Cause:** Cookies not being sent/received
**Solution:** Ensure `credentials: 'include'` is set in fetch/axios and CORS allows credentials

### Issue: "Could not validate credentials"
**Cause:** Access token expired or invalid
**Solution:** Implement automatic token refresh with axios interceptor

### Issue: Tables don't exist
**Cause:** Database not initialized
**Solution:** Run `docker compose exec backend python scripts/init_db.py`

### Issue: CORS errors
**Cause:** Backend CORS not configured for frontend origin
**Solution:** Add frontend URL to CORS allowed origins in backend settings

---

## Summary

This authentication system provides a secure, production-ready JWT implementation with:
- ✅ Dual-token approach (access + refresh)
- ✅ Automatic token rotation
- ✅ httpOnly cookies for refresh tokens (XSS protection)
- ✅ Token revocation support (logout functionality)
- ✅ Role-based access control
- ✅ DynamoDB-backed user and token storage

Follow the TODO steps above to integrate into your React + Vite frontend!
