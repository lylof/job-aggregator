import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface JobOffer {
  id: number;
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

export const getJobs = async (
  page = 1, 
  pageSize = 10, 
  filters?: Record<string, any>
): Promise<PaginatedResponse<JobOffer>> => {
  try {
    let url = `/job-offers/?page=${page}&page_size=${pageSize}`;
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          url += `&${key}=${encodeURIComponent(String(value))}`;
        }
      });
    }
    
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('Error fetching jobs:', error);
    throw error;
  }
};

export const searchJobs = async (
  query: string,
  page = 1,
  pageSize = 10
): Promise<PaginatedResponse<JobOffer>> => {
  try {
    const url = `/search/?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`;
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('Error searching jobs:', error);
    throw error;
  }
};

export const getJobById = async (id: number): Promise<JobOffer> => {
  try {
    const response = await api.get(`/job-offers/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching job with ID ${id}:`, error);
    throw error;
  }
};

export const getJobBySlug = async (slug: string): Promise<JobOffer> => {
  try {
    const response = await api.get(`/job-offers/slug/${slug}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching job with slug ${slug}:`, error);
    throw error;
  }
};

export const getStatistics = async () => {
  try {
    const response = await api.get('/statistics/');
    return response.data;
  } catch (error) {
    console.error('Error fetching statistics:', error);
    throw error;
  }
};

export default api;
