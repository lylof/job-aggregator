'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { MapPin, Clock, Briefcase, Building2, Home, GraduationCap, Award, Wifi } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CategoryBadge } from '@/components/ui/category-badge';
import { cn } from '@/lib/utils';
import { JobOffer } from '@/services/api';

// Interface pour les propriétés de la carte d'offre d'emploi - ENRICHIE
export interface JobCardProps {
  job: JobOffer;
}

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Aujourd\'hui';
      if (diffDays === 1) return 'Hier';
      if (diffDays < 7) return `Il y a ${diffDays} jours`;
      if (diffDays < 30) return `Il y a ${Math.ceil(diffDays / 7)} semaines`;
      return `Il y a ${Math.ceil(diffDays / 30)} mois`;
    } catch {
      return 'Date inconnue';
    }
  };

  const getLocationDisplay = () => {
    // Prioriser la ville détectée, puis la région, puis la localisation de base
    if (job.detected_city) {
      return job.detected_region ? `${job.detected_city}, ${job.detected_region}` : job.detected_city;
    }
    return job.location || 'Togo';
  };

  const getSkillsDisplay = () => {
    if (!job.skills || job.skills.length === 0) return [];
    return job.skills.slice(0, 3); // Limiter à 3 skills pour l'affichage
  };

  const truncateDescription = (text: string, maxLength: number = 150) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + '...';
  };

  return (
    <Card className="h-full flex flex-col hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg text-gray-900 mb-2 line-clamp-2">
              <Link 
                href={`/job/${job.slug || job.id}`}
                className="hover:text-blue-600 transition-colors"
              >
                {job.title}
              </Link>
            </h3>
            
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
              <Building2 className="h-4 w-4 text-gray-400" />
              <span className="font-medium">{job.company}</span>
            </div>
            
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                <span>{getLocationDisplay()}</span>
              </div>
              
              {(job.is_remote || job.remote_work_detected) && (
                <div className="flex items-center gap-1 text-green-600">
                  <Wifi className="h-4 w-4" />
                  <span>Remote</span>
                </div>
              )}
              
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>{formatDate(job.posted_date)}</span>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col gap-2">
            <CategoryBadge category={job.offer_category || 'job'} />
            {job.contract_type && job.contract_type !== 'Non spécifié' && (
              <Badge variant="outline" className="text-xs">
                {job.contract_type}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-3 flex-1">
        <p className="text-sm text-gray-600 mb-3">
          {truncateDescription(job.description)}
        </p>

        {/* Skills */}
        {getSkillsDisplay().length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {getSkillsDisplay().map((skill, index) => (
              <Badge 
                key={index} 
                variant="secondary" 
                className="text-xs bg-blue-50 text-blue-700 hover:bg-blue-100"
              >
                {skill}
              </Badge>
            ))}
            {job.skills && job.skills.length > 3 && (
              <Badge variant="secondary" className="text-xs bg-gray-50 text-gray-600">
                +{job.skills.length - 3} autres
              </Badge>
            )}
          </div>
        )}

        {/* Informations additionnelles */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          {job.salary && job.salary !== 'À négocier' && (
            <span className="font-medium text-green-600">{job.salary}</span>
          )}
          
          {job.experience_level && job.experience_level !== 'Non spécifié' && (
            <div className="flex items-center gap-1">
              <Briefcase className="h-3 w-3" />
              <span>{job.experience_level}</span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="pt-3">
        <Link 
          href={`/job/${job.slug || job.id}`}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors text-center"
        >
          Voir l'offre
        </Link>
      </CardFooter>
    </Card>
  );
};

export default JobCard;
