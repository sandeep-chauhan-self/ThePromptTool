/**
 * API communication layer for Daily Prompt.
 * Uses Axios with exponential backoff retry logic.
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const MAX_RETRIES = 3;

/**
 * Fetch the next daily prompt from the API.
 * Retries on network errors with exponential backoff.
 * Returns { type: 'success' | 'exhausted' | 'error', data?, error? }
 */
export async function fetchDailyPrompt(retries = 0) {
  try {
    const { data } = await api.get('/api/prompt/daily');
    return { type: 'success', data };
  } catch (error) {
    // All prompts exhausted
    if (error.response?.status === 404) {
      return {
        type: 'exhausted',
        data: error.response.data,
      };
    }

    // Retry on network or server errors
    if (retries < MAX_RETRIES) {
      const delay = 1000 * Math.pow(2, retries);
      await new Promise(r => setTimeout(r, delay));
      return fetchDailyPrompt(retries + 1);
    }

    return {
      type: 'error',
      error: error.response?.data?.message || error.message || 'Something went wrong',
    };
  }
}

/**
 * Fetch prompt statistics.
 */
export async function fetchStats() {
  try {
    const { data } = await api.get('/api/stats');
    return { type: 'success', data };
  } catch (error) {
    return {
      type: 'error',
      error: error.message || 'Failed to fetch stats',
    };
  }
}

/**
 * Submit a custom user prompt.
 */
export async function addCustomPrompt(promptData) {
  try {
    const { data } = await api.post('/api/prompt', promptData);
    return { type: 'success', data };
  } catch (error) {
    return {
      type: 'error',
      error: error.response?.data?.message || error.message || 'Failed to submit prompt',
    };
  }
}
