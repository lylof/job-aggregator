import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PUSH - Emplois au Togo',
  description: 'Plateforme moderne d\'agrégation d\'offres d\'emploi au Togo avec données enrichies et filtres intelligents',
  keywords: 'emploi, job, travail, Togo, Lomé, carrière, recrutement',
  authors: [{ name: 'PUSH Team' }],
  creator: 'PUSH',
  publisher: 'PUSH',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  icons: {
    icon: [
      {
        url: '/favicon.svg',
        type: 'image/svg+xml',
      },
      {
        url: '/favicon-32x32.png',
        sizes: '32x32',
        type: 'image/png',
      },
      {
        url: '/favicon-16x16.png',
        sizes: '16x16', 
        type: 'image/png',
      }
    ],
    apple: {
      url: '/apple-touch-icon.png',
      sizes: '180x180',
      type: 'image/png',
    },
  },
  manifest: '/site.webmanifest',
  openGraph: {
    title: 'PUSH - Emplois au Togo',
    description: 'Trouvez votre emploi idéal au Togo avec notre plateforme moderne',
    url: 'https://push.tg',
    siteName: 'PUSH',
    locale: 'fr_FR',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'PUSH - Emplois au Togo',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PUSH - Emplois au Togo',
    description: 'Trouvez votre emploi idéal au Togo',
    images: ['/twitter-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

// Configure Stagewise toolbar
// const stagewiseConfig = {
//   plugins: []
// };

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Check if we're in development mode
  // const isDevelopment = process.env.NODE_ENV === 'development';
  
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <meta name="theme-color" content="#265DF5" />
      </head>
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
        
        {/* Render the Stagewise Toolbar in development mode only */}
        {/* {isDevelopment && <StagewiseToolbar config={stagewiseConfig} />} */}
      </body>
    </html>
  );
}
