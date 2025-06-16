'use client';

import Image from 'next/image';
import Link from 'next/link';
import { FaMapMarkerAlt, FaClock, FaBriefcase } from 'react-icons/fa';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

// Interface pour les propriétés de la carte d'offre d'emploi
export interface JobCardProps {
  id: string | number;
  title: string;
  company: string;
  companyLogo?: string;
  location: string;
  jobType: string;
  skills: string[];
  postedDate: string;
  salaryRange?: string;
  slug?: string; // Peut être l'item_id si non fourni
}

const JobCard = ({
  id,
  title,
  company,
  companyLogo,
  location,
  jobType,
  skills,
  postedDate,
  salaryRange,
  slug
}: JobCardProps) => {
  // Fallbacks pour les champs critiques
  const fallbackSlug = slug || String(id);
  const fallbackJobType = jobType || 'à plein temps';
  const fallbackSalary = salaryRange || 'À négocier';
  const fallbackSkills = Array.isArray(skills) && skills.length > 0 ? skills : ['Aucune compétence renseignée'];
  let formattedDate = 'Date inconnue';
  if (postedDate) {
    try {
      const dateObj = new Date(postedDate);
      if (!isNaN(dateObj.getTime())) {
        formattedDate = formatDistanceToNow(dateObj, { addSuffix: true, locale: fr });
      }
    } catch {}
  }

  return (
    <Link href={`/job/${fallbackSlug}`} className="block group">
      <article className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700/80 rounded-xl p-4 sm:p-6 hover:border-neutral-300 dark:hover:border-neutral-600 hover:shadow-card-hover transition-all duration-300 flex flex-col md:flex-row md:items-start gap-3 sm:gap-5">
        {/* Logo de l'entreprise */}
        <div className="relative min-w-[48px] sm:min-w-[56px] w-12 sm:w-14 h-12 sm:h-14 rounded-lg overflow-hidden bg-neutral-100 dark:bg-neutral-700 flex-shrink-0 mt-0.5 sm:mt-1">
          {companyLogo ? (
            <Image 
              src={companyLogo} 
              alt={`${company} logo`} 
              fill 
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw" 
              className="object-contain"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-neutral-100 dark:bg-neutral-700 text-neutral-500 dark:text-neutral-400 text-xl sm:text-2xl font-medium">
              {company.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        {/* Contenu principal */}
        <div className="flex-1">
          <h3 className="text-lg sm:text-xl font-semibold text-neutral-800 dark:text-white mb-1 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors duration-200">
            {title}
          </h3>
          <p className="text-sm sm:text-base text-neutral-600 dark:text-neutral-300 mb-2 sm:mb-3">
            {company}
          </p>
          
          {/* Informations supplémentaires */}
          <div className="flex flex-wrap items-center gap-x-3 sm:gap-x-5 gap-y-2 text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 mb-3 sm:mb-4">
            {location && (
              <div className="flex items-center">
                <FaMapMarkerAlt size={14} className="mr-1 sm:mr-1.5 text-neutral-400 dark:text-neutral-500" />
                <span>{location}</span>
              </div>
            )}
              <div className="flex items-center">
                <FaBriefcase size={14} className="mr-1 sm:mr-1.5 text-neutral-400 dark:text-neutral-500" />
              <span>{fallbackJobType}</span>
              </div>
            <div className="flex items-center">
              <FaClock size={14} className="mr-1 sm:mr-1.5 text-neutral-400 dark:text-neutral-500" />
              <span>{formattedDate}</span>
            </div>
          </div>

          {/* Salaire et Tags des compétences */} 
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
              <div className="text-xs sm:text-sm font-semibold text-green-600 dark:text-green-400">
              {fallbackSalary}
              </div>
              <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-1 sm:mt-0">
              {fallbackSkills.map((skill, index) => (
                  <span 
                    key={index} 
                    className="bg-neutral-100 dark:bg-neutral-700/60 text-neutral-600 dark:text-neutral-300 text-xs font-medium px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full"
                  >
                    {skill}
                  </span>
                ))}
              {Array.isArray(skills) && skills.length > 3 && (
                  <span className="bg-neutral-100 dark:bg-neutral-700/60 text-neutral-500 dark:text-neutral-400 text-xs font-medium px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full">
                    +{skills.length - 3}
                  </span>
                )}
              </div>
          </div>
        </div>
      </article>
    </Link>
  );
};

export default JobCard;
