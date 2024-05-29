## Student Performance System

The Student Performance System is a dynamic and comprehensive tool designed to optimize the management and analysis of student academic progress in educational institutions. This innovative system empowers educators, administrators, and students to track, assess, and improve educational outcomes with ease.

Running the flask application.

## Installation

First, you need to clone this repository:

```bash
git clone git@github.com:CodeEx24/student-performance.git
```

Or:

```bash
git clone https://github.com/CodeEx24/student-performance.git
```

Then change into the `student-performance` folder:

```bash
cd student-performance
```

Now, we will need to create a virtual environment and install all the dependencies:

```bash
python3 -m venv venv  # on Windows, use "python -m venv venv" instead
. venv/bin/activate   # on Windows, use "venv\Scripts\activate" instead
pip install -r requirements.txt
```

## After activating you may setup environment variables

```bash
CONFIG_MODE = "development" or "production"
ADD_DATA= True or False (If you want to add a custom data configuration)
DEVELOPMENT_DATABASE_URI="your_development_database"
PRODUCTION_DATABASE_URI="your_production_database"
JWT_SECRET_KEY="your_jwt_secret"
SECRET_KEY="secret_key"
```

### Mail server configuration

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USERNAME="username"
MAIL_PASSWORD="password"
MAIL_DEFAULT_SENDER="your sender email address"
```

### Default env configuration

```bash
STUDENT_API_BASE_URL=/api/v1/student
FACULTY_API_BASE_URL=/api/v1/faculty
UNIVERSITY_ADMIN_API_BASE_URL=/api/v1/university-admin
SYSTEM_ADMIN_API_BASE_URL=/api/v1/system-admin
REGISTRAR_API_BASE_URL=/api/v1/registrar
```

## How to Run a Specific Example Application?

**Before run a specific example application, make sure you have activated the virtual enviroment.**

If you want to run the Hello application, just execute these commands:

```bash
flask run --reload
```

Similarly, you can run HTTP application like this:

```bash
cd http
flask run
```

The applications will always running on http:///127.0.0.1:5000.

## Example Applications Menu

- Student Role (`/student`): For students portal.
- Faculty Role (`/faculty`): For faculty portal.
- Registrar Role (`/registrar`): For registrar portal.
- University Admin Role (`/university-admin`): For university admin portal.
- System Admin Role (`/system-admin`): For system admin portal.

## Contributions

Any contribution is welcome, just fork and submit your PR.

## License

This project is licensed under the MIT License (see the `LICENSE` file for details).
