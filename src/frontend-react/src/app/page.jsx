import Hero from '@/components/home/Hero';
// Ensure unused imports are removed or commented out if not needed
// import About from '@/components/home/About';
// import Podcasts from '@/components/home/Podcasts';
// import Newsletters from '@/components/home/Newsletters';
// import WhatIs from '@/components/home/WhatIs';

// Import required CSS for react-pdf
import 'react-pdf/dist/esm/Page/TextLayer.css';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';

export default function Home() {
    return (
        <>
            <Hero />
            {/* <WhatIs></WhatIs>
            <About /> */}
        </>
    );
}