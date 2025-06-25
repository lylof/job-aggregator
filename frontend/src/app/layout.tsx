import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';

export const metadata: Metadata = {
  title: 'Job Aggregator - Trouvez votre emploi idéal',
  description: 'Plateforme d\'agrégation d\'offres d\'emploi enrichies avec des données pertinentes',
};

// Configure Stagewise toolbar
// const stagewiseConfig = {
//   plugins: []
// };

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  // Check if we're in development mode
  // const isDevelopment = process.env.NODE_ENV === 'development';
  
  return (
    <html lang="fr">
      <body className="font-sans">
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-grow">{children}</main>
          <Footer />
        </div>
        
        {/* Render the Stagewise Toolbar in development mode only */}
        {/* {isDevelopment && <StagewiseToolbar config={stagewiseConfig} />} */}
      </body>
    </html>
  );
};

export default RootLayout;
