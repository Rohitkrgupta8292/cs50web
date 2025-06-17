![Final Project](./static/timber.png)

### [Video Demo](https://www.youtube.com/watch?v=nIerhgwcPNk)

# Socially Integrated Blogging Platform

## Distinctiveness and Complexity

This project, titled **"Development of a Socially Integrated Blogging Platform with User Authentication Using Django"**, is a comprehensive blogging web application that stands apart in both functionality and complexity from prior CS50W projects. Unlike Project 2 (Commerce) or Project 4 (Network), this platform is not an e-commerce system or a clone of a social media site. Instead, it focuses on **blog creation, personalized user profiles, user interaction (likes/comments), media-rich posts**, and **real-time chat**, incorporating both technical depth and front-end sophistication.

What makes this project distinctive is its integration of several complex features into one cohesive application:

- A rich text editor (TinyMCE) for blog content creation, enhancing user input with formatting, media embedding, and editing options.
- Real-time chat using Django Channels and WebSockets (optional enhancement), facilitating seamless interaction between users.
- Profile management with dynamic image uploads (profile pictures and banners), and real-time image resizing using `django-imagekit`.
- Social authentication via Google using OAuth2 for simplified and secure sign-in.
- AJAX-powered like and comment systems with no page reloads.
- Mobile-responsive UI built using **Tailwind CSS** with utility-first styling principles.
- Media handling with optimized image processing for performance and storage efficiency.

In contrast to standard CRUD apps or basic e-commerce platforms, this project blends advanced backend logic, media optimization, real-time features, and frontend interactivity. Each feature required thoughtful architectural decisions, asynchronous processing, and secure user session management, thereby adding to the project’s overall technical complexity and value.

## Project Overview

This platform allows users to register (via Google or email), create blog posts using a rich editor, engage with other posts via comments or likes, and manage their personal profiles with custom images. Users can also engage in real-time conversations, fostering a more interactive experience. The application is responsive and works well on both desktop and mobile devices.

## File Structure

Below is an overview of the main files and directories in the project:

- `final_project/`
  - `final_project/` – Main Django settings directory
    - `settings.py` – Environment-based settings configuration using `django-environ`
    - `urls.py` – URL configuration for the project
    - `wsgi.py/asgi.py` – Interfaces for deployment
  - `blog/` – Core app containing models and views for the blog
    - `models.py` – Models for Post, Profile, Comment, Like
    - `views.py` – Handles post creation, profile management, interaction logic
    - `forms.py` – Django forms for user input
    - `urls.py` – App-specific URL routing
    - `templates/blog/` – HTML templates for blog layout
    - `static/blog/` – JavaScript (AJAX), CSS, and images
  - `accounts/` – Handles user authentication
    - `views.py` – Google OAuth2 login logic and social auth callback
    - `urls.py` – Authentication routes
  - `chat/` – (Optional) Real-time chat system
  - `media/` – Stores uploaded images
- `requirements.txt` – Python package requirements
- `.env` – Contains secret keys and environment settings (excluded from Git)
- `README.md` – This documentation file

## How to Run the Application

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Rohitkrgupta8292/cs50web.git
   cd cs50web/final_project

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

3. **Install all dependencies**:
   ```bash
   pip install -r requirements.txt

4. **Set up required configurations**:
   Open `settings.py` and manually set the following (temporarily hardcoded for development):

   ```python
   GOOGLE_CLIENT_ID = 'your-google-client-id'
   GOOGLE_CLIENT_SECRET = 'your-google-client-secret'
   GOOGLE_CALLBACK_URL = 'http://127.0.0.1:8000/accounts/google/callback/'
   SECRET_KEY = 'your-django-secret-key'
   DEBUG = 
   
5. **Run database migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate

6. **Run the development server**:
   ```bash
   python manage.py 
   
7. **Visit the app in your browser at**:
   ```cpp
   http://127.0.0.1:8000/

## Features

- Full blog post creation/editing with a WYSIWYG editor (TinyMCE)
- Google OAuth login support
- User profile and banner image upload
- AJAX-based like and comment system
- Optional real-time chat module (via Django Channels/WebSockets)
- Tailwind CSS for mobile-responsive design
- Image optimization using django-imagekit
- Clean UI/UX layout with component-based templates

## Additional Notes

- MySQL is used as the primary database, but the app works with SQLite by default if configured.
- Static/media files handled locally; use tools like AWS S3 or Render for production.
- You can extend the app with categories, tags, or post drafts in the future.
- Deployment can be done via Render or any Django-friendly host.

## Requirements

    **Install all Python packages with**:
    ```bash
    pip install -r requirements.txt

### Key packages used:
- Django
- mysqlclient or sqlite 3
- django-timymce
- django-imagekit
- requests (for Google OAuth)
- Pillow
- django-environ (optional, not required currently)
- many more: go to requirements.txt file to see it.

This project represents a unique, feature-rich platform that brings together core web development principles and modern practices. It reflects both backend proficiency and frontend finesse, going well beyond the baseline expectations of a typical CS50W project.