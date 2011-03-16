from pyrfc3339 import generate

def process_report_atom(reports):
    out = []
    for report in reports:
        report['authors'] = set([narrative['name'] for narrative in report['narrative']])
        report['atom_ts'] = generate(report['timestamp'], accept_naive=True)
        out.append(report)
    return out
