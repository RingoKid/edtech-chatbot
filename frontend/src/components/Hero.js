import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from './ui/AppButton';
import Box from '@mui/material/Box';
import styles from './Hero.module.css';

function Hero() {
  return (
    <section className={styles.hero}>
      <Box sx={{ display: 'flex', justifyContent: 'center', pt: 10 }}>
          <Card sx={{ width: { xs: '90%', md: '60%' }, backdropFilter: 'none', bgcolor: '#07070a', boxShadow: 'none', borderRadius: 3, border: '1px solid rgba(255,255,255,0.18)' }}>
          <CardContent sx={{ textAlign: 'center', py: 6, bgcolor: 'transparent' }}>
            <div style={{ background: 'transparent' }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={800}>
              Early Childhood Teacher Tool for Structured Composing Lessons
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Where Early Writing and Language Grow Together
            </Typography>
            <Button component={RouterLink} to="/ai-tool" variantStyle="primary" sx={{ mt: 2, px: 4 }}>
              Get Started
            </Button>
            </div>
          </CardContent>
        </Card>
      </Box>
    </section>
  );
}

export default Hero;
