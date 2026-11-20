import pandas as pd
df = pd.read_parquet('data/processed/features_W2.parquet')
train = df[df['code_presentation'].isin(['2013B','2013J'])]
test = df[df['code_presentation'].isin(['2014B','2014J'])]
train_ids = set(train['id_student'])
test_ids = set(test['id_student'])
overlap = train_ids & test_ids
print(f'Train students: {len(train_ids)}')
print(f'Test students (before): {len(test_ids)}')
print(f'Overlap: {len(overlap)}')
print(f'Overlap % of test: {len(overlap)/len(test_ids)*100:.1f}%')
