# Khoj - a missing-persons registry for disaster response

A centralised registry matching missing-person reports filed by families
against unidentified-remains records filed by hospitals, morgues and police
posts, with a trained verifier deciding every match.

It is seeded with the August 2026 Bhotekoshi flood in Nepal as its worked
example, where families travelled between hospitals, morgues, police stations
and army camps across six districts because no single registry existed. That
disaster is one `Event` row; running the system for an earthquake elsewhere is
another row, not another codebase.

**This is a learning and portfolio project. It runs on seeded, fictional data.
It is not an official registry and is not deployed as a public service.**

## Stack

- Django 6.1, PostgreSQL 18
- Hand-built CSS token system (no framework)
- Custom user model from the first migration
- English / Nepali via Django i18n

## Setup (Windows / PowerShell)

```
cd D:\Djangoprojects\project#2
python -m venv venv
venv\Scripts\activate
pip install --no-cache-dir -r requirements.txt
copy .env.example .env      # then fill in DJANGO_SECRET_KEY and DB_PASSWORD
python manage.py migrate
python manage.py seed_event
python manage.py createsuperuser
python manage.py runserver
```

`seed_event` loads the Bhotekoshi flood, its four districts and the facilities
connected to them.

## Apps

- `accounts` - custom `User` with a `role` field (family / responder / verifier / admin)
- `registry` - events and regions, missing-person reports, unidentified records,
  and the matches between them
