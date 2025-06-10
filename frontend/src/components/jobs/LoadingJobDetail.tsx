const LoadingJobDetail = () => {
  return (
    <div className="max-w-4xl mx-auto animate-pulse">
      {/* Navigation de retour */}
      <div className="h-6 w-32 bg-secondary-200 dark:bg-secondary-700 rounded mb-6"></div>
      
      {/* En-tête de l'offre */}
      <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Logo placeholder */}
          <div className="w-20 h-20 bg-secondary-200 dark:bg-secondary-700 rounded-md"></div>
          
          {/* Informations principales */}
          <div className="flex-1 space-y-4">
            <div className="h-7 bg-secondary-200 dark:bg-secondary-700 rounded w-3/4"></div>
            <div className="h-5 bg-secondary-200 dark:bg-secondary-700 rounded w-1/2"></div>
            
            {/* Détails de l'offre */}
            <div className="flex flex-wrap gap-4">
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-24"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-20"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-32"></div>
            </div>
            
            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              <div className="h-10 bg-secondary-200 dark:bg-secondary-700 rounded w-40"></div>
              <div className="h-10 w-10 bg-secondary-200 dark:bg-secondary-700 rounded"></div>
              <div className="h-10 w-10 bg-secondary-200 dark:bg-secondary-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Contenu principal */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Colonne principale - Description */}
        <div className="md:col-span-2">
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6 mb-6">
            <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded w-48 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-3/4"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-5/6"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-4/5"></div>
            </div>
          </div>
          
          {/* Compétences requises */}
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6">
            <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded w-48 mb-4"></div>
            <div className="flex flex-wrap gap-2">
              {[...Array(6)].map((_, index) => (
                <div 
                  key={index} 
                  className="h-8 bg-secondary-200 dark:bg-secondary-700 rounded-full w-20"
                ></div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Colonne latérale - Informations supplémentaires */}
        <div className="md:col-span-1">
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6 mb-6">
            <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded w-40 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-5/6"></div>
              <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-1/2"></div>
            </div>
          </div>
          
          {/* Formulaire de candidature */}
          <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-card p-6">
            <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded w-40 mb-4"></div>
            <div className="space-y-4">
              <div className="space-y-1">
                <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-24"></div>
                <div className="h-10 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              </div>
              <div className="space-y-1">
                <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-16"></div>
                <div className="h-10 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              </div>
              <div className="space-y-1">
                <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-32"></div>
                <div className="h-10 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              </div>
              <div className="space-y-1">
                <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-28"></div>
                <div className="h-24 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
              </div>
              <div className="h-10 bg-secondary-200 dark:bg-secondary-700 rounded w-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingJobDetail;
