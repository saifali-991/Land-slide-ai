const WEIGHTS = [
  ['Rainfall', 30],
  ['Slope', 20],
  ['Soil moisture', 15],
  ['Elevation', 10],
  ['Soil / Geology', 10],
  ['Land cover', 5],
  ['Historical landslides', 5],
  ['Drainage', 3],
  ['Road cutting', 2],
]

export default function AboutPage() {
  return (
    <div className="page container">
      <h1>About NER Landslide AI</h1>
      <p className="subtitle">
        AI-based early warning &amp; landslide risk monitoring for the 8 North Eastern states
        of India.
      </p>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2>🎯 What it does</h2>
        <p>
          The platform combines <strong>static susceptibility factors</strong> (slope, elevation,
          soil/geology, land cover, historical landslides, drainage, road cutting) with{' '}
          <strong>live environmental conditions</strong> (rainfall, soil moisture, temperature,
          humidity, wind) into a single 0–100 landslide risk score with a plain-language
          explanation of <em>why</em> the score is what it is.
        </p>
        <div className="wx-row">
          <span>🟢 LOW · 0–24</span>
          <span>🟡 MODERATE · 25–49</span>
          <span>🟠 HIGH · 50–74</span>
          <span>🔴 CRITICAL · 75–100</span>
        </div>
        <p className="muted" style={{ marginTop: 10 }}>
          Thresholds are configurable (NER_THRESHOLD_* environment variables) and must be
          validated against historical event data before being treated as reliable predictions.
        </p>
      </div>

      <div className="grid grid-2" style={{ marginBottom: 16 }}>
        <div className="card">
          <h2>⚖️ How the score is computed (rule engine)</h2>
          <table className="table">
            <thead><tr><th>Factor</th><th>Weight</th></tr></thead>
            <tbody>
              {WEIGHTS.map(([k, v]) => (
                <tr key={k}><td>{k}</td><td>{v}%</td></tr>
              ))}
            </tbody>
          </table>
          <p className="muted">
            Weights are configurable via NER_W_* environment variables and are conceptual
            starting points — <strong>not</strong> scientifically validated values.
          </p>
        </div>
        <div className="card">
          <h2>🤖 Machine learning module</h2>
          <p>
            <code>ml/</code> contains a full training pipeline (dataset → preprocessing →
            training → prediction) with Logistic Regression, Random Forest, Gradient Boosting
            and optional XGBoost, evaluated with accuracy, precision, recall, F1, ROC-AUC and
            confusion matrices (false alarms vs missed events).
          </p>
          <p className="muted">
            The bundled demo model is trained on <strong>synthetic</strong> data — swap in a real
            landslide inventory (e.g. GSI) before drawing operational conclusions. The trained
            model is served at <code>POST /api/risk/predict</code> alongside the rule engine.
          </p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2>👥 Who it is for</h2>
        <ul className="reco-list">
          <li><strong>General public &amp; residents</strong> — check current risk and weather, receive warnings, read safety recommendations.</li>
          <li><strong>Travellers / tourists</strong> — check destinations before planning routes through hilly terrain.</li>
          <li><strong>Government / disaster management authorities</strong> — monitor all 8 states from one dashboard, identify elevated-risk regions as a decision-support aid.</li>
          <li><strong>Researchers / students</strong> — explore historical observations, evaluate and improve the ML model.</li>
        </ul>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2>🛡️ Important safety design</h2>
        <p>
          This is a <strong>risk-monitoring and decision-support prototype</strong>. It does{' '}
          <strong>not</strong> claim that a landslide will definitely happen. A HIGH or CRITICAL
          indicator means <em>“elevated landslide risk detected based on available data”</em>.
          All emergency decisions must defer to official government / disaster-management
          warnings (NDMA, SDMAs, IMD, GSI) and local authorities.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2>🗺️ Data sources</h2>
        <ul className="reco-list">
          <li>Live weather, rainfall accumulation &amp; soil moisture: <a href="https://open-meteo.com" target="_blank" rel="noreferrer">Open-Meteo</a> (no API key required)</li>
          <li>Elevation &amp; terrain slope: Open-Meteo elevation API (Copernicus DEM GLO-90)</li>
          <li>Maps: <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> via Leaflet</li>
          <li>Static susceptibility baselines &amp; known hotspot list: curated prototype data (see docs/DISCLAIMER.md)</li>
        </ul>
      </div>

      <div className="card">
        <h2>🚀 Future development</h2>
        <p className="muted">
          Satellite imagery · full DEM raster analysis · real-time rainfall radar · advanced ML
          models &amp; time-series forecasting · district-level monitoring · susceptibility maps ·
          community reporting · mobile app · government alert integration · offline emergency
          information.
        </p>
      </div>
    </div>
  )
}
