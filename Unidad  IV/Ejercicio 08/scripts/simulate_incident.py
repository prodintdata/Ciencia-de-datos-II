from datetime import datetime,timezone
from pathlib import Path
text=f"""# Incident simulation

- detected_at: {datetime.now(timezone.utc).isoformat()}
- signal: recall gap exceeded
- containment: REVIEW and safe baseline
- evidence: preserved report and model version
- communication: REPLACE
- corrective actions, owners and dates: REPLACE
"""
path=Path("reports/lab13/INCIDENT_POSTMORTEM.md"); path.parent.mkdir(parents=True,exist_ok=True)
# A completed postmortem is evidence: never overwrite it with the template.
if path.exists() and "REPLACE" not in path.read_text(encoding="utf-8"): print(f"{path} already completed; not overwritten")
else: path.write_text(text,encoding="utf-8"); print(path)
