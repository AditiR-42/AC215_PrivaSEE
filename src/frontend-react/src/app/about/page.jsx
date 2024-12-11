'use client';

import React from 'react';
import styles from "./styles.module.css";

export default function AboutPage() {
    return (
        <div className={styles.container}>
          <section className={styles.hero}>
              <div className={styles.heroContent}>
                  <h1>About Privasee 🔍</h1>
                  <p>PrivaSEE aims to bridge knowledge gaps around data privacy by reviewing terms and conditions agreements and informing you about the aspects of the privacy you cede by using a certain app or website. PrivaSEE allows you to understand the implications to your data privacy, and compare options in a way that aligns with your personal privacy priorities! </p>
                  <br/>
                  <p>Our app uses data from ToS;DR to provide you with up-to-date privacy grades of any app you upload terms and conditions for. Our app will also give you an app recommendation based on the desired privacy priorities and app qualities you input. </p>
              </div>
          </section>
        </div>
    );
}
