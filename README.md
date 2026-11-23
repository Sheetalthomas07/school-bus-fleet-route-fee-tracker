# School Bus Fleet Route & Transport Fee Tracker

A desktop application for school administrators to manage bus routes, bus
stops, student transport allocations, fees, bus passes, and reports.

## Requirements

- Python 3.10 or later
- Tkinter (included with most Windows Python installations)

The application uses only Python's standard library; no `pip` packages are
required.

## Run

From the project directory:

```powershell
python main.py
```

On first launch, the application creates `school_transport.db` in the project
directory and initializes the required tables. The database is local and is
excluded from Git so student, payment, and administrator records are not
published.

## Main features

- Manage routes, buses, drivers, and route start/end points.
- Manage bus stops, distances, and term fees.
- Allocate students to stops with route-capacity checks.
- Record payments and track dues/credits.
- Issue and renew bus passes.
- Review and export transport reports.

Fonts bundled in `assets/fonts` are distributed under the Open Font License;
see `assets/fonts/OFL.txt`.
