import { useRef, useState } from 'react';
import { uploadDocument } from '../api/client.js';

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function UploadDocument({ onUploaded }) {
  const input = useRef(null);
  const busy = useRef(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  function selectFile(files) {
    if (busy.current) return;
    setSuccess('');
    setError('');
    setFile(null);
    if (files.length !== 1) {
      setError('Please select one file at a time.');
    } else if (files[0].size === 0) {
      setError('Empty files cannot be uploaded.');
    } else if (files[0].size > MAX_FILE_SIZE) {
      setError('This file exceeds the 10 MB limit.');
    } else {
      setFile(files[0]);
    }
    // React state owns the selection; allow selecting the same file again.
    if (input.current) input.current.value = '';
  }

  async function submit(event) {
    event.preventDefault();
    if (!file || busy.current) return;
    busy.current = true;
    setUploading(true);
    setError('');
    setSuccess('');
    try {
      const document = await uploadDocument(file);
      setFile(null);
      setSuccess(`Uploaded “${document.original_filename}”.`);
      await onUploaded(document);
    } catch (error) {
      setError(error.message || 'Unable to upload the document.');
    } finally {
      busy.current = false;
      setUploading(false);
    }
  }

  return (
    <section className="panel" aria-labelledby="upload-title">
      <h2 id="upload-title">Upload Document</h2>
      <form onSubmit={submit}>
        <div
          className={`upload-area${dragging ? ' dragging' : ''}`}
          onDragOver={(event) => {
            event.preventDefault();
            if (!uploading) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            selectFile(event.dataTransfer.files);
          }}
        >
          <label htmlFor="document-file">Choose a document or drop it here</label>
          <p id="upload-description" className="muted">One file at a time. Maximum file size: 10 MB (10 MiB).</p>
          <input ref={input} id="document-file" type="file" disabled={uploading}
            aria-describedby="upload-description selected-file"
            onChange={(event) => {
              if (event.target.files.length) selectFile(event.target.files);
            }} />
          <p id="selected-file" className="selected-file">{file ? file.name : 'No file selected.'}</p>
          <button className="primary" type="submit" disabled={!file || uploading}>
            {uploading ? 'Uploading…' : 'Upload document'}
          </button>
        </div>
        <div aria-live="polite">{success && <p className="success">{success}</p>}</div>
        {error && <p role="alert" className="error">{error}</p>}
      </form>
    </section>
  );
}
