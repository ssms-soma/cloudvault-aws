// Empty in production: Nginx serves the UI and proxies /api on the same origin.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

async function request(path, options, failureMessage) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error('Unable to reach CloudVault. Make sure the CloudVault API is running.');
  }
  if (!response.ok) {
    // Use controlled messages rather than displaying server internals.
    const messages = {
      400: 'The file is invalid or empty. Please choose another file.',
      404: 'This document is no longer available. Refresh the document list.',
      413: 'This file exceeds the 10 MB limit.',
      422: 'Please select a valid file and try again.',
      503: 'The document service is unavailable. Please try again shortly.',
    };
    throw new Error(messages[response.status] || failureMessage);
  }
  return response;
}

export async function getDocuments() {
  const response = await request('/api/documents', {}, 'Unable to load documents. Please try again.');
  return response.json();
}

export async function uploadDocument(file) {
  const body = new FormData();
  body.append('file', file);
  const response = await request('/api/documents', { method: 'POST', body }, 'Unable to upload the document. Please try again.');
  return response.json();
}

export async function downloadDocument(id, originalFilename) {
  const response = await request(`/api/documents/${id}/download`, {}, 'Unable to download the document. Please try again.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = originalFilename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Give the browser time to begin consuming the blob before releasing it.
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function deleteDocument(id) {
  await request(`/api/documents/${id}`, { method: 'DELETE' }, 'Unable to delete the document. Please try again.');
}
