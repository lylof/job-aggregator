'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';
import { formatDistanceToNow, isValid } from 'date-fns';
import { fr } from 'date-fns/locale';
import { FaMapMarkerAlt, FaClock, FaBriefcase, FaArrowLeft, FaShareAlt, FaBookmark, FaExternalLinkAlt } from 'react-icons/fa';
import { JobOffer } from '@/services/api';

interface JobDetailProps {
  job: JobOffer;
}

const JobDetail = ({ job }: JobDetailProps) => {
  const [isSaved, setIsSaved] = useState(false);
  
  // Fallbacks pour les champs critiques
  const fallbackJobType = job.job_type || 'à plein temps';
  const fallbackSalary = job.salary || 'À négocier';
  const fallbackDescription = job.description || 'Non renseigné';
  const fallbackSkills = Array.isArray(job.skills) && job.skills.length > 0 ? job.skills : ['Aucune compétence renseignée'];
  let formattedDate = 'Date inconnue';
  const dateStr = job.posted_date;
  if (dateStr) {
    try {
      const dateObj = new Date(dateStr);
      if (!isNaN(dateObj.getTime())) {
        formattedDate = formatDistanceToNow(dateObj, { addSuffix: true, locale: fr });
      }
    } catch {}
  }

  const handleSave = () => {
    setIsSaved(!isSaved);
    // Ici, on pourrait implémenter la logique pour sauvegarder l'offre
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: `${job.title} chez ${job.company}`,
        text: `Découvrez cette offre d'emploi : ${job.title} chez ${job.company}`,
        url: window.location.href,
      });
    } else {
      // Fallback pour les navigateurs qui ne supportent pas l'API Web Share
      navigator.clipboard.writeText(window.location.href);
      alert('Lien copié dans le presse-papier !');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Navigation de retour */}
      <Link href="/" className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-6">
        <FaArrowLeft className="mr-2" />
        Retour aux offres
      </Link>
      
      {/* En-tête de l'offre */}
      <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Logo de l'entreprise */}
          <div className="relative min-w-[80px] w-20 h-20 rounded-md overflow-hidden bg-gray-100 flex-shrink-0">
              <div className="w-full h-full flex items-center justify-center bg-primary-100 text-primary-600 text-2xl font-bold">
                {job.company.charAt(0)}
              </div>
          </div>
          
          {/* Informations principales */}
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-secondary-900 dark:text-white mb-2">
              {job.title}
            </h1>
            <p className="text-lg text-secondary-600 dark:text-secondary-300 mb-4">
              {job.company}
            </p>
            
            {/* Détails de l'offre */}
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-secondary-500 dark:text-secondary-400 mb-4">
              {job.location && (
                <div className="flex items-center">
                  <FaMapMarkerAlt className="mr-2" />
                  <span>{job.location}</span>
                </div>
              )}
                <div className="flex items-center">
                  <FaBriefcase className="mr-2" />
                <span>{fallbackJobType}</span>
                </div>
              <div className="flex items-center">
                <FaClock className="mr-2" />
                <span>{formattedDate}</span>
              </div>
                <div className="text-green-600 dark:text-green-400 font-medium">
                {fallbackSalary}
                </div>
            </div>
            
            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              <a 
                href="#apply" 
                className="btn-primary flex items-center"
              >
                Postuler maintenant
              </a>
              <button 
                className={`p-2 rounded-md ${
                  isSaved 
                    ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300' 
                    : 'bg-secondary-100 text-secondary-600 dark:bg-secondary-700 dark:text-secondary-300'
                }`}
                onClick={handleSave}
                aria-label={isSaved ? 'Retirer des favoris' : 'Ajouter aux favoris'}
              >
                <FaBookmark />
              </button>
              <button 
                className="p-2 rounded-md bg-secondary-100 text-secondary-600 dark:bg-secondary-700 dark:text-secondary-300"
                onClick={handleShare}
                aria-label="Partager"
              >
                <FaShareAlt />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Contenu principal */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Colonne principale - Description */}
        <div className="md:col-span-2">
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6 mb-6">
            <h2 className="text-xl font-semibold text-secondary-900 dark:text-white mb-4">
              Description du poste
            </h2>
            <div className="prose dark:prose-invert max-w-none">
              {/* Affichage sécurisé de la description HTML */}
              <div dangerouslySetInnerHTML={{ __html: fallbackDescription }} />
            </div>
          </div>
          
          {/* Compétences requises */}
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6">
            <h2 className="text-xl font-semibold text-secondary-900 dark:text-white mb-4">
              Compétences requises
            </h2>
            <div className="flex flex-wrap gap-2">
              {Array.isArray(fallbackSkills) && fallbackSkills.length > 0 ? (
                fallbackSkills.map((skill, index) => (
                <span 
                  key={index} 
                  className="tag px-3 py-1.5 text-sm"
                >
                  {skill}
                </span>
                ))
              ) : (
                <span className="text-neutral-400">Aucune compétence renseignée</span>
              )}
            </div>
          </div>
        </div>
        
        {/* Colonne latérale - Informations supplémentaires */}
        <div className="md:col-span-1">
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6 mb-6">
            <h2 className="text-lg font-semibold text-secondary-900 dark:text-white mb-4">
              À propos de {job.company}
            </h2>
            <p className="text-secondary-600 dark:text-secondary-400 mb-4">
              {job.company} est une entreprise spécialisée dans son domaine, offrant des opportunités de carrière stimulantes et un environnement de travail dynamique.
            </p>
            <a 
              href={`https://${job.company.toLowerCase().replace(/\s+/g, '')}.com`} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center text-primary-600 hover:text-primary-700"
            >
              Visiter le site web <FaExternalLinkAlt className="ml-2 text-xs" />
            </a>
          </div>
          
          {/* Formulaire de candidature */}
          <div id="apply" className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6">
            <h2 className="text-lg font-semibold text-secondary-900 dark:text-white mb-4">
              Postuler à cette offre
            </h2>
            <form className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1">
                  Nom complet
                </label>
                <input 
                  type="text" 
                  id="name" 
                  className="input"
                  placeholder="Votre nom complet"
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1">
                  Email
                </label>
                <input 
                  type="email" 
                  id="email" 
                  className="input"
                  placeholder="votre.email@exemple.com"
                />
              </div>
              <div>
                <label htmlFor="cv" className="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1">
                  CV (PDF, DOC, DOCX)
                </label>
                <input 
                  type="file" 
                  id="cv" 
                  className="block w-full text-sm text-secondary-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-600 hover:file:bg-primary-100"
                  accept=".pdf,.doc,.docx"
                />
              </div>
              <div>
                <label htmlFor="message" className="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1">
                  Message (optionnel)
                </label>
                <textarea 
                  id="message" 
                  rows={4} 
                  className="input"
                  placeholder="Présentez-vous brièvement et expliquez pourquoi vous êtes intéressé(e) par ce poste"
                ></textarea>
              </div>
              <button 
                type="submit" 
                className="btn-primary w-full"
              >
                Envoyer ma candidature
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDetail;
