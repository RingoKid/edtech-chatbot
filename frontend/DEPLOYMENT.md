# Frontend Deployment Configuration

## Environment Setup

### Local Development
1. Copy `.env.example` to `.env.local`
2. Update URLs if needed:
   ```bash
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   VITE_WS_BASE_URL=ws://localhost:8000
   ```

### Production Deployment
1. Copy `.env.example` to `.env.production`
2. Update with your production API URLs:
   ```bash
   VITE_API_BASE_URL=https://your-api-domain.com/api/v1
   VITE_WS_BASE_URL=wss://your-api-domain.com
   ```

## Configuration Details

### API URLs
- **Local**: Uses `localhost:8000` for development
- **Production**: Falls back to relative URLs or uses environment variables
- **Environment Variables**:
  - `VITE_API_BASE_URL`: Full HTTP API base URL
  - `VITE_WS_BASE_URL`: WebSocket base URL (without the endpoint path)

### Anti-Spam Protection
- API calls are protected against rapid repeated execution
- 1-second cooldown between identical requests
- WebSocket connections have built-in reconnection logic

## Testing

### Run Tests
```bash
npm test                 # Run tests once
npm run test:ui         # Run tests with UI
npm run test:coverage   # Run tests with coverage report
```

### Test Coverage
- Component rendering and interaction
- API call protection hooks
- Environment configuration
- WebSocket connection handling

## Build and Deploy

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview  # Preview production build locally
```

### Environment Detection
The app automatically detects:
- Development mode: Uses localhost URLs as fallback
- Production mode: Uses relative URLs or environment-specified URLs
- WebSocket protocol: Automatically selects `ws://` or `wss://` based on page protocol

## Troubleshooting

### Common Issues
1. **API calls using localhost in production**
   - Ensure `.env.production` has correct URLs
   - Check that environment variables are loaded by the build system

2. **Repeated API calls**
   - API protection hooks prevent rapid repeated calls
   - Check browser dev tools for excessive network requests

3. **WebSocket connection failures**
   - Verify WebSocket URL matches your backend
   - Check if WebSocket endpoint is accessible
   - Browser dev tools will show WebSocket connection status

### Debug Mode
In development, the app shows additional debug information:
- API connection status
- WebSocket connection state
- Environment configuration details