import { useState, useEffect, useRef } from 'react';

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  enabled?: boolean;
  retries?: number;
}

export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = [],
  options: UseApiOptions<T> = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryCountRef = useRef(0);

  const { onSuccess, onError, enabled = true, retries = 3 } = options;

  useEffect(() => {
    if (!enabled) return;

    const fetchData = async () => {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setLoading(true);
      setError(null);

      try {
        const result = await apiCall();
        setData(result);
        onSuccess?.(result);
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        
        if (retryCountRef.current < retries) {
          retryCountRef.current++;
          setTimeout(fetchData, 1000 * retryCountRef.current);
          return;
        }

        setError(err);
        onError?.(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, dependencies);

  return { data, loading, error };
} 