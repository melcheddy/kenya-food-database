from supabase import create_client

# Your Supabase credentials
SUPABASE_URL = "https://biixapuddwiclyzfmfb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpaXhhcHVkZHdpY2xjeXpmbWZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3ODQxMzQsImV4cCI6MjA5MzM2MDEzNH0.RnAkAvQJeKFS8Y5HWPa7iMtNHip5CNtclcfgPMiM-p4"

print("🔌 Connecting to Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("📊 Fetching data from foods table...")
data = supabase.table('foods').select('*').limit(5).execute()

print(f"\n✅ Success! Found {len(data.data)} foods (showing first 5):")
print("-" * 50)

for food in data.data:
    print(f"🍽️  {food.get('food_name')}")
    print(f"   Energy: {food.get('energy_kcal')} kcal | Protein: {food.get('protein_g')}g")
    print()

print("🎉 Supabase connection is working!")