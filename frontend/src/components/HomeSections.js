import React from 'react';
import About from './About';
import Empowers from './Empowers';
import styles from './HomeSections.module.css';
import aboutStyles from './About.module.css';
import AppBubble from './ui/AppBubble';
import Typography from '@mui/material/Typography';

function RightTextBlock() {
  return (
    <section className={aboutStyles.about}>
  <AppBubble sx={{ padding: { xs: 4, md: 5 }, borderRadius: 12, minHeight: 220, background: 'transparent', border: '1px solid rgba(255,255,255,0.18)', boxShadow: 'none', backdropFilter: 'none' }}>
      <Typography variant="h5" component="h2" sx={{ fontWeight: 800, mb: 1, color: 'text.primary' }}>
        How Language for Composing
        <br />
        Empowers Teachers
      </Typography>
      <div className={styles.empowersList}>
        <div className={styles.empowersItem}>
          <div className={styles.num}>01</div>
          <p>Build knowledge of the language and writing skills young children need to become confident composers.</p>
        </div>
        <div className={styles.empowersItem}>
          <div className={styles.num}>02</div>
          <p>Integrate language and literacy skills during meaningful, authentic writing tasks.</p>
        </div>
        <div className={styles.empowersItem}>
          <div className={styles.num}>03</div>
          <p>Equip teachers with the tools to seamlessly integrate early writing practices into daily classroom interactions.</p>
        </div>
        <div className={styles.empowersItem}>
          <div className={styles.num}>04</div>
          <p>Equip teachers with the tools to seamlessly integrate early writing practices into daily classroom interactions.</p>
        </div>
      </div>
    </AppBubble>
    </section>
  );
}

export default function HomeSections() {
  return (
    <div className={styles.container}>
      <div className={styles.columns}>
        <div className={styles.column}>
          <AppBubble sx={{ padding: { xs: 4, md: 5 }, borderRadius: 12, minHeight: 220, background: 'transparent', border: '1px solid rgba(255,255,255,0.18)', boxShadow: 'none', backdropFilter: 'none' }}>
            <Typography component="div" sx={{ color: 'text.primary' }}>
              <About />
            </Typography>
          </AppBubble>
        </div>
        <div className={styles.column}>
          <RightTextBlock />
        </div>
      </div>

      <div className={styles.empowersWrap}>
        <Empowers />
      </div>
    </div>
  );
}
