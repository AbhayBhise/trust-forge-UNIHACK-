import requests, csv, io, time

print('Uploading full 1000-row dataset...')
t0 = time.time()

with open('../Unihack_ Sample Dataset - Input.csv', encoding='utf-8') as f:
    csv_data = f.read().encode('utf-8')

r = requests.post('http://127.0.0.1:8000/pipeline/jobs',
    files={'file': ('sample1000.csv', csv_data, 'text/csv')})
print('Submit status:', r.status_code)
job = r.json()
job_id = job.get('job_id')
total  = job.get('total_rows')
print('Job ID:', job_id, '| Total rows:', total)

# Poll until done
while True:
    time.sleep(3)
    status_r = requests.get('http://127.0.0.1:8000/pipeline/jobs/' + job_id)
    s = status_r.json()
    completed = s.get('completed', 0)
    job_status = s.get('status', '')
    verified  = s.get('verified', 0)
    needs_review = s.get('needs_review', 0)
    pct = int(100 * completed / total) if total else 0
    print(f'  [{pct:3d}%] {completed}/{total} | verified={verified} | needs_review={needs_review} | status={job_status}')
    if job_status == 'completed':
        elapsed = time.time() - t0
        print()
        print(f'DONE in {elapsed:.1f}s')
        pct_v = int(100 * verified / total) if total else 0
        print('Verified:    ', verified, '/', total, '(' + str(pct_v) + '%)')
        print('Needs review:', needs_review)
        print('CSV export:  ', s.get('csv_url', ''))
        break
    if job_status == 'failed':
        print('FAILED:', s)
        break
