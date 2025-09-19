import React from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '../components/ui/AppButton';
import videoData from '../data/videos';

export default function VideoDetail() {
  const { topic, index } = useParams();
  const idx = parseInt(index || '0', 10);
  const list = videoData[topic] || [];
  const item = list[idx] || {};
  const title = item.title || `Video ${idx + 1}`;
  const primaryFile = item.file || `/media/${topic}/video-${idx + 1}.mp4`;
  const secondaryFile = item.fileB || `/media/${topic}/video-${idx + 1}-b.mp4`;

  const isTwoUp = !!item.fileB; // if fileB exists, show two-up

  // support both structured headings or single-string placeholders
  const rawTop = item.topText || '';
  const rawBottom = item.bottomText || '';

  const topHeading = item.topHeading || (rawTop.includes('\n') ? rawTop.split('\n')[0].trim() : '');
  const topBody = item.topTextBody || (rawTop.includes('\n') ? rawTop.split('\n').slice(1).join('\n').trim() : (rawTop || '[Top placeholder text — edit me]'));

  const bottomHeading = item.bottomHeading || (rawBottom.includes('\n') ? rawBottom.split('\n')[0].trim() : '');
  const bottomBody = item.bottomTextBody || (rawBottom.includes('\n') ? rawBottom.split('\n').slice(1).join('\n').trim() : (rawBottom || '[Bottom placeholder text — edit me]'));

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {topHeading && <Typography variant="h6" gutterBottom sx={{ color: 'text.primary' }}>{topHeading}</Typography>}
      <Typography variant="body1" paragraph sx={{ color: 'text.secondary' }}>{topBody}</Typography>

      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          <Card sx={{ boxShadow: 3 }}>
            <CardContent sx={{ p: 2 }}>
              {isTwoUp ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Box component="video" src={primaryFile} controls poster={item.poster || ''} sx={{ width: '100%', borderRadius: 1 }}>
                      Your browser does not support the video tag. <a href={primaryFile}>Download</a>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Box component="video" src={secondaryFile} controls poster={item.posterB || ''} sx={{ width: '100%', borderRadius: 1 }}>
                      Your browser does not support the video tag. <a href={secondaryFile}>Download</a>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Box component="video" src={primaryFile} controls poster={item.poster || ''} sx={{ width: '100%', borderRadius: 1 }}>
                  Your browser does not support the video tag. <a href={primaryFile}>Download</a>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Box sx={{ position: 'sticky', top: 24 }}>
            <Typography variant="h5" component="h2" gutterBottom fontWeight={700}>{title}</Typography>
            <Button component={RouterLink} to={`/videos/${topic}`} variantStyle="ghost" sx={{ mb: 2 }}>&larr; Back to list</Button>
            {bottomHeading && <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>{bottomHeading}</Typography>}
            <Typography variant="body2" color="text.secondary">{bottomBody}</Typography>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
}
