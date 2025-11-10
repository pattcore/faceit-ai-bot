/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  compress: true,
  poweredByHeader: false,
  
  // GitHub Pages configuration
  output: 'export',
  basePath: process.env.NODE_ENV === 'production' ? '/faceit-ai-bot' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/faceit-ai-bot/' : '',
  
  // Performance optimizations
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            vendor: {
              chunks: 'all',
              name: 'vendor',
              test: /[\\/]node_modules[\\/]/,
              priority: 20,
            },
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              priority: 10,
            },
          },
        },
      };
    }
    return config;
  },

  // Enable for Replit proxy compatibility
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: process.env.NODE_ENV === 'development' 
              ? 'no-cache, no-store, must-revalidate'
              : 'public, max-age=31536000, immutable'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          }
        ]
      }
    ]
  },

  // Image optimization
  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
  },

  // TypeScript config
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint config  
  eslint: {
    ignoreDuringBuilds: false,
  },
};

module.exports = nextConfig;
