import React from 'react';

const Hero = () => {
  return (
    <div className="layout-wrapper">
      {/* Hero Section */}
      <div className="container">
        <h1 className="title">Empowering Choices,<br />SIMPLIFYING PRIVACY</h1>
        <div className="features">
          <div className="feature">
            <h2>Get a Summary</h2>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          </div>
          <div className="feature">
            <h2>Get a Grade</h2>
            <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          </div>
          <div className="feature">
            <h2>Get Recommended</h2>
            <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;