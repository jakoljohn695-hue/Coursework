HOUSEBOOK KENYA — TALANTA-STYLE REDESIGN

This package refreshes the frontend to a dark navy + gold premium booking style inspired by the supplied Talanta Stadium reference.
It keeps Flask property listing/search and booking-request flows.

FILES
- app.py: full Flask app + responsive templates and CSS
- requirements.txt: dependencies
- render.yaml: Render Web Service blueprint (free web service; no persistent disk)
- README_DEPLOY.txt: deployment steps

DEPLOY UPDATE
1. Back up your current GitHub repository.
2. Extract this ZIP.
3. Replace the existing app.py and requirements.txt with these files (do not upload the ZIP itself).
4. Commit/push to your same GitHub branch.
5. Render will redeploy automatically if auto-deploy is enabled; otherwise Manual Deploy > Deploy latest commit.
6. Open the Render URL and test /health, property listing, and booking form.

IMPORTANT
- This design package uses SQLite as in your original app. Render free filesystem is ephemeral; data can be lost on deploy/restart.
- Railway PostgreSQL DATABASE_PUBLIC_URL is NOT connected by this app yet. Adding a variable alone does not convert SQLite to PostgreSQL.
- PayHero STK is NOT active in this visual redesign package; payment method is only selected on booking. Do not accept real payments until PostgreSQL + PayHero integration are properly connected and tested.
- There is no host/admin login, verification workflow, CSRF protection, or production booking concurrency lock. This is a visual/demo deployment, not yet ready for real commercial bookings.
- Never put database credentials or PayHero secrets in GitHub.
