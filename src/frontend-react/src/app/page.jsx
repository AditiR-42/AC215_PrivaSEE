import Hero from '@/components/home/Hero';

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