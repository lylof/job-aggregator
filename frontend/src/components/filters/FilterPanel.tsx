'use client';

import { useState, useEffect } from 'react';
import { FaChevronDown, FaChevronUp } from 'react-icons/fa';

// Types pour les options de filtre
type FilterOption = {
  id: string;
  label: string;
  count?: number;
};

// Données des filtres
const contractTypes: FilterOption[] = [
  { id: 'full-time', label: 'CDI', count: 120 },
  { id: 'part-time', label: 'Temps partiel', count: 45 },
  { id: 'internship', label: 'Stage', count: 38 },
  { id: 'freelance', label: 'Freelance', count: 67 },
  { id: 'temporary', label: 'CDD', count: 53 },
];

const experienceLevels: FilterOption[] = [
  { id: 'entry', label: 'Débutant', count: 98 },
  { id: 'mid', label: 'Confirmé', count: 145 },
  { id: 'senior', label: 'Sénior', count: 82 },
  { id: 'expert', label: 'Expert', count: 41 },
];

const locations: FilterOption[] = [
  { id: 'paris', label: 'Paris', count: 87 },
  { id: 'lyon', label: 'Lyon', count: 45 },
  { id: 'marseille', label: 'Marseille', count: 33 },
  { id: 'bordeaux', label: 'Bordeaux', count: 28 },
  { id: 'remote', label: 'Télétravail', count: 113 },
];

const skills: FilterOption[] = [
  { id: 'javascript', label: 'JavaScript', count: 98 },
  { id: 'python', label: 'Python', count: 76 },
  { id: 'react', label: 'React', count: 64 },
  { id: 'java', label: 'Java', count: 59 },
  { id: 'nodejs', label: 'Node.js', count: 53 },
  { id: 'typescript', label: 'TypeScript', count: 48 },
  { id: 'aws', label: 'AWS', count: 42 },
  { id: 'docker', label: 'Docker', count: 39 },
];

// Composant de section de filtre
const FilterSection = ({ 
  title, 
  options, 
  selectedOptions, 
  onChange 
}: { 
  title: string; 
  options: FilterOption[]; 
  selectedOptions: string[]; 
  onChange: (id: string, checked: boolean) => void;
}) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="border-b border-neutral-200 dark:border-neutral-700 last:border-b-0">
      <button 
        className="flex items-center justify-between w-full py-3 sm:py-4 text-left font-medium text-neutral-700 dark:text-neutral-200 hover:text-neutral-900 dark:hover:text-white transition-colors"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls={`filter-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <span className="text-sm sm:text-base tracking-tight">{title}</span>
        <span className="transform transition-transform duration-300 ease-bounce-subtle">
          {isOpen ? 
            <FaChevronUp size={14} className="text-neutral-500 dark:text-neutral-400" /> : 
            <FaChevronDown size={14} className="text-neutral-500 dark:text-neutral-400" />}
        </span>
      </button>

      <div 
        id={`filter-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
        className={`overflow-hidden transition-all duration-300 ease-bounce-subtle ${isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className={`pt-2 pb-4 space-y-2.5 sm:space-y-3 ${isOpen ? 'block' : 'hidden'}`}>
          {options.map((option) => (
            <div key={option.id} className="flex items-center">
              <input
                type="checkbox"
                id={option.id}
                checked={selectedOptions.includes(option.id)}
                onChange={(e) => onChange(option.id, e.target.checked)}
                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary-600 bg-neutral-100 dark:bg-neutral-700 border-neutral-300 dark:border-neutral-600 rounded focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 dark:focus:ring-offset-neutral-800 transition-colors"
              />
              <label 
                htmlFor={option.id} 
                className="ml-2.5 sm:ml-3 text-xs sm:text-sm text-neutral-600 dark:text-neutral-300 hover:text-neutral-800 dark:hover:text-neutral-100 cursor-pointer"
              >
                {option.label}
                {option.count !== undefined && (
                  <span className="text-xs text-neutral-400 dark:text-neutral-500 ml-1.5">
                    ({option.count})
                  </span>
                )}
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

type FilterPanelProps = {
  filters: {
    contractTypes: string[];
    experienceLevels: string[];
    locations: string[];
    skills: string[];
  };
  onApplyFilters: (filters: FilterPanelProps['filters']) => void;
  onResetFilters: () => void;
};

const FilterPanel = ({ filters, onApplyFilters, onResetFilters }: FilterPanelProps) => {
  // États locaux synchronisés avec les props
  const [selectedContractTypes, setSelectedContractTypes] = useState<string[]>(filters.contractTypes);
  const [selectedExperienceLevels, setSelectedExperienceLevels] = useState<string[]>(filters.experienceLevels);
  const [selectedLocations, setSelectedLocations] = useState<string[]>(filters.locations);
  const [selectedSkills, setSelectedSkills] = useState<string[]>(filters.skills);
  const [showFiltersMobile, setShowFiltersMobile] = useState(false);

  // Synchroniser les états locaux si les props changent (reset)
  useEffect(() => {
    setSelectedContractTypes(filters.contractTypes);
    setSelectedExperienceLevels(filters.experienceLevels);
    setSelectedLocations(filters.locations);
    setSelectedSkills(filters.skills);
  }, [filters]);

  // Gestionnaires de changement pour chaque section
  const handleContractTypeChange = (id: string, checked: boolean) => {
    setSelectedContractTypes(prev => 
      checked ? [...prev, id] : prev.filter(item => item !== id)
    );
  };

  const handleExperienceLevelChange = (id: string, checked: boolean) => {
    setSelectedExperienceLevels(prev => 
      checked ? [...prev, id] : prev.filter(item => item !== id)
    );
  };

  const handleLocationChange = (id: string, checked: boolean) => {
    setSelectedLocations(prev => 
      checked ? [...prev, id] : prev.filter(item => item !== id)
    );
  };

  const handleSkillChange = (id: string, checked: boolean) => {
    setSelectedSkills(prev => 
      checked ? [...prev, id] : prev.filter(item => item !== id)
    );
  };

  // Appliquer les filtres
  const applyFilters = () => {
    onApplyFilters({
      contractTypes: selectedContractTypes,
      experienceLevels: selectedExperienceLevels,
      locations: selectedLocations,
      skills: selectedSkills,
    });
  };

  // Réinitialiser les filtres
  const resetFilters = () => {
    setSelectedContractTypes([]);
    setSelectedExperienceLevels([]);
    setSelectedLocations([]);
    setSelectedSkills([]);
    onResetFilters();
  };

  return (
    <div className="relative">
      {/* Bouton mobile pour afficher/masquer les filtres */}
      <button 
        className="md:hidden w-full mb-4 flex items-center justify-between bg-white dark:bg-neutral-800/70 p-4 rounded-lg border border-neutral-200 dark:border-neutral-700/80 shadow-subtle"
        onClick={() => setShowFiltersMobile(!showFiltersMobile)}
        aria-expanded={showFiltersMobile}
        aria-controls="mobile-filters"
      >
        <div className="flex items-center">
          <span className="text-neutral-800 dark:text-white font-medium text-sm">Filtres</span>
          <span className="ml-2 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300 px-2 py-0.5 rounded-full">
            {selectedContractTypes.length + selectedExperienceLevels.length + selectedLocations.length + selectedSkills.length || 0}
          </span>
        </div>
        <span className="transform transition-transform duration-300 ease-bounce-subtle">
          {showFiltersMobile ? 
            <FaChevronUp size={14} className="text-neutral-500 dark:text-neutral-400" /> : 
            <FaChevronDown size={14} className="text-neutral-500 dark:text-neutral-400" />}
        </span>
      </button>
      
      {/* Conteneur principal des filtres - responsive */}
      <div 
        id="mobile-filters"
        className={`bg-white dark:bg-neutral-800/50 p-4 sm:p-6 rounded-xl border border-neutral-200 dark:border-neutral-700/80 shadow-sm md:sticky md:top-24 transition-all duration-300 ${showFiltersMobile ? 'max-h-[2000px] opacity-100' : 'md:max-h-[2000px] md:opacity-100 max-h-0 opacity-0 overflow-hidden md:overflow-visible'}`}
      >
        <h2 className="text-lg sm:text-xl font-semibold text-neutral-800 dark:text-white mb-1">
          Filtres
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 mb-4 sm:mb-6">Affinez votre recherche d'emploi.</p>
        
        <div className="space-y-1">
        <FilterSection 
          title="Type de contrat"
          options={contractTypes}
          selectedOptions={selectedContractTypes}
          onChange={handleContractTypeChange}
        />
        <FilterSection 
          title="Niveau d'expérience"
          options={experienceLevels}
          selectedOptions={selectedExperienceLevels}
          onChange={handleExperienceLevelChange}
        />
        <FilterSection 
          title="Localisation"
          options={locations}
          selectedOptions={selectedLocations}
          onChange={handleLocationChange}
        />
        <FilterSection 
          title="Compétences"
          options={skills}
          selectedOptions={selectedSkills}
          onChange={handleSkillChange}
        />
      </div>

      <div className="mt-6 sm:mt-8 pt-4 sm:pt-6 border-t border-neutral-200 dark:border-neutral-700 space-y-2 sm:space-y-3">
        <button 
          onClick={applyFilters}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 sm:py-2.5 px-4 rounded-lg text-xs sm:text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-800 shadow-sm hover:shadow-md"
        >
          Appliquer les filtres
        </button>
        <button 
          onClick={resetFilters}
          className="w-full bg-transparent hover:bg-neutral-100 dark:hover:bg-neutral-700/60 text-neutral-700 dark:text-neutral-300 font-medium py-2 sm:py-2.5 px-4 rounded-lg text-xs sm:text-sm border border-neutral-300 dark:border-neutral-600 hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors focus:outline-none focus:ring-2 focus:ring-neutral-400 dark:focus:ring-neutral-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-800"
        >
          Réinitialiser
        </button>
      </div>
    </div>
    </div>
  );
};

export default FilterPanel;
