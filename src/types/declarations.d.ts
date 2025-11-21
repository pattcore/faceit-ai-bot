declare module '*.json' {
  const value: Record<string, any>;
  export default value;
}

declare module 'next/navigation';
declare module 'next/link';
