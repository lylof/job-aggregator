import { Suspense } from 'react';
import { Metadata } from 'next';
import { MapPin, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import JobListContainer from '@/components/jobs/JobListContainer';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getItems } from '@/services/api';

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

// Fonction utilitaire pour calculer le temps écoulé
const getTimeAgo = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'aujourd\'hui';
    if (diffDays === 1) return '1 jour';
    if (diffDays < 7) return `${diffDays} jours`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} semaine${Math.floor(diffDays / 7) > 1 ? 's' : ''}`;
    return `${Math.floor(diffDays / 30)} mois`;
  } catch {
    return 'récemment';
  }
};

// Fonction pour nettoyer la description HTML
const cleanDescription = (htmlString: string): string => {
  if (!htmlString) return '';
  // Supprimer les balises HTML et limiter la longueur
  const textOnly = htmlString.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  return textOnly.length > 120 ? textOnly.substring(0, 120) + '...' : textOnly;
};

// Récupération des jobs en vedette côté serveur - MAINTENANT AVEC L'API RÉELLE
const getFeaturedJobs = async () => {
  try {
    // Appel à l'API réelle pour récupérer les offres d'emploi
    const apiResponse = await getItems(1, 8); // Récupérer 8 offres récentes
    
    // Mapper les données de l'API vers le format attendu par l'interface
    const featured = apiResponse.items.map((item) => ({
      id: item.id,
      title: item.title || 'Poste à pourvoir',
      company: item.company || 'Entreprise',
      location: item.location || 'Togo',
      type: item.contract_type || 'CDI',
      postedDate: getTimeAgo(item.posted_date),
      description: cleanDescription(item.description),
    }));
    
    return featured;
  } catch (error) {
    console.error('Erreur lors de la récupération des jobs en vedette:', error);
    // Fallback en cas d'erreur - quelques offres par défaut
    return [
      { 
        id: 'fallback-1',
        title: 'Chargement des offres...', 
        company: 'Veuillez rafraîchir', 
        location: 'Togo', 
        type: 'CDI',
        postedDate: 'récemment',
        description: 'Connexion à la base de données en cours...'
      }
    ];
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
      
            {/* Barre de recherche centrale en forme de pilule */}
            <div className="max-w-3xl mx-auto">
              <form className="w-full">
                <div className="relative group">
                  {/* Effet de glow subtil */}
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/20 to-primary/10 rounded-full blur opacity-30 group-focus-within:opacity-60 transition-opacity duration-300"></div>
                  
                  {/* Container principal avec forme de pilule */}
                  <div className="relative bg-background/90 backdrop-blur-md border border-border/40 rounded-full shadow-xl group-focus-within:shadow-2xl group-focus-within:border-primary/50 transition-all duration-300">
                    
                    {/* Icône de recherche */}
                    <div className="absolute inset-y-0 left-0 flex items-center pl-6 pointer-events-none">
                      <Search className="w-5 h-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-200" />
      </div>
      
                    {/* Input de recherche */}
                    <Input
                      type="search"
                      placeholder="Rechercher des offres d'emploi au Togo..."
                      className="pl-14 pr-36 h-16 text-lg bg-transparent border-none focus:ring-0 focus:outline-none placeholder:text-muted-foreground/70 rounded-full font-medium"
                      aria-label="Recherche d'emploi"
                    />
                    
                    {/* Bouton de recherche */}
                    <Button
                      type="submit"
                      size="lg"
                      className="absolute right-2 top-2 h-12 px-8 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full shadow-lg hover:shadow-xl transition-all duration-200 font-semibold text-base"
                    >
                      Rechercher
                    </Button>
                  </div>
                </div>
              </form>
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