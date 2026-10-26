# Sustainable Recycling of EV Batteries

Streamlit facility app for material recovery, process performance, operational electricity emissions, operating costs, and improvement planning.

## Run locally
1. Install Python (3.11 or 3.12 recommended).
2. Open this folder in a terminal.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python -m streamlit run app.py`.

## Important notes
- The original Demo scenario and Facility data modes are retained.
- Demo values are illustrative, not facility measurements or industry benchmarks.
- The current carbon boundary includes purchased electricity adjusted for renewable share and optional separately measured process emissions. It excludes diesel/LPG, transport and broader lifecycle emissions. Do not use it as a complete GHG inventory.
- The improvement planner dynamically surfaces actions based on the entered energy intensity, stage efficiencies, mass-balance gap and residue share. Quantified savings are screening estimates only; verify using plant measurements, process trials and supplier quotations.
- Process stage efficiencies are entered values and should be replaced with measured stage input/output data where available.
