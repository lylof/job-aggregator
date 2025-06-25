'use client';

import Image from 'next/image';
import Link from 'next/link';
import { MapPin, Clock, Briefcase, Building2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

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
  const fallbackSkills = Array.isArray(skills) && skills.length > 0 ? skills.slice(0, 3) : [];
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
      <Card className={cn(
        "hover:shadow-lg transition-all duration-300 hover:border-primary/20 group-hover:scale-[1.02]",
        "backdrop-blur-sm bg-card/80"
      )}>
        <CardHeader className="pb-3">
          <div className="flex items-start gap-3">
            {/* Logo de l'entreprise - Plus compact */}
            <div className="relative w-10 h-10 rounded-lg overflow-hidden bg-muted flex-shrink-0 ring-1 ring-border">
          {companyLogo ? (
            <Image 
              src={companyLogo} 
              alt={`${company} logo`} 
              fill 
                  sizes="40px" 
              className="object-contain"
            />
          ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5 text-primary font-semibold text-sm">
              {company.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
            {/* Titre et entreprise */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base leading-tight text-foreground group-hover:text-primary transition-colors duration-200 truncate">
            {title}
          </h3>
              <div className="flex items-center gap-1 mt-1">
                <Building2 size={12} className="text-muted-foreground flex-shrink-0" />
                <p className="text-sm text-muted-foreground truncate">{company}</p>
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0 space-y-4">
          {/* Informations compactes */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            {location && (
              <div className="flex items-center gap-1">
                <MapPin size={12} className="flex-shrink-0" />
                <span className="truncate max-w-[120px]">{location}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Briefcase size={12} className="flex-shrink-0" />
              <span>{fallbackJobType}</span>
              </div>
            <div className="flex items-center gap-1">
              <Clock size={12} className="flex-shrink-0" />
              <span>{formattedDate}</span>
            </div>
          </div>

          {/* Compétences - Plus compactes */}
          {fallbackSkills.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {fallbackSkills.map((skill, index) => (
                <Badge key={index} variant="secondary" className="text-xs py-0.5 px-2 font-medium">
                    {skill}
                </Badge>
                ))}
              {Array.isArray(skills) && skills.length > 3 && (
                <Badge variant="outline" className="text-xs py-0.5 px-2">
                    +{skills.length - 3}
                </Badge>
                )}
              </div>
          )}

          {/* Salaire - Plus discret */}
          {fallbackSalary !== 'À négocier' && (
            <div className="flex justify-end">
              <Badge variant="default" className="text-xs font-semibold bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/20 dark:text-green-400">
                {fallbackSalary}
              </Badge>
          </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
};

export default JobCard;
