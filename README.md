# Django Kindergarten Management System

![Kindergarten Management System](https://your-url-to-image.png)

This project aims to create a comprehensive management system for kindergartens using Django, facilitating efficient administration and communication among administrators, teachers, and parents.

## Key Features

- **User Authentication and Authorization**: Secure login and role-based access control for administrators, teachers, and parents.
  
- **Children Information Management**: Centralized database for storing and managing Children profiles, including personal details, and emergency contacts.

- **Attendance Tracking**: Automated recording of children attendance.

- **Communication Platform**: Integrated messaging system for announcements, newsletters, and direct communication between teachers and parents.

- **Events and Calendar Management**: Calendar functionality for scheduling and managing events, holidays, and special activities within the kindergarten.

- **Billing and Payments**: Streamlined invoicing and payment management for tuition fees and additional services ('not finished yet').


## Technologies Used

- Django
- PostgreSQL
- HTML
- CSS
- JavaScript

## Getting Started

To get started with the project, follow these steps:

1. Clone this repository.
2. Create a virtual environment and activate it.
3. Install dependencies from `requirements.txt`.
4. Set up your PostgreSQL database and configure settings in `settings.py`.
5. Apply migrations to create database schema.
6. Run the Django development server.

```bash
git clone https://github.com/DawidSzoka1/KindergartenDjangoDev
cd repository
python -m venv venv
source venv/bin/activate (for Windows use venv\Scripts\activate)
pip install -r requirements.txt
# Configure your PostgreSQL database in settings.py
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
