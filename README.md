# IP Electromigration Solver

A high-performance EDA (Electronic Design Automation) dashboard built with Streamlit for Power Device Macro Electromigration (EM) sign-off.

This tool calculates current density capacities, geometry compliance, and validates local power device interconnects against PDK rule tables.

---

# Project Architecture

The application is structured for scalability and modularity:

## `src/app.py`

Frontend orchestrator.
Manages UI layout, user input, and the data flow between the physics engine and the display panels.

## `src/em_formulas.py`

The physics engine.
Centralizes all EM derating formulas, temperature factors, and parallel current capacity calculations.

## `src/tech_rules.py`

Data access layer.
Ingests and sanitizes PDK specifications from Excel/ODS files, providing a structured API for the rest of the application.

## `src/optimizer.py`

Strategy/Sweep engine.
Contains the search algorithms used to normalize design widths against baseline benchmarks.

---

# Getting Started

## Prerequisites

* Python 3.8+
* Streamlit
* Pandas
* OpenPyXL

---

# Installation

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd power-em-solver
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Add the technology rule file

Place your `pdk_rules.xlsx` file inside the `/data` folder.

---

# Running the Application

Launch the dashboard locally:

```bash
streamlit run src/app.py
```

---

# Data Structure

The tool expects a specific schema within your `pdk_rules.xlsx` file.

Ensure your sheets are delimited by the following keywords:

* `METAL_TABLE_START / METAL_TABLE_END`
* `VIA_TABLE_START / VIA_TABLE_END`
* `TEMP_TABLE_START / TEMP_TABLE_END`
* `GEOMETRY_TABLE_START / GEOMETRY_TABLE_END`

