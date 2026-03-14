# Vercel landing page for CampusMate

This folder is a **static landing page** you can deploy on Vercel. It does **not** run the Streamlit app (Vercel cannot run Streamlit).

**Steps:**
1. Deploy the real app on **Streamlit Community Cloud** (see root `DEPLOY.md`).
2. Edit `index.html` and replace `YOUR_STREAMLIT_APP_URL` with your Streamlit app URL (e.g. `https://campusmate-xxx.streamlit.app`).
3. Deploy this folder to Vercel:
   - Install Vercel CLI: `npm i -g vercel`
   - From this folder: `vercel`
   - Or connect your GitHub repo in vercel.com and set **Root Directory** to `vercel-landing`.

Your Vercel site will show a simple page with a button that opens the CampusMate app.
