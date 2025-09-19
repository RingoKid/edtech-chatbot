import React from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardMedia from '@mui/material/CardMedia';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '../components/ui/AppButton';
import videoData from '../data/videos';

export default function Videos() {
  const { topic } = useParams();
  const key = topic || 'handwriting';
  const list = videoData[key] || [];

  const titleMap = {
    handwriting: 'Handwriting & Spelling',
    vocab: 'Vocabulary & Syntax',
    'idea-org': 'Idea Organization & Generation'
  };

  return (
    <Box sx={{ py: 6, px: 2 }}>
      <Box sx={{ maxWidth: 1100, mx: 'auto', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={800}>
          {titleMap[key] || 'Videos'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Browse short guided videos designed to support student composition and organization.
        </Typography>
      </Box>

      <Grid container spacing={3} justifyContent="center" sx={{ maxWidth: 1100, mx: 'auto' }}>
        {list.map((item, i) => (
          <Grid key={i} item xs={12} sm={6} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 2, boxShadow: 3 }}>
              <CardActionArea component={RouterLink} to={`/watch/${key}/${i}`} sx={{ flex: 1 }}>
                {item.thumb ? (
                  <CardMedia component="img" height="160" image={item.thumb} alt={item.title || `Video ${i + 1}`} />
                ) : (
                  <Box sx={{ height: 160, bgcolor: 'grey.100' }} />
                )}
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                    {item.title || `Video ${i + 1}`}
                  </Typography>
                  {item.meta && (
                    <Typography variant="body2" color="text.secondary">
                      {item.meta}
                    </Typography>
                  )}
                </CardContent>
              </CardActionArea>
              <Box sx={{ p: 2, pt: 0, display: 'flex', justifyContent: 'flex-end' }}>
                <Button variantStyle="ghost" component={RouterLink} to={`/watch/${key}/${i}`}>
                  Watch
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
