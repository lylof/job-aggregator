const LoadingSkeleton = () => (
  <div className="card p-5 animate-pulse">
    <div className="flex gap-4">
      {/* Logo placeholder */}
      <div className="w-[60px] h-[60px] bg-secondary-200 dark:bg-secondary-700 rounded-md flex-shrink-0"></div>
      
      <div className="flex-1 space-y-3">
        {/* Title placeholder */}
        <div className="h-5 bg-secondary-200 dark:bg-secondary-700 rounded w-3/4"></div>
        
        {/* Company placeholder */}
        <div className="h-4 bg-secondary-200 dark:bg-secondary-700 rounded w-1/2"></div>
        
        {/* Details placeholder */}
        <div className="flex space-x-4">
          <div className="h-3 bg-secondary-200 dark:bg-secondary-700 rounded w-20"></div>
          <div className="h-3 bg-secondary-200 dark:bg-secondary-700 rounded w-24"></div>
          <div className="h-3 bg-secondary-200 dark:bg-secondary-700 rounded w-16"></div>
        </div>
        
        {/* Tags placeholder */}
        <div className="flex flex-wrap gap-2">
          <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded-full w-16"></div>
          <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded-full w-20"></div>
          <div className="h-6 bg-secondary-200 dark:bg-secondary-700 rounded-full w-14"></div>
        </div>
      </div>
    </div>
  </div>
);

const LoadingJobList = () => {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <div className="h-5 bg-secondary-200 dark:bg-secondary-700 rounded w-40 animate-pulse"></div>
        <div className="h-8 bg-secondary-200 dark:bg-secondary-700 rounded w-32 animate-pulse"></div>
      </div>
      
      {[...Array(5)].map((_, index) => (
        <LoadingSkeleton key={index} />
      ))}
    </div>
  );
};

export default LoadingJobList;
