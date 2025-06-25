'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const SearchBar = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const router = useRouter();

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchTerm)}`);
    }
  };

  return (
    <form onSubmit={handleSearch} className="w-full max-w-2xl">
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Search className="w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors duration-200" />
        </div>
        <Input
          type="search"
          placeholder="Rechercher des offres d'emploi..."
          className="pl-10 pr-20 h-12 text-base bg-background/50 backdrop-blur-sm border-border/50 focus:border-primary/50 focus:bg-background transition-all duration-200"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          aria-label="Recherche d'emploi"
        />
        <Button
          type="submit"
          size="sm"
          className="absolute right-1.5 top-1.5 h-9 px-4 bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          Rechercher
        </Button>
      </div>
    </form>
  );
};

export default SearchBar;
