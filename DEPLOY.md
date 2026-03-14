# Deploy CampusMate

## Vercel does **not** run Streamlit

Vercel is for **static sites** and **serverless functions**. Streamlit needs a **long-running Python server**, so **you cannot run this app directly on Vercel**.

Use **Streamlit Community Cloud** (free) to host the app, and optionally use Vercel only for a **landing page** that links to it.

---

## Option 1: Streamlit Community Cloud (recommended – free)

This is the official way to host Streamlit apps.

### 1. Push your code to GitHub

```bash
cd "c:\Users\HARSHAL\Downloads\FYP-1"
git init
git add .
git commit -m "CampusMate app"
# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/FYP-1.git
git push -u origin main
```

### 2. Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io**
2. Sign in with GitHub.
3. Click **"New app"**.
4. **Repository:** `YOUR_USERNAME/FYP-1`
5. **Branch:** `main`
6. **Main file path:** `frontend/app.py`
7. **App URL:** (optional) e.g. `campusmate-fyp`
8. Click **"Deploy"**.

The app will be built and available at `https://YOUR_APP_NAME.streamlit.app`.

### 3. Requirements

- `requirements.txt` is at the **repo root** (already there).
- Main file is `frontend/app.py`; the backend is loaded from the repo root.

---

## Option 2: Vercel – landing page only

You can deploy a **static landing page** on Vercel that links to your Streamlit app:

1. Deploy the app on **Streamlit Community Cloud** (Option 1) and copy your app URL.
2. In the project root, open `vercel-landing/index.html` and replace `YOUR_STREAMLIT_APP_URL` with your URL (e.g. `https://campusmate-fyp.streamlit.app`).
3. Deploy the `vercel-landing` folder to Vercel:
   - Either connect the repo to Vercel and set **Root Directory** to `vercel-landing`,  
   - Or run `cd vercel-landing && vercel` and follow the prompts.

Then your Vercel site will show a simple page with a button that opens the CampusMate app on Streamlit Cloud.

---

## Summary

| Goal                         | Use                          |
|-----------------------------|------------------------------|
| Run the CampusMate app      | **Streamlit Community Cloud** |
| Have a custom domain / page | **Vercel** for landing + link |
