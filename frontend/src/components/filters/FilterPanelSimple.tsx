'use client';

import { useState } from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';

interface FilterState {
  contractTypes: string[];
  locations: string[];
  experienceLevels: string[];
}

interface FilterPanelProps {
  filters: FilterState;
  onApplyFilters: (filters: FilterState) => void;
  onResetFilters: () => void;
}

// Options de filtres simplifiées
const contractTypeOptions = [
  { value: 'cdi', label: 'CDI' },
  { value: 'cdd', label: 'CDD' },
  { value: 'stage', label: 'Stage' },
  { value: 'freelance', label: 'Freelance' },
];

const experienceOptions = [
  { value: 'junior', label: 'Junior (0-2 ans)' },
  { value: 'confirme', label: 'Confirmé (3-5 ans)' },
  { value: 'senior', label: 'Senior (5+ ans)' },
];

// Régions principales du Togo
const locationOptions = [
  { value: 'lome', label: 'Lomé' },
  { value: 'maritime', label: 'Région Maritime' },
  { value: 'plateaux', label: 'Région des Plateaux' },
  { value: 'centrale', label: 'Région Centrale' },
  { value: 'remote', label: 'Télétravail' },
];

const FilterPanelSimple = ({ filters, onApplyFilters, onResetFilters }: FilterPanelProps) => {
  const [localFilters, setLocalFilters] = useState(filters);

  const handleFilterChange = (category: keyof FilterState, value: string) => {
    setLocalFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(item => item !== value)
        : [...prev[category], value]
    }));
  };

  const handleApply = () => {
    onApplyFilters(localFilters);
  };

  const handleReset = () => {
    const resetFilters = {
      contractTypes: [],
      experienceLevels: [],
      locations: [],
    };
    setLocalFilters(resetFilters);
    onResetFilters();
  };

  const getTotalFilters = () => {
    return Object.values(localFilters).reduce((total, arr) => total + arr.length, 0);
  };

  const renderFilterGroup = (
    title: string,
    category: keyof FilterState,
    options: { value: string; label: string }[]
  ) => (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium text-foreground">{title}</Label>
      <div className="space-y-1">
        {options.map(option => (
          <label 
            key={option.value}
            className="flex items-center space-x-2 cursor-pointer group"
          >
            <input
              type="checkbox"
              checked={localFilters[category].includes(option.value)}
              onChange={() => handleFilterChange(category, option.value)}
              className="w-3 h-3 text-primary bg-background border-border rounded focus:ring-1 focus:ring-primary focus:ring-offset-0"
            />
            <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
              {option.label}
            </span>
          </label>
        ))}
      </div>
    </div>
  );

  return (
    <Card className="sticky top-20 h-fit">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Filter className="w-3 h-3 text-primary" />
          <CardTitle className="text-sm">Filtres</CardTitle>
          {getTotalFilters() > 0 && (
            <Badge variant="secondary" className="text-xs px-1.5 py-0.5">
              {getTotalFilters()}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        
        {/* Type de contrat */}
        {renderFilterGroup('Type de contrat', 'contractTypes', contractTypeOptions)}
        
        <Separator className="my-2" />
        
        {/* Localisation */}
        {renderFilterGroup('Localisation', 'locations', locationOptions)}
        
        <Separator className="my-2" />
        
        {/* Expérience */}
        {renderFilterGroup('Expérience', 'experienceLevels', experienceOptions)}
        
        <Separator className="my-2" />
        
        {/* Boutons d'action */}
        <div className="space-y-1.5 pt-1">
          <Button 
            onClick={handleApply}
            className="w-full h-8"
            size="sm"
          >
            Filtrer
          </Button>
          
          <Button 
            variant="outline" 
            onClick={handleReset}
            className="w-full h-8"
            size="sm"
            disabled={getTotalFilters() === 0}
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Réinitialiser
          </Button>
        </div>

        {/* Filtres actifs compacts */}
        {getTotalFilters() > 0 && (
          <div className="space-y-1 pt-1">
            <Label className="text-xs font-medium text-muted-foreground">Actifs</Label>
            <div className="flex flex-wrap gap-1">
              {Object.entries(localFilters).map(([category, values]) =>
                values.slice(0, 2).map(value => ( // Limite à 2 badges visibles
                  <Badge 
                    key={`${category}-${value}`}
                    variant="secondary"
                    className="text-xs px-1.5 py-0.5 cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                    onClick={() => handleFilterChange(category as keyof FilterState, value)}
                  >
                    {value} ×
                  </Badge>
                ))
              )}
              {getTotalFilters() > 2 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0.5">
                  +{getTotalFilters() - 2}
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FilterPanelSimple; 