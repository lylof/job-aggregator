import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interface definitions - ENRICHIE avec tous les champs API
export interface JobOffer {
  // Champs de base
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  posted_date: string;
  job_type: string;
  slug: string;
  source_url?: string;
  
  // Classification automatique
  offer_category?: string; // 'job', 'scholarship', 'internship', 'training', 'volunteer'
  
  // Données enrichies LLM
  skills: string[];
  salary?: string;
  experience_level?: string;
  contract_type?: string;
  education_level?: string;
  
  // Informations entreprise enrichies
  company_logo_url?: string;
  company_website?: string;
  company_description?: string;
  
  // Données supplémentaires
  languages?: string[];
  sector?: string;
  tags?: string[];
  number_of_positions?: number;
  application_url?: string;
  contact_email?: string;
  other_benefits?: string;
  profile_required?: string;
  
  // Géolocalisation avancée
  item_country?: string;
  item_state?: string;
  item_latitude?: number;
  item_longitude?: number;
  detected_city?: string;
  detected_region?: string;
  detected_latitude?: number;
  detected_longitude?: number;
  remote_work_detected?: boolean;
  
  // Métadonnées
  is_remote?: boolean;
  expires_at?: string;
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

// Fetch job offers with pagination
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
    
    // Transformer les données de l'API backend vers le format frontend ENRICHI
    const transformedItems = response.data.items?.map((item: any) => ({
      // Champs de base
      id: item.item_id || item.id || '',
      title: item.item_title || item.title || '',
      company: item.company_name || item.company || '',
      location: item.item_city || item.location || 'Togo',
      description: item.item_description || item.description || '',
      posted_date: item.item_posted_at || item.posted_date || '',
      job_type: item.item_employment_type || item.job_type || '',
      slug: item.slug || item.item_id?.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase() || '',
      source_url: item.source_url || item.item_id,
      
      // Classification automatique
      offer_category: item.offer_category || 'job',
      
      // Données enrichies LLM
      skills: item.skills || [],
      salary: (item.salary !== null && item.salary !== undefined) ? item.salary : 'À négocier',
      experience_level: (item.experience_level !== null && item.experience_level !== undefined) ? item.experience_level : 'Non spécifié',
      contract_type: (item.contract_type !== null && item.contract_type !== undefined) ? item.contract_type : (item.item_employment_type || 'Non spécifié'),
      education_level: (item.education_level !== null && item.education_level !== undefined) ? item.education_level : 'Non spécifié',
      
      // Informations entreprise enrichies
      company_logo_url: item.company_logo_url || undefined,
      company_website: item.company_website || undefined,
      company_description: item.company_description || undefined,
      
      // Données supplémentaires
      languages: item.languages || [],
      sector: item.sector || 'Non spécifié',
      tags: item.tags || [],
      number_of_positions: item.number_of_positions || 1,
      application_url: item.application_url || undefined,
      contact_email: item.contact_email || undefined,
      other_benefits: item.other_benefits || undefined,
      profile_required: item.profile_required || undefined,
      
      // Géolocalisation avancée
      item_country: item.item_country || 'Togo',
      item_state: item.item_state || item.location,
      item_latitude: item.item_latitude || undefined,
      item_longitude: item.item_longitude || undefined,
      detected_city: item.detected_city || undefined,
      detected_region: item.detected_region || undefined,
      detected_latitude: item.detected_latitude || undefined,
      detected_longitude: item.detected_longitude || undefined,
      remote_work_detected: item.remote_work_detected || false,
      
      // Métadonnées
      is_remote: item.item_is_remote || item.remote_work_detected || false,
      expires_at: item.item_expires_at || undefined,
      enriched_data: item.enriched_data || item.raw_data
    })) || [];

    return {
      items: transformedItems,
      total: response.data.total || 0,
      page: response.data.page || page,
      page_size: response.data.page_size || pageSize,
      total_pages: response.data.total_pages || Math.ceil(response.data.total / pageSize),
    };
  } catch (error) {
    console.error('API Error:', error);
    
    // Fallback data for Togo
    return {
      items: [
        {
          id: '1',
          title: 'Developpeur Full-Stack',
          company: 'TechStart Lome',
          location: 'Lome, Maritime',
          description: 'Rejoignez notre equipe dynamique pour developper des applications web modernes avec React, Node.js et PostgreSQL.',
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
          description: 'Pilotez nos campagnes marketing digitales et developpez notre presence en ligne sur le marche togolais.',
          skills: ['Marketing Digital', 'SEO', 'Google Ads', 'Analytics'],
          posted_date: '2024-01-19',
          job_type: 'Marketing',
          contract_type: 'CDI',
          experience_level: 'Senior',
          salary: '550K-950K CFA',
          slug: 'chef-projet-marketing-digital-togo'
        },
        {
          id: '3',
          title: 'Comptable Senior',
          company: 'Cabinet Expertise',
          location: 'Lome, Maritime',
          description: 'Gestion comptable complete pour nos clients entreprises avec expertise fiscale togolaise.',
          skills: ['Comptabilite', 'Fiscalite', 'Excel', 'SAGE'],
          posted_date: '2024-01-18',
          job_type: 'Comptabilite',
          contract_type: 'CDI',
          experience_level: 'Senior',
          salary: '400K-650K CFA',
          slug: 'comptable-senior-cabinet-expertise'
        },
        {
          id: '4',
          title: 'Designer UI/UX',
          company: 'Creative Studio Togo',
          location: 'Lome, Maritime',
          description: 'Creation d\'interfaces utilisateur modernes et experiences utilisateur optimisees pour applications mobiles et web.',
          skills: ['Figma', 'Adobe XD', 'Prototyping', 'User Research'],
          posted_date: '2024-01-17',
          job_type: 'Design',
          contract_type: 'CDD',
          experience_level: 'Intermediaire',
          salary: '350K-550K CFA',
          slug: 'designer-ui-ux-creative-studio'
        },
        {
          id: '5',
          title: 'Commercial B2B',
          company: 'Solutions Business Togo',
          location: 'Lome, Maritime',
          description: 'Developpement commercial et gestion portefeuille clients entreprises sur le territoire togolaise.',
          skills: ['Vente B2B', 'Negociation', 'Prospection', 'CRM'],
          posted_date: '2024-01-16',
          job_type: 'Commercial',
          contract_type: 'CDI',
          experience_level: 'Intermediaire',
          salary: '300K-500K CFA',
          slug: 'commercial-b2b-solutions-business'
        }
      ],
      total: 448,
      page: 1,
      page_size: 10,
      total_pages: 45,
    };
  }
};

// Fetch specific job offer
export const getItemById = async (id: string): Promise<JobOffer | null> => {
  try {
    const response = await apiClient.get(`/items/${id}`);
    return response.data;
  } catch (error) {
    console.error(`API Error for job ${id}:`, error);
    return null;
  }
};

// Fetch filter options
export const getFilters = async (): Promise<FilterOptions> => {
  try {
    const response = await apiClient.get('/filters');
    return response.data;
  } catch (error) {
    console.error('API Error for filters:', error);
    
    // Fallback data for Togo
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

// Search job offers
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
    console.error('Search API Error:', error);
    return getItems(page, pageSize, { search: query, ...filters });
  }
};

// Get platform statistics
export const getStats = async () => {
  try {
    const response = await apiClient.get('/stats');
    return response.data;
  } catch (error) {
    console.error('Stats API Error:', error);
    return {
      total_jobs: 448,
      total_companies: 127,
      new_jobs_today: 12,
      locations_count: 6
    };
  }
};

// Utility function to map API response to JobOffer interface
export const mapItemToJobOffer = (item: any): JobOffer => {
  return {
    id: item.id || '',
    title: item.title || '',
    company: item.company || '',
    location: item.location || '',
    description: item.description || '',
    skills: item.skills || [],
    posted_date: item.posted_date || '',
    job_type: item.job_type || '',
    slug: item.slug || '',
    salary: item.salary,
    experience_level: item.experience_level,
    contract_type: item.contract_type,
    source_url: item.source_url,
    enriched_data: item.enriched_data
  };
};

export default apiClient; 