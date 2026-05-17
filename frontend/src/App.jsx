import React, { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import axios from 'axios';

const API = 'http://localhost:8000';

// ── Inline SVG Icons ──────────────────────────────────────────
function UserIcon() {
  return <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>;
}
function MailIcon() {
  return <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" /></svg>;
}
function BuildingIcon() {
  return <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><rect x="4" y="2" width="16" height="20" rx="2" /><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01" /></svg>;
}
function GlobeIcon() {
  return <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" /><path d="M2 12h20" /></svg>;
}
function SendIcon() {
  return <svg width="17" height="17" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>;
}
function CheckIcon() {
  return <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" /></svg>;
}
function DownloadIcon() {
  return <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>;
}

// ── PDF Viewer Component ──────────────────────────────────────
function PdfViewer({ pdfUrl, companyName }) {
  return (
    <div className="pdf-section animate-fade-in">
      <div className="pdf-header">
        <CheckIcon />
        <div>
          <p className="pdf-title">Report Ready!</p>
          <p className="pdf-subtitle">Audit report for <strong>{companyName}</strong> · Also sent to your email</p>
        </div>
      </div>
      <div className="pdf-embed-wrapper">
        <iframe
          src={pdfUrl}
          className="pdf-embed"
          title="Audit Report"
        />
      </div>
      <a href={pdfUrl} download className="download-btn">
        <DownloadIcon />
        Download PDF
      </a>
    </div>
  );
}

// ── Processing Banner ─────────────────────────────────────────
function ProcessingBanner() {
  return (
    <div className="alert alert-info animate-fade-in">
      <span className="spinner-blue" />
      <p>Generating your personalized audit report… this usually takes 10–20 seconds.</p>
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────
function App() {
  const { register, handleSubmit, formState: { errors }, reset, getValues } = useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [phase, setPhase] = useState('form'); // 'form' | 'processing' | 'done' | 'error'
  const [pdfUrl, setPdfUrl] = useState(null);
  const [submittedData, setSubmittedData] = useState(null);
  const pollRef = useRef(null);

  // Polling logic
  const startPolling = (email) => {
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await axios.get(`${API}/api/report-status?email=${encodeURIComponent(email)}`);
        if (data.status === 'done' && data.pdfUrl) {
          clearInterval(pollRef.current);
          setPdfUrl(data.pdfUrl);
          setPhase('done');
        } else if (data.status === 'error') {
          clearInterval(pollRef.current);
          setPhase('error');
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 2000); // poll every 2 seconds
  };

  useEffect(() => () => clearInterval(pollRef.current), []); // cleanup on unmount

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      await axios.post(`${API}/api/leads`, data);
      setSubmittedData(data);
      setPhase('processing');
      startPolling(data.email);
      reset();
    } catch (err) {
      console.error(err);
      setPhase('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    clearInterval(pollRef.current);
    setPhase('form');
    setPdfUrl(null);
    setSubmittedData(null);
  };

  return (
    <div className="page">
      <div className={`card ${phase === 'done' ? 'card-wide' : ''}`}>
        <div className="card-body">

          {/* ── Header ── */}
          <div className="form-header">
            <h1 className="form-title">Get Your Free Audit</h1>
            <p className="form-subtitle">
              Discover how AI can transform your business. Submit your details to receive a personalized report instantly.
            </p>
          </div>

          {/* ── Phase: Error ── */}
          {phase === 'error' && (
            <div className="alert alert-error animate-fade-in" style={{ marginBottom: '1.25rem' }}>
              <p>Something went wrong. Please try again.</p>
            </div>
          )}

          {/* ── Phase: Form ── */}
          {(phase === 'form' || phase === 'error') && (
            <form className="form" onSubmit={handleSubmit(onSubmit)}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <div className="input-wrapper">
                  <span className="input-icon"><UserIcon /></span>
                  <input type="text" className={`form-input${errors.name ? ' error' : ''}`} placeholder="John Doe"
                    {...register('name', { required: 'Name is required' })} />
                </div>
                {errors.name && <span className="error-text">{errors.name.message}</span>}
              </div>

              <div className="form-group">
                <label className="form-label">Work Email</label>
                <div className="input-wrapper">
                  <span className="input-icon"><MailIcon /></span>
                  <input type="email" className={`form-input${errors.email ? ' error' : ''}`} placeholder="john@company.com"
                    {...register('email', { required: 'Email is required', pattern: { value: /^\S+@\S+\.\S+$/, message: 'Enter a valid email' } })} />
                </div>
                {errors.email && <span className="error-text">{errors.email.message}</span>}
              </div>

              <div className="form-group">
                <label className="form-label">Company Name</label>
                <div className="input-wrapper">
                  <span className="input-icon"><BuildingIcon /></span>
                  <input type="text" className={`form-input${errors.companyName ? ' error' : ''}`} placeholder="Acme Corp"
                    {...register('companyName', { required: 'Company name is required' })} />
                </div>
                {errors.companyName && <span className="error-text">{errors.companyName.message}</span>}
              </div>

              <div className="form-group">
                <label className="form-label">Company Website</label>
                <div className="input-wrapper">
                  <span className="input-icon"><GlobeIcon /></span>
                  <input type="text" className={`form-input${errors.website ? ' error' : ''}`} placeholder="example.com"
                    {...register('website', { required: 'Website is required' })} />
                </div>
                {errors.website && <span className="error-text">{errors.website.message}</span>}
              </div>

              <button type="submit" className="submit-btn" disabled={isSubmitting}>
                {isSubmitting ? <><span className="spinner" />Submitting...</> : <><SendIcon />Request Free Audit</>}
              </button>
            </form>
          )}

          {/* ── Phase: Processing ── */}
          {phase === 'processing' && <ProcessingBanner />}

          {/* ── Phase: Done — PDF Preview ── */}
          {phase === 'done' && pdfUrl && (
            <>
              <PdfViewer pdfUrl={pdfUrl} companyName={submittedData?.companyName} />
              <button className="new-audit-btn" onClick={handleReset}>← Submit Another Audit</button>
            </>
          )}
        </div>

        <div className="card-footer">
          <p>🔒 Secure, automated process. Powered by SimpliFiQ.</p>
        </div>
      </div>
    </div>
  );
}

export default App;
