/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    // experimental: {
    //     allowedDevOrigins: [
    //         "localhost:3000",
    //         ".cloudspaces.litng.ai"
    //     ],
    // },
    async rewrites() {
        return [
            {
                source: '/vnc/:path*',
                destination: 'http://127.0.0.1:6080/:path*',
            },
        ];
    },
};

export default nextConfig;
