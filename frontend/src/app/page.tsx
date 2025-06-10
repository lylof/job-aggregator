"use client";
import { useState } from 'react';
import { Suspense } from 'react';
import SearchBar from '@/components/filters/SearchBar';
import FilterPanel from '@/components/filters/FilterPanel';
import JobList from '@/components/jobs/JobList';
import LoadingJobList from '@/components/jobs/LoadingJobList';

export default function HomePage() {
  // État global des filtres (typage explicite)
  const [filters, setFilters] = useState<{
    contractTypes: string[];
    experienceLevels: string[];
    locations: string[];
    skills: string[];
  }>({
    contractTypes: [],
    experienceLevels: [],
    locations: [],
    skills: [],
  });

  // Handler pour appliquer les filtres
  const handleApplyFilters = (newFilters: typeof filters) => {
    setFilters(newFilters);
  };

  // Handler pour reset
  const handleResetFilters = () => {
    setFilters({
      contractTypes: [],
      experienceLevels: [],
      locations: [],
      skills: [],
    });
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary-900 dark:text-white mb-2">
          Offres d&apos;emploi
        </h1>
        <p className="text-secondary-600 dark:text-secondary-400">
          Trouvez les meilleures opportunités professionnelles
        </p>
      </div>
      
      <div className="mb-6">
        <SearchBar />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Job Listings - Main content area */}
        <div className="lg:col-span-3">
          <Suspense fallback={<LoadingJobList />}>
            <JobList filters={filters} />
          </Suspense>
        </div>
        
        {/* Filter Panel - Sidebar */}
        <div className="lg:col-span-1">
          <FilterPanel
            filters={filters}
            onApplyFilters={handleApplyFilters}
            onResetFilters={handleResetFilters}
          />
        </div>
      </div>
    </div>
  );
}
