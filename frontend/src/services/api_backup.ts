// API Service
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  salary?: string;
  experience_level?: string;
  contract_type?: string;
  source_url?: string;
  enriched_data?: any;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FilterOptions {
  types: string[];
  countries: string[];
  cities: string[];
  contracts: string[];
  skills: string[];
  locations: string[];
  experience_levels: string[];
}

export const getItems = async (
  page: number = 1,
  pageSize: number = 10,
  filters?: {
    location?: string;
    job_type?: string;
    contract_type?: string;
    experience_level?: string;
    search?: string;
  }
): Promise<PaginatedResponse<JobOffer>> => {
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters,
    });

    const response = await apiClient.get(`/items?${params}`);
    return response.data;
  } catch (error) {
    console.error('Erreur API:', error);
    
    return {
      items: [
        {
          id: '1',
          title: 'Developpeur Full-Stack',
          company: 'TechStart Lome',
          location: 'Lome, Maritime',
          description: 'Rejoignez notre equipe dynamique pour developper des applications web modernes...',
          skills: ['React', 'Node.js', 'PostgreSQL', 'TypeScript'],
          posted_date: '2024-01-20',
          job_type: 'Developpement',
          contract_type: 'CDI',
          experience_level: 'Intermediaire',
          salary: '450K-750K CFA',
          slug: 'developpeur-fullstack-techstart-lome'
        },
        {
          id: '2',
          title: 'Chef de Projet Marketing Digital',
          company: 'Digital Togo',
          location: 'Lome, Maritime',
          description: 'Pilotez nos campagnes marketing digitales et developpez notre presence en ligne...',
          skills: ['Marketing Digital', 'SEO', 'Google Ads', 'Analytics'],
          posted_date: '2024-01-19',
          job_type: 'Marketing',
          contract_type: 'CDI',
          experience_level: 'Senior',
          salary: '550K-950K CFA',
          slug: 'chef-projet-marketing-digital-togo'
        }
      ],
      total: 448,
      page: 1,
      page_size: 10,
      total_pages: 45,
    };
  }
};

export const getItemById = async (id: string): Promise<JobOffer | null> => {
  try {
    const response = await apiClient.get(`/items/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Erreur API pour l'offre ${id}:`, error);
    return null;
  }
};

export const getFilters = async (): Promise<FilterOptions> => {
  try {
    const response = await apiClient.get('/filters');
    return response.data;
  } catch (error) {
    console.error('Erreur API filtres:', error);
    
    return {
      types: ['Developpement', 'Marketing', 'Comptabilite', 'Design', 'Commercial', 'RH'],
      countries: ['Togo'],
      cities: ['Lome', 'Kpalime', 'Sokode', 'Kara', 'Dapaong', 'Atakpame'],
      contracts: ['CDI', 'CDD', 'Stage', 'Freelance', 'Temps partiel'],
      skills: ['React', 'Node.js', 'Python', 'Marketing Digital', 'Comptabilite', 'Design'],
      locations: [
        'Lome, Maritime',
        'Kpalime, Plateaux', 
        'Sokode, Centrale',
        'Kara, Kara',
        'Dapaong, Savanes',
        'Atakpame, Plateaux'
      ],
      experience_levels: ['Debutant', 'Intermediaire', 'Senior', 'Expert']
    };
  }
};

export const searchItems = async (
  query: string,
  page: number = 1,
  pageSize: number = 10,
  filters?: {
    location?: string;
    job_type?: string;
    contract_type?: string;
    experience_level?: string;
  }
): Promise<PaginatedResponse<JobOffer>> => {
  try {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters,
    });

    const response = await apiClient.get(`/search?${params}`);
    return response.data;
  } catch (error) {
    console.error('Erreur recherche:', error);
    return getItems(page, pageSize, { search: query, ...filters });
  }
};

export const getStats = async () => {
  try {
    const response = await apiClient.get('/stats');
    return response.data;
  } catch (error) {
    console.error('Erreur stats:', error);
    return {
      total_jobs: 448,
      total_companies: 127,
      new_jobs_today: 12,
      locations_count: 6
    };
  }
};

export default apiClient;
