/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/app/**/*.{js,jsx}',
        './src/components/**/*.{js,jsx}',
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                montserrat: ['Montserrat', 'sans-serif'],
                playfair: ['Playfair Display', 'serif'],
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}