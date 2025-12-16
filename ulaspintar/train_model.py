# train_model.py
import pandas as pd
import re
from collections import Counter
import joblib
import os

def clean_text(text):
    """Fungsi cleaning text"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def train_model():
    """Train model dari file CSV yang ada di folder root"""
    print("🔍 Mencari file CSV untuk training...")
    
    # File CSV yang mungkin ada
    csv_files = [
        '1021480588.csv',
        '1021272829.csv', 
        '1021326563.csv',
        '1020232630.csv',
        'sample_reviews.csv'
    ]
    
    # Filter hanya file yang benar-benar ada
    existing_files = []
    for file in csv_files:
        if os.path.exists(file):
            existing_files.append(file)
            print(f"✓ Ditemukan: {file}")
    
    if not existing_files:
        print("❌ Tidak ada file CSV ditemukan di folder ini!")
        print("\n📁 File CSV harus berada di folder yang sama dengan train_model.py:")
        print("   - 1021480588.csv")
        print("   - 1021272829.csv")
        print("   - 1021326563.csv")
        print("   - 1020232630.csv")
        print("   - sample_reviews.csv")
        return None
    
    print(f"\n📊 Memproses {len(existing_files)} file CSV...")
    
    all_reviews = []
    all_ratings = []
    
    # Baca semua file CSV
    for csv_file in existing_files:
        try:
            df = pd.read_csv(csv_file)
            if 'review' in df.columns:
                reviews = df['review'].dropna().tolist()
                all_reviews.extend(reviews)
                
                if 'rating' in df.columns:
                    ratings = df['rating'].dropna().tolist()
                    all_ratings.extend(ratings)
                
                print(f"  ✓ {csv_file}: {len(reviews)} ulasan")
        except Exception as e:
            print(f"  ✗ Error membaca {csv_file}: {e}")
    
    if not all_reviews:
        print("❌ Tidak ada data ulasan yang valid ditemukan")
        return None
    
    print(f"\n📈 Total data: {len(all_reviews)} ulasan")
    if all_ratings:
        print(f"⭐ Total rating: {len(all_ratings)} data rating")
    
    # Clean semua reviews
    print("🧹 Membersihkan teks...")
    cleaned_reviews = [clean_text(review) for review in all_reviews]
    
    # Analisis kata
    print("🔤 Menganalisis kata-kata...")
    all_text = ' '.join(cleaned_reviews)
    words = all_text.split()
    word_freq = Counter(words)
    
    # Filter kata yang umum
    common_words = {word: freq for word, freq in word_freq.items() 
                    if len(word) > 2 and freq > 2}
    
    print(f"\n📊 Statistik Kata:")
    print(f"   - Total kata unik: {len(word_freq)}")
    print(f"   - Kata umum (panjang > 2, frekuensi > 2): {len(common_words)}")
    
    # Kategorikan kata berdasarkan konteks
    positive_keywords = [
        'bagus', 'baik', 'suka', 'puas', 'mantap', 'recommended',
        'cepat', 'murah', 'berkualitas', 'sempurna', 'original',
        'memuaskan', 'top', 'terbaik', 'ramah', 'aman', 'rapih',
        'senang', 'hebat', 'luar', 'biasa', 'wow', 'keren', 'cocok',
        'pas', 'sesuai', 'lengkap', 'enak', 'nyaman', 'lembut',
        'halus', 'tepat', 'amanah', 'sukses', 'salut', 'jempol',
        'gemess', 'lucu', 'cantik', 'imut', 'gemes', 'recommended'
    ]
    
    negative_keywords = [
        'buruk', 'jelek', 'kecewa', 'lambat', 'mahal', 'rusak',
        'cacat', 'mengecewakan', 'palsu', 'gagal', 'error',
        'bermasalah', 'reject', 'komplain', 'salah', 'tipis',
        'kecil', 'panas', 'kasar', 'kotor', 'bau', 'retak',
        'sobek', 'lecet', 'penyok', 'bolong', 'kurang', 'tidak',
        'jangan', 'kapok', 'rugi', 'bohong', 'menipu', 'tipu',
        'ngawur', 'jelek', 'menyesal', 'nyesel', 'bangsat'
    ]
    
    # Hitung frekuensi kata positif/negatif
    positive_words = {}
    negative_words = {}
    neutral_words = {}
    
    for word, freq in common_words.items():
        if word in positive_keywords:
            positive_words[word] = freq
        elif word in negative_keywords:
            negative_words[word] = freq
        elif freq > 5:  # Kata yang sering muncul tapi netral
            neutral_words[word] = freq
    
    print(f"\n🎯 Kategori Kata:")
    print(f"   - Kata Positif: {len(positive_words)}")
    print(f"   - Kata Negatif: {len(negative_words)}")
    print(f"   - Kata Netral: {len(neutral_words)}")
    
    # Tampilkan contoh
    print("\n📝 Contoh Kata Positif (10 teratas):")
    for word, freq in sorted(positive_words.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {word}: {freq}x")
    
    print("\n📝 Contoh Kata Negatif (10 teratas):")
    for word, freq in sorted(negative_words.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {word}: {freq}x")
    
    # Buat model data
    model_data = {
        'positive_words': positive_words,
        'negative_words': negative_words,
        'neutral_words': neutral_words,
        'total_training_samples': len(all_reviews),
        'training_date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        'source_files': existing_files
    }
    
    # Simpan model
    model_filename = 'trained_model.pkl'
    joblib.dump(model_data, model_filename)
    
    print(f"\n✅ Model berhasil disimpan sebagai '{model_filename}'")
    print(f"📁 Ukuran file: {os.path.getsize(model_filename) / 1024:.2f} KB")
    print(f"📅 Tanggal training: {model_data['training_date']}")
    
    return model_data

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 TRAINING MODEL NAIVE BAYES - ULASPINTAR")
    print("=" * 50)
    
    model = train_model()
    
    if model:
        print("\n" + "=" * 50)
        print("🎉 TRAINING SELESAI!")
        print("=" * 50)
        print("\n📋 Model dapat digunakan di app.py untuk analisis sentimen.")
    else:
        print("\n❌ Training gagal. Periksa file CSV Anda.")