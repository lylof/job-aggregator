import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
I
export interface JobOffer {
  id: string;
  title: string;
  company: string;
  company_logo?: string;
  location: string;
  description: string;
  skills: string[];
  posted_date: string;
  salary_range?: string;
  job_type: string;
  slug: string;
  date_posted_local?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Nouveau : Types pour items_cache (Supabase)
export interface ItemCache {
  item_id: string;
  item_provider: string;
  item_type: string;
  source_type: string;
  source_name?: string;
  created_at?: string;
  updated_at?: string;
  item_posted_at?: string;
  item_expires_at?: string;
  item_title?: string;
  company_name?: string;
  item_employment_type?: string;
  item_is_remote?: boolean;
  item_city?: string;
  item_state?: string;
  item_country?: string;
  item_latitude?: number;
  item_longitude?: number;
  item_description?: string;
  item_highlights?: Record<string, any>;
  raw_data: Record<string, any>;
  sync_batch_id?: string;
  is_active?: boolean;
  job_detailed?: boolean;
  details_fetched_at?: string;
  job_full_data?: Record<string, any>;
}

// Mapping ItemCache -> JobOffer (pour compatibilité composants)
export function mapItemToJobOffer(item: ItemCache): JobOffer {
  return {
    id: item.item_id,
    title: item.item_title || '',
    company: item.company_name || '',
    company_logo: '', // à enrichir si possible
    location: [item.item_city, item.item_country].filter(Boolean).join(', '),
    description: item.item_description || '',
    skills: item.item_highlights?.qualifications || [],
    posted_date: item.item_posted_at || item.created_at || '',
    salary_range: '', // à enrichir si possible
    job_type: item.item_employment_type || '',
    slug: item.item_id, // fallback, à améliorer si besoin
    date_posted_local: item.item_posted_at || '',
  };
}

// Récupérer les items depuis /items (API Supabase via FastAPI)
export const getItems = async (
  page = 1, 
  pageSize = 10, 
  filters?: Record<string, any>
): Promise<PaginatedResponse<ItemCache>> => {
  let url = `/items?page=${page}&page_size=${pageSize}`;
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          url += `&${key}=${encodeURIComponent(String(value))}`;
        }
      });
    }
    const response = await api.get(url);
  // Si l'API backend fournit la pagination, utilise-la, sinon fallback
  if (
    response.data &&
    typeof response.data === 'object' &&
    'items' in response.data &&
    'total' in response.data
  ) {
    return response.data;
  }
  // Fallback : on retourne tout comme une seule page
  return {
    items: response.data,
    total: response.data.length,
    page,
    page_size: pageSize,
    total_pages: 1,
  };
};

// Recherche d'items (par type, pays, etc.)
export const searchItems = async (
  filters: Record<string, any>,
  page = 1,
  pageSize = 10
): Promise<PaginatedResponse<ItemCache>> => {
  return getItems(page, pageSize, filters);
};

// Statistiques globales (optionnel)
export const getStatistics = async () => {
  try {
    const response = await api.get('/statistics/');
    return response.data;
  } catch (error) {
    console.error('Error fetching statistics:', error);
    throw error;
  }
};

// Récupérer un item par ID (pour la page détail)
export const getItemById = async (itemId: string): Promise<JobOffer> => {
  const response = await api.get(`/items/${itemId}`);
  const item = response.data;
  return mapItemToJobOffer(item);
};

// Récupérer dynamiquement les options de filtre depuis l'API
export const getFilters = async () => {
  try {
    const response = await api.get('/items/filters');
    if (response.data && response.data.error) {
      // Affiche un message d'erreur utilisateur
      alert('Erreur lors de la récupération des filtres : ' + response.data.error + '\nVérifiez la connexion à la base de données ou contactez l\'administrateur.');
    }
    return response.data;
  } catch (error) {
    console.error('Erreur lors de la récupération des filtres:', error);
    // Fallback : retourne des filtres vides pour éviter le crash du frontend
    alert('Erreur critique lors de la récupération des filtres. Vérifiez la connexion au backend.');
    return {
      types: [],
      countries: [],
      cities: [],
      contracts: [],
      skills: [],
    };
  }
};

export default api;
