// Reserved for frontend API integration in the next phase.
// No upload or document requests are made by the current dashboard.
export const API_BASE_URL = 'http://localhost:8000';

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }
  return response.json();
}
