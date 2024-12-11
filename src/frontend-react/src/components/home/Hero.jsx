import React from 'react';
import Link from 'next/link'; // Import Link for navigation
import styles from "./Hero.module.css";

const Hero = () => {
  return (
    <div className={styles.layoutWrapper}>
      {/* Hero Section */}
      <div className={styles.container}>
        <h1 className={styles.title}>Empowering Choices,<br />SIMPLIFYING PRIVACY</h1>
        
        {/* Get a Summary Section */}
        <Link href="/summarize">
          <div className={styles.featureRow} role="button" tabIndex="0">
            <div className={styles.featureImage}>
              <img 
                src="/assets/getasummary.png" 
                alt="Summary Illustration" 
                className={styles.image}
              />
            </div>
            <div className={styles.featureText}>
              <h2 className={styles.featureTitle}>Get a Summary ✅</h2>
              <p className={styles.featureDescription}>
                Upload a pdf of an app's terms and conditions. Receive a privacy grade on a scale of A-F, as well as a summary of key legal issues.
              </p>
            </div>
          </div>
        </Link>

        {/* Get a Recommendation Section */}
        <Link href="/recommend">
          <div className={`${styles.featureRow} ${styles.mt8}`} role="button" tabIndex="0">
            <div className={styles.featureImage}>
              <img 
                src="/assets/getarecommendation.png" 
                alt="Recommendation Illustration" 
                className={styles.image}
              />
            </div>
            <div className={styles.featureText}>
              <h2 className={styles.featureTitle}>Get a Recommendation 🌟</h2>
              <p className={styles.featureDescription}>
                Input the type of app you're looking for. Receive an app recommendation based on your top privacy priorities and concerns.
              </p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
};

export default Hero;
