// API Service temporaire pour éviter les erreurs de compilation

export interface JobOffer {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  skills: string[];
  posted_date: string;
  job_type: string;
  slug: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Fonction temporaire - sera remplacée par la vraie API
export const getItems = async (): Promise<PaginatedResponse<any>> => {
  return {
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
  };
};

// Fonction temporaire
export const getItemById = async (id: string): Promise<JobOffer | null> => {
  return null;
};

// Fonction temporaire
export const getFilters = async () => {
    return {
      types: [],
      countries: [],
      cities: [],
      contracts: [],
      skills: [],
    };
};

// Fonction temporaire
export const searchItems = async (): Promise<PaginatedResponse<any>> => {
  return {
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
  };
};

export default {}; 