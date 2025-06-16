"use client";
import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import useSWR from 'swr';
import { searchJobs, searchItems, mapItemToJobOffer } from '@/services/api';
import JobCard from '@/components/jobs/JobCard';
import LoadingJobList from '@/components/jobs/LoadingJobList';
import { FaSadTear } from 'react-icons/fa';

const fetcher = async (q: string, page: number) => {
  if (!q) return { items: [], total_pages: 1 };
  // Essayer d'abord le nouveau système (items)
  const itemsRes = await searchItems({ type: 'job', q }, page, 10);
  if (itemsRes.items && itemsRes.items.length > 0) {
    // Mapper les items au format JobOffer
    return {
      ...itemsRes,
      items: itemsRes.items.map(mapItemToJobOffer),
    };
  }
  // Fallback sur l'ancien système si aucun résultat
  return await searchJobs(q, page, 10);
};

export default function SearchPage() {
  const searchParams = useSearchParams();
  const q = searchParams.get('q') || '';
  const [currentPage, setCurrentPage] = useState(1);

  const { data, error, isLoading } = useSWR([q, currentPage], ([q, page]) => fetcher(q, page));

  if (isLoading) return <LoadingJobList />;
  if (error) return <div className="text-red-500">Erreur lors du chargement des résultats.</div>;
  if (!data || data.items.length === 0) return (
    <div className="flex flex-col items-center justify-center h-64">
      <FaSadTear className="text-4xl text-gray-400 mb-2" />
      <span>Aucun résultat trouvé pour "{q}"</span>
    </div>
  );

  return (
    <div className="space-y-4">
      {data.items.map((job: any) => (
        <JobCard key={job.id} {...job} />
      ))}
      {/* Pagination simple */}
      <div className="flex justify-center gap-2 mt-4">
        <button
          className="btn btn-sm"
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          Précédent
        </button>
        <span>Page {currentPage} / {data.total_pages || 1}</span>
        <button
          className="btn btn-sm"
          onClick={() => setCurrentPage((p) => p + 1)}
          disabled={currentPage === (data.total_pages || 1)}
        >
          Suivant
        </button>
      </div>
    </div>
  );
} 