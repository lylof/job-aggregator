"use client"

import React from 'react';
import { Badge } from './badge';
import { cn } from '@/lib/utils';

interface CategoryBadgeProps {
  category: string;
  className?: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category, className }) => {
  const getCategoryConfig = (cat: string) => {
    switch (cat?.toLowerCase()) {
      case 'job':
        return {
          label: 'Emploi',
          variant: 'default' as const,
          className: 'bg-blue-100 text-blue-800 hover:bg-blue-200 border-blue-200'
        };
      case 'scholarship':
        return {
          label: 'Bourse',
          variant: 'secondary' as const,
          className: 'bg-purple-100 text-purple-800 hover:bg-purple-200 border-purple-200'
        };
      case 'internship':
        return {
          label: 'Stage',
          variant: 'outline' as const,
          className: 'bg-green-100 text-green-800 hover:bg-green-200 border-green-200'
        };
      case 'training':
        return {
          label: 'Formation',
          variant: 'secondary' as const,
          className: 'bg-orange-100 text-orange-800 hover:bg-orange-200 border-orange-200'
        };
      case 'volunteer':
        return {
          label: 'Bénévolat',
          variant: 'outline' as const,
          className: 'bg-pink-100 text-pink-800 hover:bg-pink-200 border-pink-200'
        };
      default:
        return {
          label: 'Autre',
          variant: 'secondary' as const,
          className: 'bg-gray-100 text-gray-800 hover:bg-gray-200 border-gray-200'
        };
    }
  };

  const config = getCategoryConfig(category);

  return (
    <Badge 
      variant={config.variant}
      className={cn(config.className, className)}
    >
      {config.label}
    </Badge>
  );
}; 