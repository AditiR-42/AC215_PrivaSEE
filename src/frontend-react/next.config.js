/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    webpack: (config) => {
        // Add rule for handling SVGs
        config.module.rules.push({
            test: /\.svg$/,
            use: ["@svgr/webpack"]
        });

        // Add rule for handling only CSS from react-pdf
        config.module.rules.push({
            test: /\.css$/,
            include: /node_modules\/react-pdf/,
            use: [
                {
                    loader: 'style-loader',
                },
                {
                    loader: 'css-loader',
                },
            ],
        });

        return config;
    },
    rewrites: async () => {
        return [
            {
                source: "/api/:path*",
                destination:
                    process.env.NODE_ENV === "development"
                        ? "http://rag-system-api-service:9000/:path*"
                        : "/api/",
            },
            {
                source: "/docs",
                destination:
                    process.env.NODE_ENV === "development"
                        ? "http://rag-system-api-service:9000/docs"
                        : "/api/docs",
            },
            {
                source: "/openapi.json",
                destination:
                    process.env.NODE_ENV === "development"
                        ? "http://rag-system-api-service:9000/openapi.json"
                        : "/api/openapi.json",
            },
        ];
    },
    reactStrictMode: false,
};

module.exports = nextConfig;
