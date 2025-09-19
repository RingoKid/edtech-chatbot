import React from 'react';
import Button from '@mui/material/Button';
import { styled } from '@mui/material/styles';

// A polished, Instagram-level style button abstraction. Usage:
// <AppButton variantStyle="primary" startIcon={<Icon/>}>Text</AppButton>
const Gradient = styled(Button)(({ theme }) => ({
  borderRadius: 999,
  padding: '10px 18px',
  textTransform: 'none',
  fontWeight: 700,
  letterSpacing: '0.2px',
  boxShadow: theme.palette.mode === 'dark' ? '0 6px 18px rgba(10,10,10,0.12)' : '0 6px 18px rgba(0,0,0,0.06)',
  transition: 'transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease',
  '&:hover': {
    transform: 'scale(1.04)',
    boxShadow: theme.palette.mode === 'dark' ? '0 12px 30px rgba(10,10,10,0.18)' : '0 12px 30px rgba(0,0,0,0.12)'
  }
}));

export default function AppButton({ variantStyle = 'primary', children, sx, ...props }) {
  let style = {};
  // Default: buttons (text buttons) should have white text on black background
  // Hover should invert to white background and black text with a zoom effect.
  // The 'primary' variant here is used as the active/selected state: show white background and black text
  if (variantStyle === 'primary') {
    // Active/selected state: white bg, black text; on hover only zoom
    style = {
      background: theme => (theme.palette.mode === 'dark' ? '#ffffff' : '#ffffff'),
      color: theme => (theme.palette.mode === 'dark' ? '#07070a' : '#07070a'),
      boxShadow: theme => (theme.palette.mode === 'dark' ? '0 6px 18px rgba(255,255,255,0.06)' : '0 6px 18px rgba(0,0,0,0.06)'),
      // Make hover styling explicit to prevent MUI's default hover color from changing the bg
      '&&:hover': {
        background: theme => (theme.palette.mode === 'dark' ? '#ffffff' : '#ffffff'),
        color: theme => (theme.palette.mode === 'dark' ? '#07070a' : '#07070a'),
        transform: 'scale(1.04)'
      }
    };
  } else {
    // Default non-active buttons: black bg, white text; on hover invert colors and zoom
    style = {
      background: theme => (theme.palette.mode === 'dark' ? '#07070a' : '#ffffff'),
      color: theme => (theme.palette.mode === 'dark' ? '#ffffff' : '#07070a'),
      border: 'none',
      '&:hover': {
        background: theme => (theme.palette.mode === 'dark' ? '#ffffff' : '#07070a'),
        color: theme => (theme.palette.mode === 'dark' ? '#07070a' : '#ffffff'),
        transform: 'scale(1.04)'
      }
    };
    // Secondary or outline variants may want subtle borders — handle outline specifically if requested
    if (variantStyle === 'outline') {
      style.border = theme => (theme.palette.mode === 'dark' ? '1px solid rgba(255,255,255,0.12)' : '1px solid rgba(0,0,0,0.08)');
    }
    if (variantStyle === 'ghost') {
      // ghost behaves like default black bg but we keep a faint border
      style.border = theme => (theme.palette.mode === 'dark' ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(0,0,0,0.06)');
    }
  }

  return (
    <Gradient sx={{ ...style, ...sx }} {...props}>
      {children}
    </Gradient>
  );
}
