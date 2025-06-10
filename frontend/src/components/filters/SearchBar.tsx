'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { FaSearch } from 'react-icons/fa';

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
    <form onSubmit={handleSearch} className="w-full max-w-2xl ml-0">
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 sm:pl-3.5 pointer-events-none transition-all duration-300 group-focus-within:text-primary-500">
          <FaSearch className="w-4 h-4 sm:w-5 sm:h-5 text-neutral-400 dark:text-neutral-500 group-focus-within:text-primary-500 dark:group-focus-within:text-primary-400 transition-colors duration-300" />
        </div>
        <input
          type="search"
          id="default-search"
          placeholder="Poste, compétence, entreprise..."
          className="block w-full p-3 sm:p-4 pl-10 sm:pl-12 text-sm sm:text-base text-neutral-900 dark:text-neutral-100 border border-neutral-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:placeholder-neutral-400 dark:focus:ring-primary-500 dark:focus:border-primary-500 shadow-sm hover:shadow-md transition-all duration-300 ease-bounce-subtle"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          required
          aria-label="Recherche d'emploi"
        />
        <button
          type="submit"
          className="text-white absolute right-2 sm:right-2.5 bottom-2 sm:bottom-2.5 bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-xs sm:text-sm px-3 sm:px-5 py-1.5 sm:py-2.5 dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800 transition-all duration-300 ease-bounce-subtle shadow-sm hover:shadow-md transform hover:-translate-y-0.5 active:translate-y-0"
          aria-label="Rechercher"
        >
          Rechercher
        </button>
      </div>
    </form>
  );
};

export default SearchBar;
