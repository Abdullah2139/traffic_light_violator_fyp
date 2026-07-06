from pathlib import Path

readme = r"""# AI-Powered Traffic Light Violation Detection System

<p align="center">
  <strong>Computer-vision traffic monitoring with vehicle detection, red-light violation identification, number-plate OCR, a Django dashboard, SQLite storage, and PDF reporting.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Django-6.0-darkgreen?logo=django" alt="Django">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-red?logo=opencv" alt="OpenCV">
  <img src="https://img.shields.io/badge/Ultralytics-YOLO-purple" alt="Ultralytics YOLO">
  <img src="https://img.shields.io/badge/Database-SQLite-lightblue?logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/Status-Academic%20Prototype-orange" alt="Academic Prototype">
</p>

---

## Table of Contents

- [Overview](#overview)
- [Main Features](#main-features)
- [System Workflow](#system-workflow)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Database Model](#database-model)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Video Input Options](#video-input-options)
- [Web Routes](#web-routes)
- [Detection Logic](#detection-logic)
- [Important Configuration](#important-configuration)
- [Troubleshooting](#troubleshooting)
- [Current Limitations](#current-limitations)
- [Security and Production Notes](#security-and-production-notes)
- [Future Improvements](#future-improvements)
- [Project Team](#project-team)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Overview

This repository contains an academic **Smart Traffic Violation Detection System** that processes traffic video and identifies vehicles crossing a defined violation zone while the traffic signal is red.

The system combines:

- **Ultralytics YOLO** for vehicle detection
- **OpenCV** for video processing and traffic-light colour analysis
- **EasyOCR** for number-plate text extraction
- **Django** for the web dashboard and application logic
- **SQLite** for violation record storage
- **xhtml2pdf** for downloadable traffic violation reports

When a violation is detected, the application attempts to read the number plate, records the vehicle type, assigns a fine, stores the event in the database, and displays it on a dashboard.

> **Project status:** This is an academic prototype. It is suitable for demonstrations, experimentation, and further research, but it is not yet ready for real-world traffic enforcement.

---

## Main Features

### AI and Computer Vision

- Detects common road vehicles from video frames
- Processes cars, motorcycles, buses, and trucks
- Detects red, yellow, and green traffic-light states
- Uses configurable stop-line and violation-zone coordinates
- Marks vehicles as:
  - `NORMAL`
  - `APPROACHING`
  - `OK`
  - `VIOLATION`
- Displays live bounding boxes and signal status
- Supports recorded videos, custom video files, and a network camera stream

### Number-Plate Processing

- Crops the lower portion of a detected vehicle
- Runs OCR using EasyOCR
- Removes non-alphanumeric characters from detected text
- Falls back to `UNKNOWN` when OCR confidence or text quality is insufficient

### Violation Management

- Saves violations through the Django ORM
- Stores:
  - Number plate
  - Vehicle type
  - Detection timestamp
  - Fine amount
  - Optional image-evidence path
- Uses a default fine amount of **Rs. 500**
- Avoids inserting an identical plate and vehicle-type combination more than once

### Web Dashboard

- Displays the total number of violations
- Displays the total value of recorded fines
- Shows recent violations in descending time order
- Refreshes automatically every three seconds
- Provides vehicle, plate, timestamp, and fine information
- Includes a downloadable PDF report

---

## System Workflow

1. A video source is opened using OpenCV.
2. Each frame is resized to `1280 × 720`.
3. A fixed region of interest is analysed to determine the signal colour.
4. YOLO detects supported vehicle classes.
5. The bottom-centre point of every vehicle is calculated.
6. The point is compared with the configured stop line and violation zone.
7. A violation is recorded only when:
   - The vehicle has crossed the violation-zone line, and
   - The detected signal colour is red.
8. The lower portion of the vehicle is sent to EasyOCR.
9. The plate number, vehicle type, timestamp, and fine are stored in SQLite.
10. The Django dashboard reads and displays the stored records.
11. Users can export a PDF report from the dashboard.

---

## Architecture

```mermaid
flowchart LR
    A[Recorded Video / Custom Video / Phone Camera] --> B[OpenCV Frame Capture]
    B --> C[Traffic-Light ROI Analysis]
    B --> D[YOLO Vehicle Detection]
    C --> E[Signal State: Red / Yellow / Green]
    D --> F[Vehicle Bounding Box and Position]
    E --> G{Violation Rule}
    F --> G
    G -->|Red light + crossed zone| H[Crop Plate Region]
    H --> I[EasyOCR]
    I --> J[Clean Plate Text]
    J --> K[Django ORM]
    K --> L[(SQLite Database)]
    L --> M[Django Dashboard]
    L --> N[PDF Report]
