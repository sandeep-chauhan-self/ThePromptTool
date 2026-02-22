/**
 * usePrompt — Custom hook encapsulating the prompt lifecycle state machine.
 *
 * States: idle → loading → revealed | exhausted | error
 */

import { useCallback, useEffect, useReducer } from 'react';
import { fetchDailyPrompt, fetchStats } from '../api/promptApi';

const initialState = {
  status: 'idle',     // 'idle' | 'loading' | 'revealed' | 'exhausted' | 'error'
  prompt: null,
  stats: null,
  error: null,
};

function promptReducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, status: 'loading', error: null };
    case 'FETCH_SUCCESS':
      return {
        ...state,
        status: 'revealed',
        prompt: action.payload,
        stats: action.payload.stats,
        error: null,
      };
    case 'FETCH_EXHAUSTED':
      return {
        ...state,
        status: 'exhausted',
        stats: action.payload?.stats || state.stats,
        error: null,
      };
    case 'FETCH_ERROR':
      return {
        ...state,
        status: 'error',
        error: action.payload,
      };
    case 'SET_STATS':
      return { ...state, stats: action.payload };
    case 'RESET':
      return { ...initialState, stats: state.stats };
    default:
      return state;
  }
}

export function usePrompt() {
  const [state, dispatch] = useReducer(promptReducer, initialState);

  // Load initial stats on mount
  useEffect(() => {
    async function loadStats() {
      const result = await fetchStats();
      if (result.type === 'success') {
        dispatch({ type: 'SET_STATS', payload: result.data });
      }
    }
    loadStats();
  }, []);

  const requestPrompt = useCallback(async () => {
    dispatch({ type: 'FETCH_START' });

    const result = await fetchDailyPrompt();

    switch (result.type) {
      case 'success':
        dispatch({ type: 'FETCH_SUCCESS', payload: result.data });
        break;
      case 'exhausted':
        dispatch({ type: 'FETCH_EXHAUSTED', payload: result.data });
        break;
      case 'error':
        dispatch({ type: 'FETCH_ERROR', payload: result.error });
        break;
    }
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return {
    status: state.status,
    prompt: state.prompt,
    stats: state.stats,
    error: state.error,
    requestPrompt,
    reset,
  };
}
