import { useCallback, useEffect, useRef, useState } from 'react';
import UploadDocument from '../components/UploadDocument.jsx';
import { deleteDocument, downloadDocument, getDocuments } from '../api/client.js';
import { formatDate, formatFileSize, formatFileType } from '../utils/format.js';

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [success, setSuccess] = useState('');
  const [pending, setPending] = useState({});
  const activeActions = useRef(new Set());
  const requestVersion = useRef(0);

  const refresh = useCallback(async () => {
    const version = ++requestVersion.current;
    setLoading(true);
    setLoadError('');
    try {
      const result = await getDocuments();
      if (version === requestVersion.current) setDocuments(result);
    } catch {
      if (version === requestVersion.current) {
        setLoadError('Unable to load documents. Make sure the CloudVault API is running, then try again.');
      }
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    return () => { requestVersion.current += 1; };
  }, [refresh]);

  async function act(document, action) {
    if (activeActions.current.has(document.id)) return;
    if (action === 'delete' && !window.confirm(`Delete "${document.original_filename}"?`)) return;
    activeActions.current.add(document.id);
    setPending((current) => ({ ...current, [document.id]: action }));
    setActionError('');
    setSuccess('');
    try {
      if (action === 'delete') {
        await deleteDocument(document.id);
        setDocuments((current) => current.filter((item) => item.id !== document.id));
        setSuccess(`Deleted “${document.original_filename}”.`);
        await refresh();
      } else {
        await downloadDocument(document.id, document.original_filename);
        setSuccess(`Download started for “${document.original_filename}”.`);
      }
    } catch (error) {
      setActionError(error.message || 'The action failed. Please try again.');
    } finally {
      activeActions.current.delete(document.id);
      setPending((current) => {
        const next = { ...current };
        delete next[document.id];
        return next;
      });
    }
  }

  async function uploaded(document) {
    setActionError('');
    setSuccess('');
    setDocuments((current) => [document, ...current.filter((item) => item.id !== document.id)]);
    await refresh();
  }

  return (
    <main className="dashboard">
      <header>
        <h1>CloudVault</h1>
        <p className="subtitle">Secure Cloud Document Management</p>
      </header>
      <UploadDocument onUploaded={uploaded} />
      <section className="panel" aria-labelledby="documents-title">
        <div className="section-heading">
          <h2 id="documents-title">Your Documents</h2>
          <button type="button" onClick={refresh} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
        <div aria-live="polite">{success && <p className="success">{success}</p>}</div>
        {actionError && <p role="alert" className="error">{actionError}</p>}
        {loadError && <p role="alert" className="error">{loadError}</p>}
        {loading && <p role="status" className="muted">Loading documents…</p>}
        {!loading && !loadError && documents.length === 0 && (
          <div className="empty-state">
            <p>No documents uploaded yet.</p>
            <p className="muted">Choose your first document above to get started.</p>
          </div>
        )}
        {documents.length > 0 && (
          <ul className="document-list" aria-label="Documents" aria-busy={loading}>
            {documents.map((document) => (
              <li key={document.id} className="document-row">
                <div className="document-info">
                  <h3>{document.original_filename}</h3>
                  <dl>
                    <div><dt>Type</dt><dd>{formatFileType(document)}</dd></div>
                    <div><dt>Size</dt><dd>{formatFileSize(document.file_size)}</dd></div>
                    <div><dt>Uploaded</dt><dd>{formatDate(document.uploaded_at)}</dd></div>
                  </dl>
                </div>
                <div className="actions">
                  <button type="button" disabled={!!pending[document.id]}
                    aria-label={`Download ${document.original_filename}`}
                    onClick={() => act(document, 'download')}>
                    {pending[document.id] === 'download' ? 'Downloading…' : 'Download'}
                  </button>
                  <button className="danger" type="button" disabled={!!pending[document.id]}
                    aria-label={`Delete ${document.original_filename}`}
                    onClick={() => act(document, 'delete')}>
                    {pending[document.id] === 'delete' ? 'Deleting…' : 'Delete'}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
