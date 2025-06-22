# DesktopApp

This is a desktop application project.

## Features

- Connects to a database using environment variables for security
- Modular and easy-to-read code structure
- Designed for easy deployment and configuration

## Getting Started

1. **Clone the repository:**
   ```
   git clone https://github.com/Karanci/DesktopApp.git
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Create a `.env` file in the `server` directory with your database credentials:
     ```
     DB_HOST=your_host
     DB_USER=your_user
     DB_PASSWORD=your_password
     DB_NAME=your_db
     DB_PORT=3306
     ```

4. **Run the application:**
   ```
   python main.py
   ```

## Security

- **Never share your `.env` file or sensitive credentials.**
- The `.gitignore` file is configured to prevent sensitive files from being uploaded to GitHub.

## License

This project is licensed under the MIT License.
