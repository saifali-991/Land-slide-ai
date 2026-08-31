import { useEffect, useRef } from 'react'
import {
  CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap, useMapEvents,
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

function ClickCatcher({ onPick }) {
  useMapEvents({
    click(e) {
      if (onPick) onPick({ lat: e.latlng.lat, lon: e.latlng.lng })
    },
  })
  return null
}

function Recenter({ center }) {
  const map = useMap()
  const lastRef = useRef(null)
  useEffect(() => {
    if (!center) return
    // Only move the map when the target actually changed — avoids resetting
    // the user's pan/zoom on every parent re-render / data refresh.
    const key = `${center.lat},${center.lon},${center.zoom ?? ''}`
    if (lastRef.current === key) return
    lastRef.current = key
    map.setView([center.lat, center.lon], center.zoom ?? map.getZoom())
  }, [center, map])
  return null
}

/**
 * Reusable Leaflet map.
 * markers: [{ key?, lat, lon, label, color, radius?, children? }]
 * onPick:  receives { lat, lon } when the user clicks the map
 */
export default function MapView({ markers = [], center, zoom = 6, height = 420, onPick }) {
  return (
    <div className="map-wrap" style={{ height }}>
      <MapContainer
        center={center ? [center.lat, center.lon] : [26.2, 92.2]}
        zoom={zoom}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {onPick && <ClickCatcher onPick={onPick} />}
        {center && <Recenter center={center} />}
        {markers.map((m) => (
          <CircleMarker
            key={m.key ?? `${m.lat},${m.lon}`}
            center={[m.lat, m.lon]}
            radius={m.radius ?? 10}
            pathOptions={{ color: m.color, fillColor: m.color, fillOpacity: 0.85, weight: 2 }}
          >
            <Tooltip>{m.label}</Tooltip>
            {m.children}
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}
