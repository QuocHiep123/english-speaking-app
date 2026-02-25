/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@vietspeak/shared-types"],
  
  // API proxy configuration for development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.BACKEND_URL || 'http://localhost:8000/api/:path*',
      },
    ];
  },

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_APP_NAME: 'VietSpeak AI',
    NEXT_PUBLIC_APP_VERSION: '0.1.0',
  },

  // Webpack configuration for audio processing
  webpack: (config) => {
    config.module.rules.push({
      test: /\.worklet\.js$/,
      use: { loader: 'worklet-loader' },
    });
    return config;
  },
};

module.exports = nextConfig;
