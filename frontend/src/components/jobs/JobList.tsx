'use client';

import { useState, useEffect } from 'react';
import JobCard, { JobCardProps } from './JobCard';
import { FaSadTear } from 'react-icons/fa';
import { getJobs } from '@/services/api';

// Composant de pagination avec style "linear app design"
const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange 
}: { 
  currentPage: number; 
  totalPages: number; 
  onPageChange: (page: number) => void;
}) => {
  // Créer un tableau de pages à afficher
  const getPageNumbers = () => {
    const pages = [];
    
    // Toujours afficher la première page
    pages.push(1);
    
    // Ajouter des points de suspension si nécessaire
    if (currentPage > 3) {
      pages.push('...');
    }
    
    // Ajouter les pages autour de la page actuelle
    for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
      pages.push(i);
    }
    
    // Ajouter des points de suspension si nécessaire
    if (currentPage < totalPages - 2) {
      pages.push('...');
    }
    
    // Toujours afficher la dernière page si elle existe
    if (totalPages > 1) {
      pages.push(totalPages);
    }
    
    return pages;
  };

  return (
    <div className="flex justify-center mt-10">
      <nav className="flex items-center justify-center space-x-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium ${
            currentPage === 1 
              ? 'text-neutral-400 dark:text-neutral-600 cursor-not-allowed' 
              : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700'
          }`}
          aria-label="Page précédente"
        >
          &lsaquo;
        </button>
        
        {getPageNumbers().map((page, index) => (
          page === '...' ? (
            <span 
              key={`ellipsis-${index}`} 
              className="h-8 w-8 flex items-center justify-center text-neutral-500 dark:text-neutral-400"
            >
              ...
            </span>
          ) : (
            <button
              key={`page-${page}`}
              onClick={() => onPageChange(Number(page))}
              className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium transition-colors ${
                currentPage === page
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 font-semibold'
                  : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700'
              }`}
              aria-label={`Page ${page}`}
              aria-current={currentPage === page ? 'page' : undefined}
            >
              {page}
            </button>
          )
        ))}
        
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium ${
            currentPage === totalPages 
              ? 'text-neutral-400 dark:text-neutral-600 cursor-not-allowed' 
              : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700'
          }`}
          aria-label="Page suivante"
        >
          &rsaquo;
        </button>
      </nav>
    </div>
  );
};

// Données de test pour le développement
const MOCK_JOBS: JobCardProps[] = [
  {
    id: '1',
    title: 'Développeur Frontend React',
    company: 'TechSolutions',
    companyLogo: 'https://via.placeholder.com/150',
    location: 'Paris, France',
    jobType: 'CDI',
    skills: ['React', 'TypeScript', 'Tailwind CSS'],
    postedDate: '2025-05-20',
    salaryRange: '45k€ - 60k€',
    slug: 'developpeur-frontend-react'
  },
  {
    id: '2',
    title: 'Ingénieur Backend Node.js',
    company: 'DataInnovate',
    companyLogo: 'https://via.placeholder.com/150',
    location: 'Lyon, France',
    jobType: 'CDI',
    skills: ['Node.js', 'MongoDB', 'Express', 'AWS'],
    postedDate: '2025-05-22',
    salaryRange: '50k€ - 65k€',
    slug: 'ingenieur-backend-nodejs'
  },
  {
    id: '3',
    title: 'UX/UI Designer',
    company: 'DesignMasters',
    companyLogo: 'https://via.placeholder.com/150',
    location: 'Bordeaux, France',
    jobType: 'Freelance',
    skills: ['Figma', 'Adobe XD', 'Sketch'],
    postedDate: '2025-05-25',
    salaryRange: '400€ - 500€ / jour',
    slug: 'ux-ui-designer'
  },
  {
    id: '4',
    title: 'Data Scientist',
    company: 'AIForAll',
    companyLogo: 'https://via.placeholder.com/150',
    location: 'Remote',
    jobType: 'CDD',
    skills: ['Python', 'TensorFlow', 'PyTorch', 'SQL'],
    postedDate: '2025-05-18',
    salaryRange: '55k€ - 70k€',
    slug: 'data-scientist'
  },
  {
    id: '5',
    title: 'DevOps Engineer',
    company: 'CloudMasters',
    companyLogo: 'https://via.placeholder.com/150',
    location: 'Lille, France',
    jobType: 'CDI',
    skills: ['Docker', 'Kubernetes', 'CI/CD', 'Terraform'],
    postedDate: '2025-05-15',
    salaryRange: '60k€ - 75k€',
    slug: 'devops-engineer'
  },
];

type JobListProps = {
  filters: {
    contractTypes: string[];
    experienceLevels: string[];
    locations: string[];
    skills: string[];
  };
};

// Composant principal de liste des offres d'emploi
const JobList = ({ filters }: JobListProps) => {
  const [jobs, setJobs] = useState<JobCardProps[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [useMockData, setUseMockData] = useState(false);

  // Charger des données de test
  const loadMockData = () => {
    console.log("Chargement des données de test...");
    setLoading(true);
    
    // Simuler un délai de chargement
    setTimeout(() => {
      const itemsPerPage = 3;
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const paginatedJobs = MOCK_JOBS.slice(startIndex, endIndex);
      
      setJobs(paginatedJobs);
      setTotalPages(Math.ceil(MOCK_JOBS.length / itemsPerPage));
      setError(null);
      setLoading(false);
    }, 500);
  };

  // Activer les données de test
  const enableMockData = () => {
    setUseMockData(true);
    setCurrentPage(1);
  };

  // Récupérer les données de l'API
  const fetchApiData = async () => {
    try {
      // Construction des filtres pour l'API
      const apiFilters: Record<string, any> = {};
      if (filters.contractTypes.length > 0) apiFilters.contract_type = filters.contractTypes.join(',');
      if (filters.experienceLevels.length > 0) apiFilters.experience = filters.experienceLevels.join(',');
      if (filters.locations.length > 0) apiFilters.location = filters.locations.join(',');
      if (filters.skills.length > 0) apiFilters.skill = filters.skills;

      const data = await getJobs(currentPage, 10, apiFilters);
      const transformedJobs = data.items.map((job: any) => ({
        id: job.id,
        title: job.title,
        company: job.company,
        companyLogo: job.company_logo,
        location: job.location,
        jobType: job.job_type,
        skills: job.skills || [],
        postedDate: job.posted_date,
        salaryRange: job.salary_range,
        slug: job.slug
      }));
      setJobs(transformedJobs);
      setTotalPages(data.total_pages);
      setError(null);
    } catch (err) {
      console.error('Erreur:', err);
      setError("Impossible de charger les offres d'emploi. Cliquez sur 'Utiliser des données de test' pour voir un exemple.");
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  // Gestionnaire de changement de page
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Effet pour charger les données
  useEffect(() => {
    setLoading(true);
    if (useMockData) {
      loadMockData();
    } else {
      fetchApiData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, useMockData, filters]);

  // Affichage en cas de chargement
  if (loading && jobs.length === 0) {
    return (
      <div className="py-20 text-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-12 w-12 bg-neutral-200 dark:bg-neutral-700 rounded-full mb-4"></div>
          <div className="h-4 w-48 bg-neutral-200 dark:bg-neutral-700 rounded mb-3"></div>
          <div className="h-3 w-36 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
      </div>
    );
  }

  // Affichage en cas d'erreur
  if (error) {
    return (
      <div className="p-8 rounded-xl bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 text-center">
        <FaSadTear className="mx-auto text-red-400 dark:text-red-300 text-5xl mb-4" />
        <h3 className="text-xl font-semibold text-red-700 dark:text-red-300 mb-2">Une erreur est survenue</h3>
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button 
            onClick={() => fetchApiData()}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg shadow-sm hover:shadow-md transition-all"
          >
            Réessayer
          </button>
          <button 
            onClick={() => enableMockData()}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg shadow-sm hover:shadow-md transition-all"
          >
            Utiliser des données de test
          </button>
        </div>
      </div>
    );
  }

  // Affichage en cas d'absence d'offres
  if (jobs.length === 0) {
    return (
      <div className="text-center py-20 px-6 mx-auto max-w-xl">
        <FaSadTear className="mx-auto text-5xl text-neutral-400 dark:text-neutral-500 mb-6" />
        <h3 className="text-2xl font-semibold text-neutral-700 dark:text-neutral-200 mb-3">Aucune offre trouvée</h3>
        <p className="text-neutral-500 dark:text-neutral-400 max-w-md mx-auto mb-8">
          Nous n'avons pas trouvé d'offres correspondant à vos critères actuels. Essayez d'élargir votre recherche ou de modifier vos filtres.
        </p>
        <button 
          className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg text-sm transition-colors shadow-sm hover:shadow-md focus:ring-4 focus:ring-primary-300 dark:focus:ring-primary-800 focus:outline-none"
          onClick={() => fetchApiData()}
        >
          Voir toutes les offres
        </button>
      </div>
    );
  }

  // Affichage normal
  return (
    <div>
      {/* En-tête avec le nombre d'offres et tri */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div className="bg-neutral-100 dark:bg-neutral-800/60 px-4 py-2 rounded-lg">
          <p className="text-neutral-600 dark:text-neutral-300">
            <span className="font-semibold text-neutral-900 dark:text-white">{jobs.length}</span> offres d'emploi trouvées
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-neutral-600 dark:text-neutral-400">Trier par:</span>
          <select className="bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 text-neutral-700 dark:text-neutral-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 block py-2 px-3 text-sm">
            <option value="recent">Plus récent</option>
            <option value="relevant">Pertinence</option>
            <option value="salary">Salaire</option>
          </select>
        </div>
      </div>

      {/* Liste des offres */}
      <div className="space-y-6">
        {jobs.map((job) => (
          <JobCard key={job.id} {...job} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination 
          currentPage={currentPage} 
          totalPages={totalPages} 
          onPageChange={handlePageChange} 
        />
      )}
    </div>
  );
};

export default JobList;
