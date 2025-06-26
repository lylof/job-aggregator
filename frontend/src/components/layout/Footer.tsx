'use client';

import Link from 'next/link';
import { Github, Twitter, Linkedin, Mail, MapPin } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-card border-t border-border">
      <div className="container-custom py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Logo et description */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center space-x-3 mb-4 group">
              <svg 
                width="100" 
                height="28" 
                viewBox="0 0 148 42" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
                className="h-7 w-auto group-hover:scale-105 transition-transform duration-200"
              >
                <path d="M126.287 35.9187V10.9905H131.557V21.2758H142.256V10.9905H147.515V35.9187H142.256V25.6212H131.557V35.9187H126.287Z" fill="#265DF5"/>
                <path d="M118.804 18.1615C118.706 17.1797 118.288 16.4169 117.55 15.8732C116.812 15.3295 115.809 15.0577 114.544 15.0577C113.683 15.0577 112.957 15.1794 112.365 15.4228C111.772 15.6582 111.318 15.9868 111.001 16.4088C110.693 16.8307 110.539 17.3095 110.539 17.8451C110.523 18.2914 110.616 18.6809 110.819 19.0136C111.03 19.3463 111.318 19.6343 111.683 19.8778C112.048 20.1131 112.47 20.32 112.949 20.4986C113.428 20.669 113.939 20.815 114.483 20.9367L116.722 21.4723C117.81 21.7157 118.808 22.0403 119.717 22.4461C120.625 22.8518 121.413 23.3508 122.078 23.9432C122.743 24.5356 123.259 25.2335 123.624 26.0368C123.997 26.8402 124.188 27.7612 124.196 28.7998C124.188 30.3254 123.798 31.6481 123.027 32.7679C122.265 33.8796 121.161 34.7438 119.717 35.3605C118.28 35.9691 116.548 36.2734 114.519 36.2734C112.507 36.2734 110.754 35.9651 109.261 35.3484C107.776 34.7316 106.616 33.8187 105.78 32.6097C104.952 31.3925 104.518 29.8872 104.477 28.0939H109.577C109.634 28.9297 109.874 29.6275 110.296 30.1874C110.726 30.7392 111.298 31.1571 112.012 31.4412C112.734 31.7171 113.549 31.855 114.458 31.855C115.351 31.855 116.126 31.7252 116.783 31.4655C117.449 31.2058 117.964 30.8447 118.329 30.3822C118.694 29.9197 118.877 29.3881 118.877 28.7877C118.877 28.2278 118.71 27.7571 118.378 27.3757C118.053 26.9943 117.574 26.6697 116.941 26.402C116.317 26.1342 115.55 25.8907 114.641 25.6716L111.927 24.99C109.825 24.4788 108.165 23.6795 106.948 22.5921C105.731 21.5048 105.126 20.0401 105.135 18.198C105.126 16.6887 105.528 15.3701 106.34 14.2422C107.159 13.1142 108.283 12.2338 109.711 11.6008C111.139 10.9679 112.762 10.6514 114.58 10.6514C116.43 10.6514 118.045 10.9679 119.424 11.6008C120.812 12.2338 121.891 13.1142 122.662 14.2422C123.433 15.3701 123.831 16.6766 123.855 18.1615H118.804Z" fill="#265DF5"/>
                <path d="M97.1174 10.9905H102.388V27.1792C102.388 28.9969 101.954 30.5873 101.085 31.9506C100.225 33.3139 99.0203 34.3769 97.4704 35.1397C95.9205 35.8943 94.115 36.2716 92.0539 36.2716C89.9847 36.2716 88.1751 35.8943 86.6252 35.1397C85.0753 34.3769 83.8703 33.3139 83.0101 31.9506C82.15 30.5873 81.7199 28.9969 81.7199 27.1792V10.9905H86.9903V26.7288C86.9903 27.6782 87.1973 28.5222 87.6111 29.2606C88.0331 29.999 88.6255 30.5792 89.3882 31.0012C90.151 31.4231 91.0396 31.6341 92.0539 31.6341C93.0763 31.6341 93.9649 31.4231 94.7196 31.0012C95.4823 30.5792 96.0706 29.999 96.4845 29.2606C96.9065 28.5222 97.1174 27.6782 97.1174 26.7288V10.9905Z" fill="#265DF5"/>
                <path d="M60.8606 35.9187V10.9905H70.6956C72.5863 10.9905 74.1971 11.3516 75.5279 12.0738C76.8587 12.7878 77.873 13.7819 78.5708 15.0559C79.2768 16.3218 79.6298 17.7824 79.6298 19.4378C79.6298 21.0932 79.2728 22.5538 78.5587 23.8197C77.8446 25.0856 76.81 26.0715 75.4548 26.7775C74.1078 27.4835 72.4767 27.8365 70.5617 27.8365H64.2931V23.6128H69.7096C70.724 23.6128 71.5598 23.4383 72.2171 23.0894C72.8825 22.7324 73.3775 22.2414 73.7021 21.6166C74.0348 20.9836 74.2011 20.2574 74.2011 19.4378C74.2011 18.6101 74.0348 17.8879 73.7021 17.2712C73.3775 16.6464 72.8825 16.1635 72.2171 15.8227C71.5517 15.4738 70.7077 15.2993 69.6853 15.2993H66.1311V35.9187H60.8606Z" fill="#265DF5"/>
                <path d="M5.45445 10.3289C8.73925 2.47107 17.7721 -1.2361 25.63 2.0487L39.8325 7.98577C45.1215 10.1967 47.6167 16.2766 45.4058 21.5656L43.6863 25.6788C38.0722 39.1088 22.6339 45.4448 9.20385 39.8307C1.64322 36.6701 -1.92375 27.9789 1.23682 20.4182L5.45445 10.3289Z" fill="url(#paint0_linear_footer)"/>
                <path d="M11.6564 37.8237L5.05494 29.1929L29.6129 10.4088L36.2144 19.0396L11.6564 37.8237Z" fill="url(#paint1_linear_footer)"/>
                <defs>
                  <linearGradient id="paint0_linear_footer" x1="73.7998" y1="0.851562" x2="65.8294" y2="49.969" gradientUnits="userSpaceOnUse">
                    <stop offset="1" stopColor="#265DF5"/>
                  </linearGradient>
                  <linearGradient id="paint1_linear_footer" x1="27.0577" y1="17.1298" x2="0.220227" y2="32.2398" gradientUnits="userSpaceOnUse">
                    <stop offset="0.1875" stopColor="white"/>
                    <stop offset="0.798077" stopColor="#275DF5" stopOpacity="0"/>
                  </linearGradient>
                </defs>
              </svg>
            </Link>
            
            <p className="text-muted-foreground mb-6 max-w-md leading-relaxed">
              Plateforme moderne d'agrégation d'offres d'emploi avec données enrichies 
              et filtres intelligents pour vous aider à trouver votre emploi idéal au Togo.
            </p>
            
            {/* Contact rapide */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="w-4 h-4" />
                <span>contact@push.tg</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>Lomé, Togo</span>
              </div>
            </div>
          </div>
          
          {/* Liens rapides */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Navigation</h4>
            <ul className="space-y-3">
              <li>
                <Link 
                  href="/" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Accueil
                </Link>
              </li>
              <li>
                <Link 
                  href="/search" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Rechercher un emploi
                </Link>
              </li>
              <li>
                <Link 
                  href="/about" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  À propos
                </Link>
              </li>
              <li>
                <Link 
                  href="/contact" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Contact
                </Link>
              </li>
            </ul>
          </div>
          
          {/* Réseaux sociaux et informations */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Communauté</h4>
            
            <div className="flex space-x-2 mb-6">
              <Button variant="ghost" size="icon" className="w-9 h-9" asChild>
              <a 
                href="https://github.com" 
                target="_blank" 
                rel="noopener noreferrer"
                aria-label="GitHub"
              >
                  <Github className="w-4 h-4" />
              </a>
              </Button>
              <Button variant="ghost" size="icon" className="w-9 h-9" asChild>
              <a 
                href="https://twitter.com" 
                target="_blank" 
                rel="noopener noreferrer"
                aria-label="Twitter"
              >
                  <Twitter className="w-4 h-4" />
              </a>
              </Button>
              <Button variant="ghost" size="icon" className="w-9 h-9" asChild>
              <a 
                href="https://linkedin.com" 
                target="_blank" 
                rel="noopener noreferrer"
                aria-label="LinkedIn"
              >
                  <Linkedin className="w-4 h-4" />
              </a>
              </Button>
            </div>
            
            {/* Statistiques */}
            <Card className="glass-effect">
              <CardContent className="p-4">
                <h5 className="font-medium text-sm mb-2">Plateforme</h5>
                <div className="space-y-1 text-xs text-muted-foreground">
                  <div>✅ API Opérationnelle</div>
                  <div>📊 448 offres d'emploi</div>
                  <div>🏢 127+ entreprises</div>
                  <div>🇹🇬 Marché togolais</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator className="my-8" />
        
        {/* Bas de page */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {currentYear} PUSH. Tous droits réservés.
          </p>
          
          <div className="flex items-center gap-4">
            <Link 
              href="/privacy" 
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Confidentialité
            </Link>
            <Link 
              href="/terms" 
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Conditions
            </Link>
            <Link 
              href="/sitemap" 
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Plan du site
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
