# Bloom

Bloom is a Django mental wellness app with mood tracking, journaling, wellness insights, an AI chatbot, and therapist booking.

## Stack

- Django 5
- PostgreSQL
- Django templates
- OpenAI SDK
- Pillow

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables in [`.env`](./.env).
4. Run migrations:

```powershell
python manage.py migrate
```

5. Start the server:

```powershell
python manage.py runserver
```

## Database

The project is configured to use PostgreSQL through `DATABASE_URL`.

Example:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/Bloom
```

## Inspect data

You can inspect PostgreSQL-backed data in two ways.

Using Django shell:

```powershell
python manage.py shell
```

Example:

```python
from django.contrib.auth.models import User
from therapists.models import TherapistProfile
print(User.objects.count())
print(TherapistProfile.objects.count())
```

Using Django admin:

```powershell
python manage.py createsuperuser
python manage.py runserver
```

Then open `http://127.0.0.1:8000/admin/`.
