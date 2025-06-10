import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';

// Import StagewiseToolbar for development mode only
import { StagewiseToolbar } from '@stagewise/toolbar-next';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Job Aggregator - Trouvez votre emploi idéal',
  description: 'Plateforme d\'agrégation d\'offres d\'emploi enrichies avec des données pertinentes',
};

// Configure Stagewise toolbar
const stagewiseConfig = {
  plugins: []
};

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  // Check if we're in development mode
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  return (
    <html lang="fr">
      <body className={inter.className}>
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-grow">{children}</main>
          <Footer />
        </div>
        
        {/* Render the Stagewise Toolbar in development mode only */}
        {isDevelopment && <StagewiseToolbar config={stagewiseConfig} />}
      </body>
    </html>
  );
};

export default RootLayout;
