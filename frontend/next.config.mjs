/** @type {import('next').NextConfig} */
const nextConfig = {
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
