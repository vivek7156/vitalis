import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { validateProfile } from "./validation";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const fields = [
  ["Gender", "Gender", "select", ["Female", "Male"]],
  ["Age", "Age (years)", "number", null],
  ["family_history_with_overweight", "Family history of overweight", "select", ["yes", "no"]],
  ["FAVC", "Frequent high-calorie food", "select", ["yes", "no"]],
  ["FCVC", "Vegetable consumption (1–3)", "number", null],
  ["NCP", "Main meals per day (1–4)", "number", null],
  ["CAEC", "Food between meals", "select", ["no", "Sometimes", "Frequently", "Always"]],
  ["SMOKE", "Smokes tobacco", "select", ["yes", "no"]],
  ["CH2O", "Daily water intake (1–3 L)", "number", null],
  ["SCC", "Monitors calorie consumption", "select", ["yes", "no"]],
  ["FAF", "Physical activity (days/week)", "number", null],
  ["TUE", "Technology use (hours/day)", "number", null],
  ["CALC", "Alcohol consumption", "select", ["no", "Sometimes", "Frequently", "Always"]],
  ["MTRANS", "Primary transportation", "select", ["Automobile", "Bike", "Motorbike", "Public_Transportation", "Walking"]],
];

const initialForm = Object.fromEntries(fields.map(([name]) => [name, ""]));

function Consent({ onAccept }) {
  return (
    <section className="card consent" aria-labelledby="consent-title">
      <span className="eyebrow">WELCOME TO VITALIS</span>
      <h2 id="consent-title">A clearer starting point for your wellness questions.</h2>
      <p>
        Vitalis provides research-oriented screening support. It is not a diagnosis,
        treatment recommendation, or emergency service.
      </p>
      <ul className="notice-list">
        <li>Your answers are used to demonstrate the selected screening model.</li>
        <li>Do not enter names, contact details, or other direct identifiers.</li>
        <li>For urgent symptoms, contact local emergency services or a clinician.</li>
      </ul>
      <button className="primary-button" onClick={onAccept}>I understand and continue</button>
    </section>
  );
}

function Field({ name, label, type, options, value, onChange, error }) {
  return (
    <label className="field">
      <span>{label}</span>
      {type === "select" ? (
        <select name={name} value={value} onChange={onChange} aria-invalid={Boolean(error)}>
          <option value="">Select an option</option>
          {options.map((option) => <option key={option} value={option}>{option.replaceAll("_", " ")}</option>)}
        </select>
      ) : (
        <input
          name={name}
          type="number"
          value={value}
          onChange={onChange}
          min={name === "Age" ? 14 : undefined}
          max={name === "Age" ? 120 : undefined}
          step="any"
          aria-invalid={Boolean(error)}
        />
      )}
      {error && <small className="field-error">{error}</small>}
    </label>
  );
}

function ScreeningForm({ onResult }) {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("idle");
  const [errorMessage, setErrorMessage] = useState("");

  function update(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
    setErrors({ ...errors, [event.target.name]: "" });
  }

  function validate() {
    const nextErrors = validateProfile(form, fields);
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function submit(event) {
    event.preventDefault();
    if (!validate()) return;
    setStatus("loading");
    setErrorMessage("");
    const payload = { ...form, Age: Number(form.Age) };
    ["FCVC", "NCP", "CH2O", "FAF", "TUE"].forEach((key) => { payload[key] = Number(payload[key]); });
    try {
      const response = await fetch(`${API_URL}/api/v1/screen/obesity`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || data.detail || "The screening request could not be completed.");
      setStatus("idle");
      onResult(data);
    } catch (error) {
      setStatus("error");
      setErrorMessage(error.message);
    }
  }

  return (
    <form className="card form-card" onSubmit={submit} noValidate>
      <div className="section-heading">
        <div><span className="eyebrow">OBESITY SCREENING</span><h2>Lifestyle profile</h2></div>
        <span className="status-pill">E2 · lifestyle-only</span>
      </div>
      <p className="muted">Required fields are used to check whether the obesity specialist is ready to run.</p>
      <div className="form-grid">
        {fields.map(([name, label, type, options]) => (
          <Field key={name} name={name} label={label} type={type} options={options}
            value={form[name]} onChange={update} error={errors[name]} />
        ))}
      </div>
      {errorMessage && <div className="alert error" role="alert">{errorMessage}</div>}
      <button className="primary-button" disabled={status === "loading"}>
        {status === "loading" ? "Checking readiness…" : "Run screening check"}
      </button>
      <p className="form-footnote">Height and weight are intentionally not collected in this primary E2 model.</p>
    </form>
  );
}

function Result({ result }) {
  if (!result) return null;
  const isPending = result.model_readiness !== "AVAILABLE";
  return (
    <section className="card result-card" aria-live="polite">
      <div className="section-heading">
        <div><span className="eyebrow">SCREENING STATUS</span><h2>{isPending ? "Ready for the next module" : "Your screening result"}</h2></div>
        <span className={`status-pill ${isPending ? "pending" : "ready"}`}>{result.model_readiness}</span>
      </div>
      {result.prediction && <div className="prediction"><span>Model output</span><strong>{result.prediction}</strong><span>{Math.round(result.probability * 100)}% model confidence</span></div>}
      <p>{result.message}</p>
      {result.advisory_notes?.map((note) => <div className="alert notice" key={note}>{note}</div>)}
      {isPending && <p className="muted">No health estimate was invented. The API has validated and transformed your input, but only a trained and calibrated artifact may provide an estimate.</p>}
      <p className="disclaimer">Screening support only; not a diagnosis. Discuss health concerns with a qualified professional.</p>
    </section>
  );
}

function WellnessPanel() {
  return (
    <section className="card wellness">
      <div className="section-heading"><div><span className="eyebrow">SEPARATE WELLNESS VIEW</span><h2>Daily signals</h2></div><span className="status-pill pending">DEMO ONLY</span></div>
      <p className="muted">Wearable data is intentionally separate from disease screening and does not change model predictions.</p>
      <div className="wellness-grid">
        <div><strong>—</strong><span>Steps</span></div><div><strong>—</strong><span>Sleep</span></div><div><strong>—</strong><span>Heart rate</span></div>
      </div>
      <p className="form-footnote">No wearable source is connected. Values remain unavailable rather than fabricated.</p>
    </section>
  );
}

function App() {
  const [consented, setConsented] = useState(false);
  const [result, setResult] = useState(null);
  return (
    <main>
      <header className="topbar"><a className="brand" href="/">vitalis<span>.</span></a><span className="topbar-note">Research prototype · non-diagnostic</span></header>
      <div className="shell">
        <section className="hero"><span className="eyebrow">PERSONAL HEALTH, MADE CLEARER</span><h1>Understand your screening pathway.</h1><p>Answer a few lifestyle questions and see whether the validated Vitalis specialist is ready to help.</p></section>
        {!consented ? <Consent onAccept={() => setConsented(true)} /> : <><ScreeningForm onResult={setResult} /><Result result={result} /><WellnessPanel /></>}
      </div>
      <footer>Vitalis · Built for research and screening support · No direct identifiers required</footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
