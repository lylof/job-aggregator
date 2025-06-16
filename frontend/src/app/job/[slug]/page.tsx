import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import JobDetail from '@/components/jobs/JobDetail';
import LoadingJobDetail from '@/components/jobs/LoadingJobDetail';
import { getItemById } from '@/services/api';

// Définition des paramètres de page
type PageProps = {
  params: {
    slug: string;
  };
};

// Récupération des données côté serveur
const getJob = async (slug: string) => {
  try {
    const job = await getItemById(slug);
    return job;
  } catch (e) {
    return null;
  }
};

// Page principale
const JobPage = async ({ params }: PageProps) => {
  const { slug } = params;
  const job = await getJob(slug);

  // Si l'offre n'existe pas, retourner une page 404
  if (!job) {
    notFound();
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <Suspense fallback={<LoadingJobDetail />}>
        <JobDetail job={job} />
      </Suspense>
    </div>
  );
};

export default JobPage;
