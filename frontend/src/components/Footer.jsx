export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div>
          <strong>NER Landslide AI</strong> — prototype decision-support tool for the
          8 North Eastern states of India (Assam, Arunachal Pradesh, Manipur, Meghalaya,
          Mizoram, Nagaland, Sikkim, Tripura).
        </div>
        <div>
          Data sources: Open-Meteo (weather &amp; terrain) · OpenStreetMap (maps).
          Risk scores are <strong>not</strong> scientifically validated predictions —
          always follow official disaster-management (NDMA/SDMA) and local authority advisories.
        </div>
        <div>⚠️ In an emergency, contact your State Disaster Management Authority / local administration.</div>
      </div>
    </footer>
  )
}
