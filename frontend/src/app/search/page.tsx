"use client";
import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import useSWR from 'swr';
import { searchItems, mapItemToJobOffer } from '@/services/api';
import JobCard from '@/components/jobs/JobCard';
import LoadingJobList from '@/components/jobs/LoadingJobList';
import { Frown } from 'lucide-react';
import { Button } from '@/components/ui/button';

const fetcher = async (q: string, page: number) => {
  if (!q) return { items: [], total_pages: 1 };
  // Rechercher avec le système items
  const itemsRes = await searchItems(q, page, 10);
    // Mapper les items au format JobOffer
    return {
      ...itemsRes,
      items: itemsRes.items.map(mapItemToJobOffer),
    };
};

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get('q') || '';
  const [currentPage, setCurrentPage] = useState(1);

  const { data, error, isLoading } = useSWR([q, currentPage], ([q, page]) => fetcher(q, page));

  if (isLoading) return <LoadingJobList />;
  if (error) return <div className="text-red-500">Erreur lors du chargement des résultats.</div>;
  if (!data || data.items.length === 0) return (
    <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
      <Frown className="w-12 h-12 mb-4" />
      <span className="text-lg">Aucun résultat trouvé pour "{q}"</span>
    </div>
  );

  return (
    <div className="space-y-4">
      {data.items.map((job: any) => (
        <JobCard key={job.id} {...job} />
      ))}
      {/* Pagination moderne */}
      <div className="flex items-center justify-center gap-4 mt-8">
        <Button
          variant="outline"
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          Précédent
        </Button>
        <span className="text-sm text-muted-foreground">
          Page {currentPage} sur {data.total_pages || 1}
        </span>
        <Button
          variant="outline"
          onClick={() => setCurrentPage((p) => p + 1)}
          disabled={currentPage === (data.total_pages || 1)}
        >
          Suivant
        </Button>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<LoadingJobList />}>
      <SearchContent />
    </Suspense>
  );
} 