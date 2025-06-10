'use client';

import Link from 'next/link';
import { useState } from 'react';
import { FaBriefcase, FaBars, FaTimes } from 'react-icons/fa';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  return (
    <header className="w-full bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50 backdrop-blur-sm bg-white/90 dark:bg-neutral-900/90 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-center sm:justify-between">
          {/* Logo et titre */}
          <Link href="/" className="flex items-center space-x-2.5 group transform transition-transform duration-300 hover:scale-105">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 dark:from-primary-600 dark:to-primary-800 rounded-xl flex items-center justify-center shadow-md transition-all duration-300 group-hover:shadow-lg">
              <FaBriefcase className="text-white text-xl" />
            </div>
            <span className="text-lg font-bold tracking-tight text-neutral-900 dark:text-white">Job Aggregator</span>
          </Link>

          {/* Navigation - Desktop */}
          <nav className="flex items-center mt-4 sm:mt-0 space-x-1">
            <Link 
              href="/" 
              className="px-4 py-2 text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/60 rounded-lg transition-all duration-300 hover:shadow-sm"
            >
              Accueil
            </Link>
            <Link 
              href="/about" 
              className="px-4 py-2 text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/60 rounded-lg transition-all duration-300 hover:shadow-sm"
            >
              À propos
            </Link>
            <Link 
              href="/contact" 
              className="ml-2 px-5 py-2 bg-primary-600 text-white hover:bg-primary-700 rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:-translate-y-0.5 active:translate-y-0"
            >
              Contact
            </Link>
          </nav>

          {/* Hamburger menu - Mobile */}
          <button 
            className="sm:hidden absolute right-4 top-4 w-10 h-10 flex items-center justify-center text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-all duration-300 hover:shadow-md"
            onClick={toggleMenu}
            aria-label="Menu"
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <FaTimes size={20} /> : <FaBars size={20} />}
          </button>
        </div>

        {/* Menu mobile avec animation */}
        <div 
          className={`sm:hidden w-full overflow-hidden transition-all duration-300 ease-bounce-subtle ${isMenuOpen ? 'max-h-64 opacity-100' : 'max-h-0 opacity-0'}`}
        >
          <nav className="mt-4 py-3 space-y-2 border-t border-neutral-200 dark:border-neutral-800 pt-4">
            <Link 
              href="/" 
              className="block px-4 py-3 text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/60 rounded-lg transition-all duration-300 hover:shadow-sm transform hover:translate-x-1"
              onClick={() => setIsMenuOpen(false)}
            >
              Accueil
            </Link>
            <Link 
              href="/about" 
              className="block px-4 py-3 text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/60 rounded-lg transition-all duration-300 hover:shadow-sm transform hover:translate-x-1"
              onClick={() => setIsMenuOpen(false)}
            >
              À propos
            </Link>
            <Link 
              href="/contact" 
              className="block mt-3 px-4 py-3 bg-primary-600 text-white hover:bg-primary-700 rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:translate-x-1"
              onClick={() => setIsMenuOpen(false)}
            >
              Contact
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
