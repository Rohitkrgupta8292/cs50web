# Final Project

## Description
A Django web application with a blog component that supports social authentication via GitHub and Google. This project is designed to provide a platform for users to create, manage, and share blog posts.

## Features
- **Admin Interface**: Manage blog posts, comments, and user accounts through a user-friendly admin panel.
- **Blog Functionality**: Users can create, edit, and delete their blog posts.
- **Rich Text Editing**: Integrated TinyMCE editor for formatting blog content.
- **User Authentication**: Supports social login via GitHub and Google for easy user registration and login.
- **Profile Management**: Users can manage their profiles, including updating their bio and profile pictures.

# Final Project

## Description
A Django web application with a blog component that supports social authentication via GitHub and Google.

## Features
- Admin interface for managing content.
- Blog functionality with rich text editing using TinyMCE.
- User authentication via GitHub and Google.
- User profile management.
- Commenting system for blog posts.
- Like functionality for posts.


## Installation
### Prerequisites
- Python
- Django
- Other dependencies as specified in `requirements.txt`

### Steps to Set Up
1. Clone the repository.
2. Navigate to the project directory.
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage
Access the application at `http://127.0.0.1:8000/`. The admin interface can be accessed at `http://127.0.0.1:8000/admin/`.

## License
This project is licensed under the MIT License.
