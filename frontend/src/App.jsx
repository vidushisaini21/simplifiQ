import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import axios from 'axios';

// Lucide icon approximations using basic SVGs for simplicity & aesthetics
const UserIcon = () => <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const MailIcon = () => <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>;
const BriefcaseIcon = () => <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>;
const GlobeIcon = () => <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>;
const ArrowRightIcon = () => <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>;
const CheckCircleIcon = () => <svg viewBox="0 0 24 24" width="32" height="32" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>;
const DownloadIcon = () => <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState("");

  const [polling, setPolling] = useState(false);
  const [pollEmail, setPollEmail] = useState("");
  const [pdfUrl, setPdfUrl] = useState(null);

  useEffect(() => {
    let intervalId;

    if (polling && pollEmail) {
      intervalId = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/report-status?email=${encodeURIComponent(pollEmail)}`);
          const data = res.data;

          if (data.status === "done" && data.pdfUrl) {
            setPolling(false);
            setPdfUrl(data.pdfUrl);
          } else if (data.status === "error") {
            setPolling(false);
            setErrorText(data.error || "Generation failed.");
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 5000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [polling, pollEmail]);

  const onSubmit = async (data) => {
    setLoading(true);
    setErrorText("");
    setPdfUrl(null);

    try {
      await axios.post(`${API_BASE_URL}/api/leads`, data);
      setPollEmail(data.email);
      setPolling(true);
    } catch (err) {
      console.error(err);
      setErrorText(err.response?.data?.detail || "Failed to start report generation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      {!pdfUrl ? (
        <div className="card animate-fade-in">
          <div className="card-body">
            <div className="form-header">
              <h1 className="form-title">Simpli<span>FiQ</span></h1>
              <p className="form-subtitle">AI-Powered Web Ecosystem Audits</p>
            </div>

            {errorText && (
              <div className="alert alert-error">
                <strong>Generation Error:</strong> {errorText}
              </div>
            )}

            {polling && (
              <div className="alert alert-info">
                <span className="spinner-blue"></span>
                <strong style={{ display: 'block', fontSize: '1.1rem', marginBottom: '4px' }}>Analyzing Digital Presence</strong>
                Scanning tech stack, scraping metadata, and generating AI insights. This usually takes 10-20 seconds...
              </div>
            )}

            {!polling && (
              <form onSubmit={handleSubmit(onSubmit)}>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <div className="input-wrapper">
                    <input
                      className={`form-input ${errors.name ? 'error' : ''}`}
                      placeholder="Jane Doe"
                      {...register("name", { required: true })}
                    />
                    <div className="input-icon"><UserIcon /></div>
                  </div>
                  {errors.name && <span className="error-text">Name is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <div className="input-wrapper">
                    <input
                      type="email"
                      className={`form-input ${errors.email ? 'error' : ''}`}
                      placeholder="jane@company.com"
                      {...register("email", { required: true })}
                    />
                    <div className="input-icon"><MailIcon /></div>
                  </div>
                  {errors.email && <span className="error-text">Email is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Company Name</label>
                  <div className="input-wrapper">
                    <input
                      className={`form-input ${errors.companyName ? 'error' : ''}`}
                      placeholder="Acme Corp"
                      {...register("companyName", { required: true })}
                    />
                    <div className="input-icon"><BriefcaseIcon /></div>
                  </div>
                  {errors.companyName && <span className="error-text">Company name is required</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Company Website</label>
                  <div className="input-wrapper">
                    <input
                      className={`form-input ${errors.website ? 'error' : ''}`}
                      placeholder="https://acme.com"
                      {...register("website", {
                        required: true,
                        pattern: /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/
                      })}
                    />
                    <div className="input-icon"><GlobeIcon /></div>
                  </div>
                  {errors.website && <span className="error-text">Valid URL required</span>}
                </div>

                <button type="submit" disabled={loading} className="submit-btn">
                  {loading ? <span className="spinner"></span> : <>Start Free Audit <ArrowRightIcon /></>}
                </button>
              </form>
            )}
          </div>
          <div className="card-footer">
            Powered by Gemini AI 1.5 Flash • Built for Growth
          </div>
        </div>
      ) : (
        /* Report Result Page */
        <div className="card card-wide animate-fade-in">
          <div className="card-body">
            <div className="pdf-section">
              <div className="pdf-header">
                <div><CheckCircleIcon /></div>
                <div>
                  <div className="pdf-title">Audit Successfully Generated</div>
                  <div className="pdf-subtitle">A copy has been sent to <strong>{pollEmail}</strong> via Resend Email API.</div>
                </div>
              </div>

              <div className="pdf-embed-wrapper">
                <iframe
                  src={`${pdfUrl}#view=FitH`}
                  title="PDF Report"
                  className="pdf-embed"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <a
                  href={pdfUrl}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                  className="download-btn"
                >
                  <DownloadIcon /> Download PDF Report
                </a>

                <button
                  onClick={() => {
                    setPdfUrl(null);
                    setPolling(false);
                    setPollEmail("");
                    setErrorText("");
                    reset();
                  }}
                  className="new-audit-btn"
                >
                  ✦ Make Another Audit
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
