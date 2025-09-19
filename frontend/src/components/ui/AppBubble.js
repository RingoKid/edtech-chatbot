import React from 'react';
import Box from '@mui/material/Box';
import { styled, alpha } from '@mui/material/styles';
import Typography from '@mui/material/Typography';

const Bubble = styled(Box)(({ theme }) => ({
  borderRadius: 12,
  padding: theme.spacing(3.5),
  boxSizing: 'border-box',
  width: '100%',
  overflow: 'hidden',
  position: 'relative',
  background: theme.palette.mode === 'dark'
    ? 'linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02))'
    : theme.palette.background.paper,
  border: theme.palette.mode === 'dark' ? `1px solid ${alpha(theme.palette.common.white, 0.08)}` : `1px solid ${alpha(theme.palette.common.black, 0.06)}`,
  boxShadow: theme.palette.mode === 'dark' ? '0 8px 30px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.02)' : '0 6px 18px rgba(0,0,0,0.06)',
  backdropFilter: 'blur(6px)',
  color: 'rgba(255,255,255,0.94)'
}));

export default function AppBubble({ title, children, sx }) {
  return (
    <Bubble sx={{ ...sx }}>
      {title ? <Typography variant="h6" fontWeight={800} gutterBottom sx={{ color: 'text.primary' }}>{title}</Typography> : null}
      {children}
    </Bubble>
  );
}
