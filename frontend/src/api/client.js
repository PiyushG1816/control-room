import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getRuns() {
  try {
    const response = await api.get('/runs');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch runs:', error);
    throw error;
  }
}

export async function getRun(id) {
  try {
    const response = await api.get(`/runs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch run ${id}:`, error);
    throw error;
  }
}

export async function getCompare(runAId, runBId) {
  try {
    const response = await api.get('/compare', {
      params: { run_a: runAId, run_b: runBId },
    });
    return response.data;
  } catch (error) {
    console.error(
      `Failed to compare runs ${runAId} vs ${runBId}:`,
      error,
    );
    throw error;
  }
}
