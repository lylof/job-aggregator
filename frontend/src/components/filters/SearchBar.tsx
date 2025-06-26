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
    <form onSubmit={handleSearch} className="w-full max-w-3xl">
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/20 to-primary/10 rounded-full blur opacity-30 group-focus-within:opacity-60 transition-opacity duration-300"></div>
        
        <div className="relative bg-background/80 backdrop-blur-md border border-border/30 rounded-full shadow-lg group-focus-within:shadow-xl group-focus-within:border-primary/40 transition-all duration-300">
          
          <div className="absolute inset-y-0 left-0 flex items-center pl-6 pointer-events-none">
            <Search className="w-5 h-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-200" />
        </div>
          
          <Input
          type="search"
            placeholder="Rechercher des offres d'emploi au Togo..."
            className="pl-14 pr-32 h-14 text-lg bg-transparent border-none focus:ring-0 focus:outline-none placeholder:text-muted-foreground/70 rounded-full"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          aria-label="Recherche d'emploi"
        />
          
          <Button
          type="submit"
            size="default"
            className="absolute right-2 top-2 h-10 px-6 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full shadow-md hover:shadow-lg transition-all duration-200 font-medium"
        >
          Rechercher
          </Button>
        </div>
      </div>
    </form>
  );
};

export default SearchBar;
