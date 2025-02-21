# Cerberus - Pentesting Web Application

A simple pentesting web application built with Flask (Python) and JavaScript. It provides scanning functionality, report generation, and basic dashboard statistics.

## Features

- **Dashboard**: Displays stats such as the number of generated reports, available modules, and scanned clients.
- **Scanner**: Runs full scans based on a provided target.
- **Reports**: Lists all generated PDF reports with the option to delete.
- **Settings**: Placeholder for future configuration options.

## Project Structure

- `app.py`: Main Flask application containing routes, scanning logic, and report handling.
- `static/`: Holds CSS, JS, and image assets.
- `templates/`: HTML templates for rendering pages.
- `modules/`: Python modules used for scanning and report generation.
- `informes/`: Stores generated PDF reports.
- `logs/`: Contains log data for scanned targets.

## Installation

1. Clone this repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure the necessary folders (`modules`, `informes`, `logs`, `static`, `templates`) are present.

## Usage

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```
3. Use the dashboard to view stats and perform scans.

## Endpoints Overview

- **GET /**: Renders the main page.
- **GET /api/stats**: Returns JSON with reports, modules, and clients stats.
- **POST /fullscan**: Initiates a full scan process.
- **POST /stopscan**: Attempts to stop the current scanning process.
- **GET /api/reports**: Retrieves a list of available PDF reports.
- **DELETE /api/reports/<filename>**: Deletes a specific report.

<br/>

<p align="center">
  <img src="static/img/cerberus_logo.png" alt="cerberus_logo" width="100" height="100">
</p>