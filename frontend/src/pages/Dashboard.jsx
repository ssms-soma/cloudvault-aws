import UploadPlaceholder from '../components/UploadPlaceholder.jsx';

export default function Dashboard() {
  return (
    <main className="dashboard">
      <header>
        <p className="eyebrow">LOCAL PROJECT PREVIEW</p>
        <h1>CloudVault</h1>
        <p className="subtitle">Secure Cloud Document Management</p>
      </header>

      <UploadPlaceholder />

      <section className="panel" aria-labelledby="documents-title">
        <h2 id="documents-title">Your Documents</h2>
        <div className="empty-state">
          <p>No documents yet.</p>
          <p>Documents will appear here once storage and uploads are connected.</p>
        </div>
      </section>

      <footer>AWS infrastructure and document storage are planned for the next phase.</footer>
    </main>
  );
}
