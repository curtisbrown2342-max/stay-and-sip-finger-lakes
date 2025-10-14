# Stay & Sip Finger Lakes (Streamlit)

A simple, free-to-host local travel hub for the Finger Lakes (Keuka, Seneca, Cayuga). Show stays, wineries/distilleries, attractions, and wedding venues with filterable cards, a map, and itinerary ideas. Uses JSON files you can edit easily.

## Quickstart
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the URL (usually http://localhost:8501).

## Where to edit data
- `data/stays.json`
- `data/wineries.json`
- `data/attractions.json`
- `data/wedding_venues.json`
- `data/itineraries.json`

Each listing has a `link` field — replace with affiliate or partner URLs.

## Deploy free
- **Streamlit Community Cloud**: push to GitHub → “New app” → select repo
- **Hugging Face Spaces (Streamlit)**: create a Space and upload files

## Notes
- Add an affiliate disclosure to the footer if you use paid links.
- All photos are placeholders (Unsplash). Replace with your own images to stand out.