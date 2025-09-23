# Perencanaan: Leaflet + MapTiler (Tiles) + LocationIQ (Geocoding)

Tanggal: 2025-09-23
Status: Rencana Alternatif (Jika skala data besar / biaya Mapbox dipertimbangkan)

## Tujuan
- Render peta ringan (Leaflet) dengan tiles OSM-derived (MapTiler)
- Pencarian lokasi (LocationIQ – OSM-based)
- Click/drag pin untuk ambil latitude/longitude dan simpan ke DB

## Arsitektur
- UI Peta: Leaflet
- Tiles: MapTiler Streets/Hybrid (opsi Satellite/Hybrid untuk detail)
- Geocoding: LocationIQ Search (forward) + reverse bila dibutuhkan
- Backend: Laravel (RvmController) simpan `latitude`, `longitude`

## Konfigurasi Env
```
MAP_TILER_KEY=***************
LOCATIONIQ_KEY=**************
GEOCODING_PROVIDER=locationiq
```

## Integrasi Front-end (Skema)
1) Leaflet Init
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```
```js
const map = L.map('leaflet-admin').setView([-7.795, 110.366], 12);
L.tileLayer(`https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=${MAP_TILER_KEY}`, {
  attribution: '&copy; OpenStreetMap contributors & MapTiler',
}).addTo(map);
const marker = L.marker([-7.795, 110.366], {draggable: true}).addTo(map);
marker.on('dragend', () => {
  const {lat, lng} = marker.getLatLng();
  updateLatLng(lat, lng);
});
map.on('click', (e) => {
  marker.setLatLng(e.latlng);
  updateLatLng(e.latlng.lat, e.latlng.lng);
});
function updateLatLng(lat, lng){
  document.getElementById('latitude').value = lat.toFixed(7);
  document.getElementById('longitude').value = lng.toFixed(7);
}
```

2) Geocoding (LocationIQ)
```js
async function geoSearch(query){
  const url = `https://us1.locationiq.com/v1/search?key=${LOCATIONIQ_KEY}&q=${encodeURIComponent(query)}&format=json&normalizeaddress=1&accept-language=id`;
  const res = await fetch(url);
  const data = await res.json();
  return data; // array hasil
}
async function onPickResult(item){
  const lat = parseFloat(item.lat), lng = parseFloat(item.lon);
  map.setView([lat, lng], 17);
  marker.setLatLng([lat, lng]);
  updateLatLng(lat, lng);
}
```

## Deeplink “Open in Maps”
- Google Maps: `https://www.google.com/maps?q=LAT,LNG`
- Apple Maps: `http://maps.apple.com/?ll=LAT,LNG`
- Android Geo: `geo:LAT,LNG?q=LAT,LNG`

## Pertimbangan Skala & Biaya
- MapTiler (tiles) & LocationIQ (geocoding) memiliki free tier yang cukup untuk admin
- Jika traffic sangat tinggi: pertimbangkan self-host (OpenMapTiles + Pelias/Nominatim)

## Self-host Roadmap (Opsional)
- Tiles: Bangun OpenMapTiles + TileServer GL
- Geocoding: Pelias/Photon/Nominatim (butuh resource server)
- Pro: kontrol penuh, tanpa vendor limit; Kontra: biaya operasional & pemeliharaan

## Checklist Implementasi
- [ ] Tambah env keys MapTiler & LocationIQ
- [ ] Tambah komponen Leaflet di Admin Edit RVM
- [ ] Implement geocoding search + pilih hasil → set view & pin
- [ ] Implement click/drag pin → isi lat/long
- [ ] Simpan lat/long via controller
- [ ] Tambah deeplink “Open in Maps”
