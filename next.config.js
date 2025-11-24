/** @type {import('next').NextConfig} */
const securityHeaders = [
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Content-Security-Policy',
    value:
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com; " +
      "style-src 'self' 'unsafe-inline'; " +
      "img-src 'self' data: blob: https:; " +
      "font-src 'self' data: https:; " +
      "connect-src 'self' https:; " +
      "frame-src 'self' https://challenges.cloudflare.com; " +
      "frame-ancestors 'none'; " +
      "base-uri 'self'; " +
      "form-action 'self';",
  },
];

const nextConfig = {
  reactStrictMode: true,
  compress: true,
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
  
  typescript: {
    ignoreBuildErrors: true,
  },

  eslint: {
    ignoreDuringBuilds: true,
  },

  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
  },
};

module.exports = nextConfig;
