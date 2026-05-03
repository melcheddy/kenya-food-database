import os
import pandas as pd
from supabase import create_client, Client
import time

# Your Supabase credentials
SUPABASE_URL = "https://biixapuddwiclyzfmfb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpaXhhcHVkZHdpY2xjeXpmbWZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3ODQxMzQsImV4cCI6MjA5MzM2MDEzNH0.RnAkAvQJeKFS8Y5HWPa7iMtNHip5CNtclcfgPMiM-p4"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Path to your CSV file
csv_path = r"C:\Users\HP ELITEBOOK 820 G3\OneDrive\Documents\nutrition_project\kfct_foods.csv"

print("=" * 50)
print("📊 KENYA FOOD DATABASE IMPORTER")
print("=" * 50)

# Check if CSV exists
if not os.path.exists(csv_path):
    print(f"❌ CSV file not found at: {csv_path}")
    print("Please update the csv_path variable with the correct location.")
    exit(1)

# Read CSV file
print(f"\n📖 Reading CSV file...")
df = pd.read_csv(csv_path)

print(f"✅ Found {len(df)} foods with {len(df.columns)} columns")

# Clean column names
df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

# Convert NaN to None
df = df.where(pd.notnull(df), None)

print("\n📤 Uploading to Supabase...")
print("-" * 40)

success_count = 0
error_count = 0

for index, row in df.iterrows():
    try:
        # Convert row to dictionary and clean
        data = row.to_dict()
        data = {k: v for k, v in data.items() if v is not None and str(v) != 'nan'}
        
        # Insert into Supabase
        response = supabase.table('foods').insert(data).execute()
        success_count += 1
        
        # Show progress every 50 foods
        if success_count % 50 == 0:
            print(f"  📍 Progress: {success_count}/{len(df)} foods uploaded")
        
    except Exception as e:
        error_count += 1
        food_name = row.get('food_name', 'Unknown')
        print(f"  ❌ Error on {food_name}: {str(e)[:80]}...")

print("-" * 40)
print(f"\n📊 IMPORT COMPLETE!")
print(f"   ✅ Success: {success_count}")
print(f"   ❌ Errors: {error_count}")
print("\n🎉 Done!")