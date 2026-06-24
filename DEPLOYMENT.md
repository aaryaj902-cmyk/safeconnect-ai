# Deploying SafeConnect AI to the Internet (GitHub + Render)

This makes your app reachable by anyone, anywhere, via a real public link —
not a `localhost` link. Follow these steps in order.

---

## Part 1 — Push the code to GitHub

### 1.1 Create the repository
1. Go to https://github.com/new
2. Repository name: `safeconnect-ai` (or anything you like)
3. Keep it **Public** (Render's free tier needs this, or a connected private
   repo — public is simplest)
4. Do **not** check "Add a README" — leave it empty
5. Click **Create repository**

### 1.2 Upload your code
On the new repo's page, GitHub shows a button **"uploading an existing
file"** — click it, then drag your whole `safeconnect` folder's *contents*
(not the folder itself — drag `backend`, `frontend`, `render.yaml`, `.gitignore`,
`README.md` etc. all together) into the upload box.

If the drag-and-drop is awkward with many files/folders, it's easier to use
Git from your terminal instead:

```
cd %USERPROFILE%\Downloads\safeconnect_ai_fullstack\safeconnect
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/safeconnect-ai.git
git push -u origin main
```

(Replace `YOUR-USERNAME` with your actual GitHub username. If `git` isn't
installed, download it from https://git-scm.com/download/win first.)

Wait for the upload/push to finish, then refresh the GitHub page — you
should see `backend/`, `frontend/`, `render.yaml`, etc. listed.

---

## Part 2 — Deploy on Render

### 2.1 Create a Render account
Go to https://render.com and sign up — **"Sign up with GitHub"** is fastest,
since it also connects your repos automatically.

### 2.2 Deploy via Blueprint (uses render.yaml automatically)
1. On the Render dashboard, click **New +** → **Blueprint**
2. Connect your `safeconnect-ai` GitHub repo (you may need to click
   "Configure account" to grant Render access to it first)
3. Render will detect `render.yaml` and show you a preview of 3 resources
   it's about to create:
   - `safeconnect-api` (the backend)
   - `safeconnect-frontend` (the website)
   - `safeconnect-db` (the database)
4. Click **Apply**

Render will now build and deploy both services. This takes a few minutes —
the backend install (scikit-learn etc.) is the slowest part.

### 2.3 Find your live URLs
Once both services show a green "Live" status on your Render dashboard:
- Click `safeconnect-frontend` → copy its URL (looks like
  `https://safeconnect-frontend.onrender.com`)
- Click `safeconnect-api` → copy its URL (looks like
  `https://safeconnect-api.onrender.com`)

---

## Part 3 — Connect the frontend to the live backend

The frontend needs to know the backend's real URL (right now it's pointing
at a placeholder).

1. On your computer, open `frontend/js/config.js` in Notepad
2. Find this line:
   ```js
   const PRODUCTION_API_BASE = "https://safeconnect-api.onrender.com";
   ```
3. Replace the URL with your **actual** `safeconnect-api` URL from step 2.3
   (it might already match if Render used the default name — double check)
4. Save the file
5. Push the change back to GitHub:
   ```
   git add frontend/js/config.js
   git commit -m "Set production API URL"
   git push
   ```
6. Render automatically redeploys the frontend within a minute or two
   whenever you push to GitHub.

---

## Part 4 — Share the link

Your real, shareable link is the **frontend** URL from step 2.3, e.g.:

```
https://safeconnect-frontend.onrender.com/index.html
```

Anyone can open this from any device, anywhere — no terminal, no `.bat`
files, no localhost. That's the link you share.

---

## Important notes about the free tier

- **Cold starts**: Render's free web services "sleep" after 15 minutes of
  no traffic. The first request after sleeping takes 30-60 seconds to wake
  up (you'll see a loading delay) — totally normal on the free tier.
- **Database**: the free Postgres database is fine for this project's
  scale, but Render free databases expire after 90 days unless upgraded.
  You'll get an email warning before that happens.
- **Re-deploying**: any time you `git push` new changes, Render redeploys
  automatically — you don't need to repeat the Render dashboard steps again.
- **Costs**: everything above is free-tier. If the app gets real traffic and
  you want it always-on with no cold starts, Render's paid "Starter" plans
  remove the sleep behavior.
