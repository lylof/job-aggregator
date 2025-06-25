'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { getItems } from '@/services/api';
import JobCard from '@/components/jobs/JobCard';
import LoadingJobList from '@/components/jobs/LoadingJobList';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface FilterState {
    contractTypes: string[];
    experienceLevels: string[];
    locations: string[];
}

interface JobListProps {
  filters?: FilterState;
}

const fetcher = async (page: number, limit: number) => {
  try {
    const itemsRes = await getItems();
    return {
      ...itemsRes,
      items: itemsRes.items,
    };
  } catch (error) {
    console.error('Erreur lors de la récupération des offres:', error);
    throw error;
  }
};

const JobList = ({ filters }: JobListProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  const { data, error, isLoading, mutate } = useSWR(
    [`jobs-${currentPage}`, currentPage, itemsPerPage],
    ([, page, limit]) => fetcher(page, limit),
    {
      revalidateOnFocus: false,
      dedupingInterval: 30000, // 30 secondes
    }
  );

  // Fonction pour rafraîchir les données
  const handleRefresh = () => {
    mutate();
  };

  // Affichage du chargement
  if (isLoading) {
    return <LoadingJobList />;
  }

  // Affichage d'erreur avec possibilité de retry
  if (error) {
    return (
      <Card className="glass-effect border-destructive/20">
        <CardContent className="p-8 text-center">
          <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Erreur de chargement
          </h3>
          <p className="text-muted-foreground mb-4">
            Impossible de charger les offres d'emploi. L'API est peut-être temporairement indisponible.
          </p>
          <Button onClick={handleRefresh} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Réessayer
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Aucune donnée disponible
  if (!data || !data.items || data.items.length === 0) {
    return (
      <Card className="glass-effect">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Aucune offre d'emploi trouvée
          </h3>
          <p className="text-muted-foreground">
            Aucune offre ne correspond à vos critères actuels.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête avec stats */}
      <div className="flex items-center justify-between">
    <div>
          <h3 className="text-lg font-semibold text-foreground">
            {data.total || data.items.length} offres trouvées
          </h3>
          {filters && Object.values(filters).some(arr => arr.length > 0) && (
            <p className="text-sm text-muted-foreground">
              Filtres appliqués actifs
            </p>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={handleRefresh} className="gap-2">
          <RefreshCw className="w-4 h-4" />
          Actualiser
        </Button>
      </div>

      {/* Grille des offres d'emploi */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.items.map((job: any) => (
          <div key={job.id} className="animate-fade-in">
            <JobCard {...job} />
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data.total_pages && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-4 pt-6">
          <Button
            variant="outline"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Précédent
          </Button>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Page {currentPage} sur {data.total_pages}
            </span>
          </div>
          
          <Button
            variant="outline"
            onClick={() => setCurrentPage(p => p + 1)}
            disabled={currentPage === data.total_pages}
          >
            Suivant
          </Button>
        </div>
      )}
    </div>
  );
};

export default JobList;