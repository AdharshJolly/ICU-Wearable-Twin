import pandas as pd, numpy as np

base = 'dataset/mimic_demo/mimic-iv-clinical-database-demo-2.2'
stays = pd.read_csv(base+'/icu/icustays.csv.gz')
pts = pd.read_csv(base+'/hosp/patients.csv.gz')

merged = stays.merge(pts[['subject_id','dod']], on='subject_id', how='left')
merged['intime'] = pd.to_datetime(merged['intime'])
merged['outtime'] = pd.to_datetime(merged['outtime'])
merged['dod'] = pd.to_datetime(merged['dod'])

# Composite label: died within 30d of discharge OR severe LOS > 5 days
days_to_death = (merged['dod'] - merged['outtime']).dt.days
merged['died_after'] = merged['dod'].notna() & (days_to_death.fillna(999) < 30)
merged['prolonged_los'] = merged['los'] > 5
merged['label'] = (merged['died_after'] | merged['prolonged_los']).astype(int)

print('Total ICU stays:', len(merged))
print('Unique patients:', merged['subject_id'].nunique())
print('Labels - 0 (stable):', (merged['label']==0).sum(), '  1 (deterioration):', (merged['label']==1).sum())
print('Label rate:', round(merged['label'].mean() * 100, 1), '%')
print(merged[['subject_id','stay_id','los','died_after','prolonged_los','label']].head(15).to_string())
