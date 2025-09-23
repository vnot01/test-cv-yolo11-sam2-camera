# Implementasi Maps: Mapbox Search + Picker

Tanggal: 2025-09-23
Status: Siap Diimplementasikan (Admin Dashboard saja)

Referensi: [Mapbox Search Box API Playground](https://docs.mapbox.com/playground/search-box/suggest-retrieve/?mapbox_id=dXJuOm1ieHBvaTo1OGE1YWQ2MC1lOTc1LTRhZDYtYjk2Ni1kOTUzNGU0NjFjOGM&session_token=0c229e42-3d13-4419-8975-d17672081a9a&endpoint=retrieve)

## Tujuan
- Admin mencari lokasi (nama tempat/POI) → peta fokus ke hasil
- Admin klik titik presisi lokasi RVM → tangkap latitude/longitude → simpan ke DB
- Tombol “Buka di Maps” untuk membuka Google/Apple Maps via deeplink

## Komponen yang Dipakai
- Mapbox GL JS (render peta) + Mapbox Tiles/Styles
- Mapbox Search Box API (Suggest + Retrieve) untuk pencarian tempat
- Backend Laravel (RvmController) menyimpan `latitude`, `longitude`

## Setup Kunci & Env
Tambahkan ke `.env` (server admin):
```
MAPBOX_ACCESS_TOKEN=pk.****************
MAPBOX_SEARCH_SESSION_TTL_MINUTES=30
```
Pastikan kunci hanya digunakan di Admin (bukan klien publik).

## UI/UX Rekomendasi
- Input “Search place” (debounce 300–500ms)
- Dropdown suggestion → pilih satu → panggil `/retrieve` → flyTo koordinat
- Marker draggable + event click map → update lat/long hidden fields
- Tombol “Use this location” menyimpan ke DB
- Tombol “Open in Maps” → `https://www.google.com/maps?q=LAT,LNG`

## Alur Teknis (Front-end)
1) Inisialisasi Mapbox GL JS
```html
<link href="https://api.tiles.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet" />
<script src="https://api.tiles.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"></script>
```
```js
mapboxgl.accessToken = '{{ env('MAPBOX_ACCESS_TOKEN') }}';
const map = new mapboxgl.Map({
  container: 'mapbox-admin',
  style: 'mapbox://styles/mapbox/streets-v12',
  center: [110.366, -7.795], // default Yogyakarta (lng, lat)
  zoom: 12
});
let marker = new mapboxgl.Marker({draggable: true}).setLngLat([110.366, -7.795]).addTo(map);
marker.on('dragend', () => {
  const {lng, lat} = marker.getLngLat();
  updateLatLng(lat, lng);
});
map.on('click', (e) => {
  marker.setLngLat(e.lngLat);
  updateLatLng(e.lngLat.lat, e.lngLat.lng);
});
function updateLatLng(lat, lng){
  document.getElementById('latitude').value = lat.toFixed(7);
  document.getElementById('longitude').value = lng.toFixed(7);
}
```

2) Search (Suggest → Retrieve)
- Gunakan session_token unik per sesi ketik untuk hasil lebih baik & billing akurat
```js
let sessionToken = crypto.randomUUID();
async function doSuggest(query){
  const url = `https://api.mapbox.com/search/searchbox/v1/suggest?q=${encodeURIComponent(query)}&language=id&access_token=${mapboxgl.accessToken}&session_token=${sessionToken}`;
  const res = await fetch(url);
  const data = await res.json();
  return data.suggestions || [];
}
async function doRetrieve(mapbox_id){
  const url = `https://api.mapbox.com/search/searchbox/v1/retrieve?mapbox_id=${encodeURIComponent(mapbox_id)}&access_token=${mapboxgl.accessToken}&session_token=${sessionToken}`;
  const res = await fetch(url);
  const data = await res.json();
  return data.features?.[0];
}
// On select suggestion → retrieve → fly
async function onSelectSuggestion(s) {
  const feat = await doRetrieve(s.mapbox_id);
  if(!feat) return;
  const [lng, lat] = feat.geometry.coordinates;
  map.flyTo({center: [lng, lat], zoom: 17});
  marker.setLngLat([lng, lat]);
  updateLatLng(lat, lng);
}
```

3) Simpan ke DB
- Kirim bersama field lain (name/location) via POST ke `/admin/rvm` (atau PUT untuk edit)
- Backend `RvmController@store/update`:
  - Validasi: `latitude` `nullable|numeric|between:-90,90`, `longitude` `nullable|numeric|between:-180,180`
  - Simpan hanya jika ada; tampilkan di detail RVM

4) Deeplink “Open in Maps”
- Google Maps web: `https://www.google.com/maps?q=LAT,LNG`
- iOS Apple Maps: `http://maps.apple.com/?ll=LAT,LNG`
- Android Geo URI: `geo:LAT,LNG?q=LAT,LNG`

## Pembatasan & Catatan
- Mapbox Search memerlukan token & mematuhi TOS; ada usage-based limits (free tier cukup untuk 10 RVM, 100 user admin-light)
- Gunakan debounce untuk menekan request suggest
- Simpan label hasil pilih (opsional) untuk referensi; kebenaran utama tetap lat/long

## Checklist Implementasi
- [ ] Tambah MAPBOX_ACCESS_TOKEN di `.env`
- [ ] Tambah UI map + search di Admin (Edit RVM)
- [ ] Implement Suggest→Retrieve + flyTo
- [ ] Implement click/drag marker → isi lat/long
- [ ] Simpan lat/long via controller
- [ ] Tambah tombol “Open in Maps” (deeplink)

## Testing
- Cari “Universitas Nahdlatul Ulama Yogyakarta” → pilih → flyTo
- Geser pin ke titik persis pemasangan → simpan → lihat di detail RVM

---

## Referensi
- Mapbox Search Box API Playground: https://docs.mapbox.com/playground/search-box/suggest-retrieve/?mapbox_id=dXJuOm1ieHBvaTo1OGE1YWQ2MC1lOTc1LTRhZDYtYjk2Ni1kOTUzNGU0NjFjOGM&session_token=0c229e42-3d13-4419-8975-d17672081a9a&endpoint=retrieve
- Mapbox Search Box API Docs: `https://docs.mapbox.com/api/search/search-box`
