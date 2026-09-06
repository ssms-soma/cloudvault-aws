export default function UploadPlaceholder() {
  return (
    <section className="panel" aria-labelledby="upload-title">
      <h2 id="upload-title">Upload Documents</h2>
      <div className="upload-placeholder">
        <p>Your documents, in one place.</p>
        <p id="upload-description">File uploads will be available in a future phase.</p>
        <button type="button" disabled aria-describedby="upload-description">
          Upload coming soon
        </button>
      </div>
    </section>
  );
}
