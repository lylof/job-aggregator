import { Suspense } from 'react';
import { Metadata } from 'next';
import { MapPin } from 'lucide-react';
import SearchBar from '@/components/filters/SearchBar';
import JobListContainer from '@/components/jobs/JobListContainer';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Métadonnées optimisées pour le SEO
export const metadata: Metadata = {
  title: 'Job Aggregator - Emplois au Togo | Plateforme d\'emploi togolaise',
  description: 'Découvrez les meilleures offres d\'emploi au Togo. Plateforme moderne d\'agrégation d\'emplois avec filtres avancés et données enrichies pour le marché togolais.',
  keywords: 'emploi togo, job lomé, offres d\'emploi togo, carrière togo, recrutement, tech, développeur, marketing',
  openGraph: {
    title: 'Job Aggregator - Emplois au Togo',
    description: 'Plateforme moderne d\'agrégation d\'offres d\'emploi pour le marché togolais',
    type: 'website',
    locale: 'fr_TG',
  },
  robots: {
    index: true,
    follow: true,
  },
  alternates: {
    canonical: '/',
  },
};

// Récupération des jobs en vedette côté serveur
const getFeaturedJobs = async () => {
  try {
    // Remplacer par un appel API réel plus tard - adaptés au contexte togolais
    const featured = [
      { 
        id: '1',
        title: 'Développeur Full-Stack', 
        company: 'TechStart Lomé', 
        location: 'Lomé, Maritime', 
        type: 'CDI',
        postedDate: '2 jours',
        description: 'Rejoignez notre équipe dynamique pour développer des applications web modernes...'
      },
      { 
        id: '2',
        title: 'Chef de Projet Marketing', 
        company: 'Digital Togo', 
        location: 'Lomé, Maritime', 
        type: 'CDI',
        postedDate: '1 jour',
        description: 'Pilotez nos campagnes marketing digitales et développez notre présence en ligne...'
      },
      { 
        id: '3',
        title: 'Comptable Senior', 
        company: 'Cabinet Expertise', 
        location: 'Kpalimé, Plateaux', 
        type: 'CDI',
        postedDate: '3 jours',
        description: 'Prenez en charge la comptabilité de nos clients et participez aux missions d\'audit...'
      },
      { 
        id: '4',
        title: 'Designer UX/UI', 
        company: 'Creative Studio', 
        location: 'Lomé, Maritime', 
        type: 'CDI',
        postedDate: '1 jour',
        description: 'Créez des expériences utilisateur exceptionnelles pour nos clients...'
      },
      { 
        id: '5',
        title: 'Responsable Commercial', 
        company: 'Business Solutions', 
        location: 'Sokodé, Centrale', 
        type: 'CDI',
        postedDate: '4 jours',
        description: 'Développez notre portefeuille client et atteignez les objectifs de vente...'
      },
    ];
    return featured;
  } catch (error) {
    console.error('Erreur lors de la récupération des jobs en vedette:', error);
    return [];
  }
};

// Page principale - Server Component
export default async function HomePage() {
  // Data fetching côté serveur
  const featuredJobs = await getFeaturedJobs();

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section compact */}
      <section className="relative py-12 bg-gradient-to-br from-background via-muted/10 to-background">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto text-center space-y-6">
            {/* Titre principal */}
            <div className="space-y-3">
              <h1 className="text-4xl md:text-5xl font-bold text-foreground tracking-tight">
                Trouvez votre emploi de
                <span className="text-gradient block mt-1">
                  rêve maintenant
                </span>
        </h1>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Des milliers d'offres d'emploi vous attendent au Togo
        </p>
      </div>
      
            {/* Barre de recherche centrale */}
            <div className="max-w-2xl mx-auto">
              <SearchBar placeholder="Rechercher des offres d'emploi..." />
            </div>
          </div>
        </div>
      </section>

      {/* Section principale avec layout moderne */}
      <section className="py-8">
        <div className="container-custom">
          {/* Titre de section */}
      <div className="mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-1">
              Offres récentes
            </h2>
            <p className="text-sm text-muted-foreground">
              {featuredJobs.length} nouvelles opportunités ajoutées aujourd'hui
            </p>
          </div>

          {/* Layout principal : contenu + filtres */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            {/* Contenu principal - Liste des jobs */}
            <div className="lg:col-span-3 space-y-3">
              {featuredJobs.map((job) => (
                <Card key={job.id} className="group cursor-pointer border border-border/50 hover:border-border/80 hover:shadow-sm transition-all duration-150">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="text-base font-semibold text-foreground group-hover:text-primary/90 transition-colors duration-150 mb-1">
                          {job.title}
                        </h3>
                        <p className="text-sm text-muted-foreground font-medium">
                          {job.company}
                        </p>
                      </div>
                      <Badge variant="secondary" className="shrink-0 text-xs">
                        {job.type}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        <span>{job.location}</span>
                      </div>
                      <span>Publié il y a {job.postedDate}</span>
      </div>
      
                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
              
              {/* Indicateur de chargement pour plus d'offres */}
              <div className="text-center py-6">
                <div className="inline-flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <span>Chargement de plus d'offres...</span>
                </div>
              </div>
        </div>
        
            {/* Panel de filtres à droite */}
        <div className="lg:col-span-1">
              <Suspense fallback={
                <div className="h-80 bg-muted rounded-lg animate-pulse" />
              }>
                <JobListContainer showFiltersOnly={true} />
              </Suspense>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}