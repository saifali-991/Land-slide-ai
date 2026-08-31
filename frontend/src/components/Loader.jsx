export default function Loader({ label = 'Loading…' }) {
  return (
    <div className="loading-block">
      <span className="loader" /> {label}
    </div>
  )
}
