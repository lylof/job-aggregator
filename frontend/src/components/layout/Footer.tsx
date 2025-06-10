'use client';

import Link from 'next/link';
import { FaBriefcase, FaGithub, FaTwitter, FaLinkedin } from 'react-icons/fa';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-white dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800 pt-12 sm:pt-16 pb-8 sm:pb-12">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Logo et description */}
          <div className="md:col-span-5">
            <div className="flex items-center space-x-2.5 mb-4">
              <div className="w-8 h-8 bg-primary-50 dark:bg-primary-900/30 rounded-lg flex items-center justify-center transition-colors">
                <FaBriefcase className="text-primary-600 dark:text-primary-400 text-lg" />
              </div>
              <span className="text-base font-semibold tracking-tight text-neutral-900 dark:text-white">Job Aggregator</span>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4 max-w-md">
              Plateforme d&apos;agrégation d&apos;offres d&apos;emploi enrichies pour vous aider à trouver votre emploi idéal.
            </p>
          </div>
          
          {/* Liens rapides */}
          <div className="md:col-span-3">
            <h4 className="text-sm font-medium text-neutral-900 dark:text-white mb-4">Liens rapides</h4>
            <ul className="space-y-2.5">
              <li>
                <Link 
                  href="/" 
                  className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
                >
                  Accueil
                </Link>
              </li>
              <li>
                <Link 
                  href="/about" 
                  className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
                >
                  À propos
                </Link>
              </li>
              <li>
                <Link 
                  href="/contact" 
                  className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
                >
                  Contact
                </Link>
              </li>
            </ul>
          </div>
          
          {/* Réseaux sociaux */}
          <div className="md:col-span-4">
            <h4 className="text-sm font-medium text-neutral-900 dark:text-white mb-4">Suivez-nous</h4>
            <div className="flex space-x-3">
              <a 
                href="https://github.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-9 h-9 flex items-center justify-center rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
                aria-label="GitHub"
              >
                <FaGithub size={18} />
              </a>
              <a 
                href="https://twitter.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-9 h-9 flex items-center justify-center rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
                aria-label="Twitter"
              >
                <FaTwitter size={18} />
              </a>
              <a 
                href="https://linkedin.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-9 h-9 flex items-center justify-center rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
                aria-label="LinkedIn"
              >
                <FaLinkedin size={18} />
              </a>
            </div>
          </div>
        </div>

        {/* Ligne de séparation */}
        <hr className="my-8 border-neutral-200 dark:border-neutral-800" />
        
        {/* Copyright */}
        <div className="flex flex-col md:flex-row items-center justify-center md:justify-between text-center md:text-left space-y-4 md:space-y-0">
          <p className="text-xs text-neutral-500 dark:text-neutral-500">
            &copy; {currentYear} Job Aggregator. Tous droits réservés.
          </p>
          <div className="flex space-x-6">
            <a 
              href="/privacy" 
              className="text-xs text-neutral-500 hover:text-neutral-800 dark:text-neutral-500 dark:hover:text-neutral-300 transition-colors"
            >
              Politique de confidentialité
            </a>
            <a 
              href="/terms" 
              className="text-xs text-neutral-500 hover:text-neutral-800 dark:text-neutral-500 dark:hover:text-neutral-300 transition-colors"
            >
              Conditions d&apos;utilisation
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
