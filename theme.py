# Original uploaded dashboard styling, retained verbatim.
CSS='''
<style>
:root {
  --bg: #f5f1ee;
  --panel: #ffffff;
  --panel-soft: #faf7f4;
  --ink: #2e2724;
  --muted: #685d57;
  --line: #e7dfd9;
  --brand: #6c4d3d;
  --brand-soft: #f0e6df;
  --brand-strong: #3d2c26;
  --green: #2e7d5a;
  --amber: #b77d28;
  --red: #b94d41;
  --shadow: 0 10px 22px rgba(57, 39, 30, 0.05);
}

.stApp {
  background: linear-gradient(180deg, #f5f1ee 0%, #f8f4f2 100%);
  color: var(--ink);
  --text-color: var(--ink);
  --background-color: var(--bg);
  --secondary-background-color: var(--panel);
  --primary-color: var(--brand);
  color-scheme: light;
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #3f302b 0%, #2e2724 100%);
  min-width: 240px;
  max-width: 240px;
  border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] * { color: #f9f3ef; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 1.1rem 1rem; }
[data-testid="stSidebar"] button {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 10px !important;
  text-align: left;
  margin-bottom: 0.35rem;
  transition: all .15s ease;
}
[data-testid="stSidebar"] button:hover { background: rgba(255,255,255,0.08); }
[data-testid="stSidebar"] button[kind="primary"] {
  background: var(--brand-soft) !important;
  color: var(--brand-strong) !important;
  border-color: transparent !important;
}

.block-container {
  padding: 0.8rem 1.3rem 0.9rem;
  max-width: 1800px;
}
[data-testid="stVerticalBlock"] { gap: 0.45rem; }
[data-testid="stHorizontalBlock"] { gap: 0.75rem; }
[data-testid="stForm"] { padding: 0.6rem; border-radius: 12px; }
[data-testid="stMetric"] {
  background: var(--panel) !important;
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 10px 12px;
}
[data-testid="stMetricValue"] { font-size: 1.55rem; }
[data-testid="stMetricLabel"] { font-size: .76rem; color: var(--muted) !important; }

h1 {
  font-size: 2rem !important;
  letter-spacing: -0.7px;
  margin: 0.1rem 0 0.2rem !important;
}
h2 {
  font-size: 1.25rem !important;
  margin: 0.15rem 0 0.2rem !important;
}
h3 {
  font-size: 1.02rem !important;
  margin: 0.12rem 0 0.18rem !important;
}

.eyebrow {
  color: var(--brand);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2.2px;
  margin-bottom: 0.08rem;
  text-transform: uppercase;
}
.subtle { color: var(--muted); font-size: 12px; }
.kicker {
  display: inline-block;
  font-size: 10px;
  letter-spacing: 1.6px;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
  margin-bottom: 0.25rem;
}
.action-card,
.stack-card,
.queue-card,
.detail-panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: var(--shadow);
  padding: 0.9rem 1rem;
}
.action-card {
  background: linear-gradient(180deg, #fff 0%, #faf7f4 100%);
}
.stack-card {
  padding: 0.8rem 0.9rem;
}
.queue-card {
  padding: 0.8rem 0.9rem;
  margin-bottom: 0.55rem;
}
.detail-panel { padding: 1rem; }
.priority-list {
  display: grid;
  gap: 0.6rem;
}
.priority-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  background: var(--panel-soft);
  border: 1px solid var(--line);
}
.priority-row strong { font-size: 0.9rem; }
.priority-row small { color: var(--muted); }
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #efe7e2;
  color: var(--brand-strong);
}
.good { background: #e5f1eb; color: var(--green); }
.warn { background: #fdf0d8; color: var(--amber); }
.bad { background: #f8e0de; color: var(--red); }
.muted { background: #ece7e3; color: var(--muted); }

.grid-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
}
.grid-table th {
  text-align: left;
  font-size: 10px;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--muted);
  background: var(--panel-soft);
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
}
.grid-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.small-table td { padding: 6px 8px; }
.rowtext { padding: 0.25rem 0; font-size: 13px; }

button {
  border-radius: 10px !important;
  transition: transform .1s ease, box-shadow .1s ease;
}
button:hover { transform: translateY(-1px); }
[data-testid="stMain"] button {
  background: #fff !important;
  color: var(--ink) !important;
  border: 1px solid #c9b9ae !important;
}
[data-testid="stMain"] button[kind="primary"] {
  background: var(--brand) !important;
  color: #fff !important;
  border-color: var(--brand) !important;
}
[data-testid="stMain"] button:disabled {
  background: #f1ece9 !important;
  color: #766d69 !important;
  opacity: 1 !important;
}

[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMain"] [data-testid="stForm"],
[data-testid="stMain"] [data-testid="stAlert"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: var(--shadow);
}

[data-testid="stMain"] .stAlert {
  background: var(--panel) !important;
  border: 1px solid var(--line) !important;
  color: var(--ink) !important;
}

[data-testid="stMain"] input,
[data-testid="stMain"] textarea,
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="input"] {
  background: #fff !important;
  color: var(--ink) !important;
  border-radius: 9px !important;
}
[data-baseweb="popover"] *, [role="option"] { color: var(--ink) !important; }
[role="option"]:hover, [aria-selected="true"][role="option"] { background: #efe5df !important; }

[data-testid="stSidebar"] .stCaptionContainer, [data-testid="stSidebar"] .stCaptionContainer * { color: #f5eee8 !important; }
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] .subtle,
[data-testid="stMain"] .grid-table th { color: var(--muted) !important; }
[data-testid="stMain"] svg { color: inherit; }
</style>'''
