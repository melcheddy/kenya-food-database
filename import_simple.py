import pandas as pd
import requests
import json

SUPABASE_URL = "https://biixapuddwiclyzfmfb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpaXhhcHVkZHdpY2xjeXpmbWZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3ODQxMzQsImV4cCI6MjA5MzM2MDEzNH0.RnAkAvQJeKFS8Y5HWPa7iMtNHip5CNtclcfgPMiM-p4"

# CSV is in the parent folder (nutrition_project)
csv_path = r"C:\Users\HP ELITEBOOK 820 G3\OneDrive\Documents\nutrition_project\kfct_foods.csv"

print("📖 Reading CSV...")
df = pd.read_csv(csv_path)
print(f"✅ Found {len(df)} foods with {len(df.columns)} columns")

# Clean column names
df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

records = df.to_dict(orient='records')

batch_size = 50
success = 0

print("\n📤 Uploading to Supabase...")

for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/foods",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        },
        json=batch
    )
    
    if response.status_code == 201:
        success += len(batch)
        print(f"  ✅ Uploaded {success}/{len(records)} foods")
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text[:200]}")
        break

print(f"\n🎉 Complete! Uploaded {success} foods")