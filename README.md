# ambp

A FastAPI-based web application with user authentication and session management.

## Features

- User login/logout
- Session-based authentication
- Home page with user details

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ambp.git
   cd ambp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## Usage

- Visit `http://localhost:8000` in your browser.
- You will be redirected to the login page if not authenticated.
- After login, you will see the home page with your user details.

## Project Structure

- `app/routes/` - FastAPI route handlers
- `app/models.py` - Database models
- `app/schemas.py` - Pydantic models for data validation
- `app/crud.py` - Database CRUD operations
- `app/main.py` - Application entry point

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.