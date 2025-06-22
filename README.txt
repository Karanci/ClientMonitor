# DesktopApp

This project consists of a server and client architecture for monitoring purposes.

## Structure

- **server/dist/app.exe**  
  The main server application. Should be run on the server machine.

- **client/monitoring_service.py** or **client/dist/client_hearthbeat.exe**  
  The client monitoring service. Should be run on each client PC.

## How to Use

### 1. Server Side

- On the server machine, run the following executable:
  ```
  server/dist/app.exe
  ```

### 2. Client Side

- On each client PC, you can either:
  - Run the Python script:
    ```
    python client/monitoring_service.py
    ```
  - Or run the compiled executable:
    ```
    client/dist/client_hearthbeat.exe
    ```

## Configuration

- Make sure to set up your environment variables for database credentials in a `.env` file (do not share this file).
- The `.gitignore` file is configured to prevent sensitive files from being uploaded to GitHub.

## License

This project is licensed under the MIT License.
