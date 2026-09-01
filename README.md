# Khoj - disaster missing-persons registry (training project)

A reference design for a centralised missing-persons and unidentified-remains
registry, modelled on the information problems reported after the August 2026
Bhotekoshi / Rasuwa flood in Nepal, where families had to travel between
hospitals, morgues, police stations and army camps across six districts
because no single registry existed.

**This is a learning and portfolio project. It runs on seeded, fictional data.
It is not an official registry and is not deployed as a public service.**

## Stack

- Django 5.1, SQLite (Postgres later, for fuzzy name matching)
- Bootstrap 5 via CDN
- Custom user model from the first migration

## Setup (Windows / PowerShell)

```
cd D:\Djangoprojects\project#2
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Apps

- `accounts` - custom `User` with a `role` field (family / responder / verifier / admin)
- `registry` - missing-person reports, unidentified records, and the matches between them
