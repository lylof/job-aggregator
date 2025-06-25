'use client';

import { useState, Suspense } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import FilterPanelSimple from '@/components/filters/FilterPanelSimple';
import JobList from '@/components/jobs/JobList';
import LoadingJobList from '@/components/jobs/LoadingJobList';

interface FilterState {
  contractTypes: string[];
  experienceLevels: string[];
  locations: string[];
}

interface JobListContainerProps {
  showFiltersOnly?: boolean;
}

const JobListContainer = ({ showFiltersOnly = false }: JobListContainerProps) => {
  const [filters, setFilters] = useState<FilterState>({
    contractTypes: [],
    experienceLevels: [],
    locations: [],
  });

  const handleApplyFilters = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({
      contractTypes: [],
      experienceLevels: [],
      locations: [],
    });
  };

  // Si on veut seulement afficher les filtres
  if (showFiltersOnly) {
    return (
      <FilterPanelSimple
        filters={filters}
        onApplyFilters={handleApplyFilters}
        onResetFilters={handleResetFilters}
      />
    );
  }

  // Layout complet avec filtres + liste
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
      {/* Panel de filtres - Sidebar */}
      <div className="lg:col-span-1">
        <FilterPanelSimple
          filters={filters}
          onApplyFilters={handleApplyFilters}
          onResetFilters={handleResetFilters}
        />
      </div>
      
      {/* Liste des offres - Contenu principal */}
      <div className="lg:col-span-3">
        <Suspense fallback={<LoadingJobList />}>
          <JobList filters={filters} />
        </Suspense>
        
        {/* Message temporaire */}
        <Card className="mt-6 glass-effect border-amber-200 dark:border-amber-800">
          <CardContent className="p-6 text-center">
            <div className="flex items-center justify-center gap-2 mb-3">
              <Badge variant="secondary" className="bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400">
                🔧 Mode développement
              </Badge>
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Intégration API en cours
            </h3>
            <p className="text-muted-foreground text-sm">
              L'API backend est opérationnelle avec <strong>448 offres d'emploi</strong> stockées. 
              L'intégration complète avec le frontend sera finalisée prochainement.
            </p>
            
            <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded-lg">
              <p className="text-primary text-xs font-medium">
                💡 <strong>Statut :</strong> API ✅ | Base de données ✅ | Frontend 🔄
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default JobListContainer; 