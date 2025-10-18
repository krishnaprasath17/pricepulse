from run_app import app

print('Registered routes:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ','.join(sorted(rule.methods - {'HEAD','OPTIONS'}))
    print(f"{rule.rule:40} -> endpoint={rule.endpoint:30} methods={methods}")

# Show allowed methods for /api/compare
rule = None
for r in app.url_map.iter_rules():
    if r.rule == '/api/compare':
        rule = r
        break

if rule:
    print('\nFound /api/compare:')
    print('endpoint=', rule.endpoint)
    print('methods=', sorted(rule.methods))
else:
    print('\n/api/compare not found in url_map')
