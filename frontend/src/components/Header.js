import React, { useState, useRef } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Button from './ui/AppButton';
import Box from '@mui/material/Box';
import MenuIcon from '@mui/icons-material/Menu';
// header styles are progressively migrated to MUI; keep CSS file for legacy classes

export default function Header({ mode = 'dark', onToggleTheme = () => {} }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => location && location.pathname === path;

  const closeTimerRef = useRef(null);
  const [forcedActive, setForcedActive] = useState(null);

  const openMenu = (el) => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setAnchorEl(el);
  };

  const scheduleClose = (delay = 1000) => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    closeTimerRef.current = setTimeout(() => setAnchorEl(null), delay);
  };

  const handleMenuClose = () => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setAnchorEl(null);
  };

  // Keep a forced active state synced with location to ensure visual 'clicked' state
  React.useEffect(() => {
    if (location && location.pathname === '/best-practices') {
      setForcedActive('/best-practices');
    } else {
      setForcedActive(null);
    }
  }, [location]);

  return (
  <AppBar position="fixed" color="default" elevation={0} sx={{ bgcolor: 'transparent', boxShadow: 'none', backdropFilter: 'none' }}>
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: '72px' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="h6" component={RouterLink} to="/" sx={{ textDecoration: 'none', color: '#fff', fontWeight: 800 }}>
            Language For Composing
          </Typography>
        </Box>

        <Box sx={{ display: { xs: 'none', sm: 'flex' }, gap: 1, alignItems: 'center' }}>
          <Button component={RouterLink} to="/" variantStyle={isActive('/') ? 'primary' : 'ghost'} sx={{ px: 2, border: '1px solid rgba(255,255,255,0.18)', borderRadius: 8 }}>
            Home
          </Button>
          <div
            onMouseEnter={(e) => openMenu(e.currentTarget)}
            onMouseLeave={() => scheduleClose(1000)}
            style={{ display: 'inline-block' }}
          >
            <Button
              onClick={() => { setForcedActive('/best-practices'); setAnchorEl(null); navigate('/best-practices'); }}
              aria-controls="videos-menu"
              aria-haspopup="true"
              variantStyle={(isActive('/best-practices') || forcedActive === '/best-practices') ? 'primary' : 'ghost'}
              sx={{
                px: 2,
                border: '1px solid rgba(255,255,255,0.18)',
                borderRadius: 8,
                '&&:hover': {
                  background: '#ffffff',
                  color: '#07070a',
                  transform: 'scale(1.04)'
                }
              }}
            >
              Best Practices Modeled
            </Button>
            <Menu
              id="videos-menu"
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              MenuListProps={{ 'aria-labelledby': 'basic-button' }}
              MenuProps={{
                onMouseEnter: () => {
                  if (closeTimerRef.current) {
                    clearTimeout(closeTimerRef.current);
                    closeTimerRef.current = null;
                  }
                },
                onMouseLeave: () => scheduleClose(1000)
              }}
            >
              <MenuItem component={RouterLink} to="/videos/handwriting" onClick={handleMenuClose}>Handwriting & Spelling</MenuItem>
              <MenuItem component={RouterLink} to="/videos/vocab" onClick={handleMenuClose}>Vocabulary & Syntax</MenuItem>
              <MenuItem component={RouterLink} to="/videos/idea-org" onClick={handleMenuClose}>Idea Organization & Generation</MenuItem>
            </Menu>
          </div>
          <Button component={RouterLink} to="/ai-tool" variantStyle={isActive('/ai-tool') ? 'primary' : 'ghost'} sx={{ px: 2, border: '1px solid rgba(255,255,255,0.18)', borderRadius: 8 }}>
            AI Composition Tool
          </Button>
        </Box>

        <Box sx={{ display: { xs: 'flex', sm: 'none' } }}>
          <IconButton edge="end" color="inherit" aria-label="menu" onClick={() => setMobileOpen((s) => !s)}>
            <MenuIcon />
          </IconButton>
        </Box>

        <Box sx={{ ml: 2, display: { xs: 'none', sm: 'flex' }, alignItems: 'center' }}>
          <FormControlLabel
            control={<Switch checked={mode === 'light'} onChange={onToggleTheme} color="default" />}
            label={mode === 'light' ? 'Light' : 'Dark'}
            sx={{ color: '#fff', ml: 1 }}
          />
        </Box>

        {/* Mobile expanded menu */}
        {mobileOpen && (
          <Box sx={{ position: 'absolute', right: 12, top: '100%', mt: 1, bgcolor: 'background.paper', boxShadow: 3, borderRadius: 1, display: { xs: 'block', sm: 'none' } }}>
            <MenuItem component={RouterLink} to="/" onClick={() => setMobileOpen(false)}>Home</MenuItem>
            <MenuItem component={RouterLink} to="/best-practices" onClick={() => setMobileOpen(false)}>Best Practices Modeled</MenuItem>
            <MenuItem component={RouterLink} to="/ai-tool" onClick={() => setMobileOpen(false)}>AI Composition Tool</MenuItem>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}
