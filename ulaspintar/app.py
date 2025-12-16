from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import re
import sqlite3
from datetime import datetime
from collections import Counter
import joblib
import os
import json
import random

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Setup database dengan migration
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_history'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # Create new table with all columns
        cursor.execute('''
            CREATE TABLE upload_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_reviews INTEGER,
                positif_count INTEGER,
                negatif_count INTEGER,
                netral_count INTEGER,
                chart_data TEXT  -- Menyimpan data chart sebagai JSON
            )
        ''')
        print("✅ Database table created successfully")
    else:
        # Check if chart_data column exists
        cursor.execute("PRAGMA table_info(upload_history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'chart_data' not in columns:
            # Add missing column
            cursor.execute('ALTER TABLE upload_history ADD COLUMN chart_data TEXT')
            print("✅ Added chart_data column to existing table")
        
        # Check for other missing columns (future-proofing)
        required_columns = ['filename', 'upload_date', 'total_reviews', 
                           'positif_count', 'negatif_count', 'netral_count', 'chart_data']
        
        for column in required_columns:
            if column not in columns and column != 'chart_data':
                print(f"⚠️  Warning: Column {column} might be missing")
    
    conn.commit()
    conn.close()

# Inisialisasi database
init_db()

# Kamus kata untuk Naive Bayes (diperluas)
POSITIVE_WORDS = {
    'bagus': 2.5, 'baik': 2.5, 'suka': 2.5, 'puas': 2.5, 'mantap': 2.5,
    'recommended': 2.5, 'cepat': 2.0, 'murah': 2.0, 'berkualitas': 2.5,
    'sempurna': 2.5, 'original': 2.0, 'memuaskan': 2.5, 'top': 2.5,
    'terbaik': 2.5, 'ramah': 2.0, 'aman': 2.0, 'rapih': 2.0, 'senang': 2.0,
    'hebat': 2.5, 'luar': 1.5, 'biasa': 1.5, 'wow': 1.5, 'keren': 2.0, 'cocok': 1.5,
    'pas': 1.5, 'sesuai': 1.5, 'lengkap': 1.5, 'fresh': 1.0, 'enak': 2.0,
    'nyaman': 2.0, 'lembut': 1.5, 'halus': 1.5, 'tepat': 1.5, 'amanah': 2.0,
    'sukses': 1.5, 'salut': 1.5, 'jempol': 2.0, 'gemess': 1.0, 'lucu': 1.5,
    'cantik': 2.0, 'imut': 1.5, 'gemes': 1.0, 'recomend': 2.5, 'love': 2.0,
    'sempurnah': 2.5, 'oke': 1.5, 'ok': 1.5, 'mantul': 2.0, 'mantab': 2.0,
    'menarik': 1.5, 'indah': 1.5, 'elok': 1.0, 'mulus': 1.5, 'bersih': 1.5,
    'sehat': 1.0, 'segar': 1.0, 'wang': 1.0, 'harum': 1.0, 'lezat': 1.5,
    'nikmat': 1.5, 'legit': 1.0, 'renyah': 1.0
}

NEGATIVE_WORDS = {
    'buruk': 2.5, 'jelek': 2.5, 'kecewa': 2.5, 'lambat': 2.0, 'mahal': 2.0,
    'rusak': 2.5, 'cacat': 2.5, 'mengecewakan': 2.5, 'palsu': 2.5,
    'gagal': 2.5, 'error': 2.0, 'bermasalah': 2.0, 'reject': 2.0,
    'komplain': 2.0, 'salah': 2.0, 'tipis': 1.5, 'kecil': 1.5,
    'panas': 1.5, 'kasar': 1.5, 'kotor': 2.0, 'bau': 2.0, 'retak': 2.0,
    'sobek': 2.0, 'lecet': 2.0, 'penyok': 2.0, 'bolong': 2.0, 'kurang': 1.5,
    'tidak': 1.5, 'jangan': 1.5, 'kapok': 2.0, 'rugi': 2.0, 'bohong': 2.5,
    'menipu': 2.5, 'tipu': 2.5, 'ngawur': 2.0, 'menyesal': 2.0,
    'nyesel': 2.0
}

NEUTRAL_WORDS = {
    'biasa': 1.5, 'lumayan': 1.5, 'standar': 1.5, 'oke': 1.5, 'cukup': 1.5,
    'pas': 1.0, 'sesuai': 1.0, 'normal': 1.5, 'regular': 1.5, 'average': 1.5,
    'mediocre': 1.5, 'moderat': 1.5, 'sedang': 1.5, 'pertengahan': 1.5,
    'tengah': 1.5, 'netral': 2.0, 'imbang': 1.5, 'seimbang': 1.5
}

# Implementasi Naive Bayes 
class SimpleNaiveBayes:
    def __init__(self):
        self.positive_prob = {}
        self.negative_prob = {}
        self.neutral_prob = {}
        self.total_words = 0
        
    def train(self, positive_words, negative_words, neutral_words):
        # Hitung total frekuensi
        total_positive = sum(positive_words.values())
        total_negative = sum(negative_words.values())
        total_neutral = sum(neutral_words.values())
        self.total_words = total_positive + total_negative + total_neutral
        
        # Hitung probabilitas dengan smoothing
        smoothing = 0.1
        
        for word, weight in positive_words.items():
            self.positive_prob[word] = (weight + smoothing) / (total_positive + smoothing * len(positive_words))
        
        for word, weight in negative_words.items():
            self.negative_prob[word] = (weight + smoothing) / (total_negative + smoothing * len(negative_words))
        
        for word, weight in neutral_words.items():
            self.neutral_prob[word] = (weight + smoothing) / (total_neutral + smoothing * len(neutral_words))
        
        # Prior probabilities
        self.prior_positive = total_positive / self.total_words
        self.prior_negative = total_negative / self.total_words
        self.prior_neutral = total_neutral / self.total_words
    
    def predict(self, text):
        words = text.lower().split()
        
        # Inisialisasi score dengan prior probabilities
        pos_score = self.prior_positive
        neg_score = self.prior_negative
        neu_score = self.prior_neutral
        
        # Hitung likelihood untuk setiap kata
        for word in words:
            if word in self.positive_prob:
                pos_score *= self.positive_prob[word]
            else:
                pos_score *= 0.001  # Smoothing untuk kata tidak dikenal
            
            if word in self.negative_prob:
                neg_score *= self.negative_prob[word]
            else:
                neg_score *= 0.001
            
            if word in self.neutral_prob:
                neu_score *= self.neutral_prob[word]
            else:
                neu_score *= 0.001
        
        # Normalisasi scores
        total_score = pos_score + neg_score + neu_score
        if total_score > 0:
            pos_score = pos_score / total_score
            neg_score = neg_score / total_score
            neu_score = neu_score / total_score
        
        # Tentukan sentimen berdasarkan score tertinggi
        scores = {
            'positif': pos_score,
            'negatif': neg_score,
            'netral': neu_score
        }
        
        return max(scores, key=scores.get)

# Inisialisasi model Naive Bayes
model = SimpleNaiveBayes()
model.train(POSITIVE_WORDS, NEGATIVE_WORDS, NEUTRAL_WORDS)

def clean_text(text):
    """Membersihkan teks secara komprehensif"""
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    
    # Hapus URL
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Hapus karakter khusus, tanda baca, emoji
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Hapus angka
    text = re.sub(r'\d+', '', text)
    
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def analyze_sentiment_naive_bayes(text):
    """Analisis sentimen menggunakan Naive Bayes"""
    cleaned_text = clean_text(text)
    if not cleaned_text.strip():
        return 'netral'
    
    return model.predict(cleaned_text)

def rating_to_sentiment(rating):
    """Convert rating 1-5 ke sentimen"""
    if pd.isna(rating):
        return 'netral'
    
    try:
        rating = float(rating)
        if rating >= 4:
            return 'positif'
        elif rating >= 2:
            return 'netral'
        else:
            return 'negatif'
    except:
        return 'netral'

def combine_sentiment(text_sentiment, rating_sentiment):
    """Kombinasi sentimen dari teks dan rating"""
    if text_sentiment == rating_sentiment:
        return text_sentiment
    
    # Prioritas: jika salah satu negatif, hasil negatif
    if text_sentiment == 'negatif' or rating_sentiment == 'negatif':
        return 'negatif'
    
    # Jika salah satu positif dan lainnya netral, hasil positif
    if text_sentiment == 'positif' or rating_sentiment == 'positif':
        return 'positif'
    
    return 'netral'

def save_upload_history(filename, stats, chart_data=None):
    """Simpan riwayat upload ke database"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Convert chart_data to JSON string if it exists
    chart_data_json = json.dumps(chart_data) if chart_data else None
    
    cursor.execute('''
        INSERT INTO upload_history 
        (filename, upload_date, total_reviews, positif_count, negatif_count, netral_count, chart_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        datetime.now(),
        stats['total'],
        stats.get('positif', 0),
        stats.get('negatif', 0),
        stats.get('netral', 0),
        chart_data_json
    ))
    
    conn.commit()
    conn.close()

def get_upload_history():
    """Ambil riwayat upload dari database"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # Try to get all columns including chart_data
        cursor.execute('''
            SELECT id, filename, upload_date, total_reviews, 
                   positif_count, negatif_count, netral_count,
                   chart_data
            FROM upload_history 
            ORDER BY upload_date DESC 
            LIMIT 10
        ''')
    except sqlite3.OperationalError as e:
        # If error, try without chart_data column
        if 'no such column: chart_data' in str(e):
            cursor.execute('''
                SELECT id, filename, upload_date, total_reviews, 
                       positif_count, negatif_count, netral_count
                FROM upload_history 
                ORDER BY upload_date DESC 
                LIMIT 10
            ''')
        else:
            raise e
    
    history = cursor.fetchall()
    conn.close()
    
    return history

def generate_chart_data(sentiment_counts, sentiment_percentages):
    """Generate data untuk chart visualization"""
    
    # Data untuk pie/doughnut chart
    pie_data = {
        'labels': ['Positif', 'Negatif', 'Netral'],
        'datasets': [{
            'data': [
                sentiment_counts.get('positif', 0),
                sentiment_counts.get('negatif', 0),
                sentiment_counts.get('netral', 0)
            ],
            'backgroundColor': [
                'rgba(72, 187, 120, 0.8)',   # Hijau untuk positif
                'rgba(245, 101, 101, 0.8)',  # Merah untuk negatif
                'rgba(237, 137, 54, 0.8)'    # Orange untuk netral
            ],
            'borderColor': [
                'rgba(72, 187, 120, 1)',
                'rgba(245, 101, 101, 1)',
                'rgba(237, 137, 54, 1)'
            ],
            'borderWidth': 2
        }]
    }
    
    # Data untuk bar chart (persentase)
    bar_data = {
        'labels': ['Positif', 'Negatif', 'Netral'],
        'datasets': [{
            'label': 'Persentase Sentimen',
            'data': [
                sentiment_percentages.get('positif', 0),
                sentiment_percentages.get('negatif', 0),
                sentiment_percentages.get('netral', 0)
            ],
            'backgroundColor': [
                'rgba(72, 187, 120, 0.6)',
                'rgba(245, 101, 101, 0.6)',
                'rgba(237, 137, 54, 0.6)'
            ],
            'borderColor': [
                'rgba(72, 187, 120, 1)',
                'rgba(245, 101, 101, 1)',
                'rgba(237, 137, 54, 1)'
            ],
            'borderWidth': 1
        }]
    }
    
    return {
        'pie': pie_data,
        'bar': bar_data
    }

def extract_word_frequency(texts, top_n=15):
    """Ekstrak frekuensi kata untuk word cloud"""
    all_text = ' '.join(texts)
    words = all_text.split()
    
    # Filter kata umum dan pendek
    stopwords = {'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 
                'ini', 'itu', 'saya', 'kamu', 'kami', 'mereka', 'ada',
                'tidak', 'bukan', 'akan', 'sudah', 'belum', 'pernah',
                'saja', 'hanya', 'bisa', 'dapat', 'mau', 'ingin'}
    
    words = [word for word in words 
            if len(word) > 2 
            and word not in stopwords
            and not word.isdigit()]
    
    # Hitung frekuensi
    word_freq = Counter(words)
    
    # Ambil top N kata
    top_words = word_freq.most_common(top_n)
    
    return {
        'labels': [word for word, _ in top_words],
        'data': [freq for _, freq in top_words],
        'colors': ['rgba(102, 126, 234, 0.6)' for _ in top_words]
    }

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze')
def analyze():
    # Ambil riwayat untuk ditampilkan di halaman analisis
    try:
        history = get_upload_history()
    except Exception as e:
        print(f"⚠️  Error getting history: {e}")
        history = []
    
    return render_template('analyze.html', upload_history=history)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'File tidak ditemukan'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'File tidak dipilih'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File harus berformat CSV'}), 400
        
        # Baca file CSV
        df = pd.read_csv(file, encoding='utf-8')
        
        # Validasi kolom
        if 'review' not in df.columns:
            return jsonify({'error': 'CSV harus memiliki kolom "review"'}), 400
        
        # Cek apakah ada kolom rating
        has_rating = 'rating' in df.columns
        
        # Preprocessing
        df['cleaned_review'] = df['review'].apply(clean_text)
        df = df[df['cleaned_review'].str.len() > 0]
        
        if len(df) == 0:
            return jsonify({'error': 'Tidak ada ulasan valid setelah pembersihan'}), 400
        
        # Analisis sentimen menggunakan Naive Bayes 
        df['text_sentiment'] = df['cleaned_review'].apply(analyze_sentiment_naive_bayes)
        
        # Jika ada rating, konversi rating ke sentimen
        if has_rating:
            df['rating_sentiment'] = df['rating'].apply(rating_to_sentiment)
            # Gabungkan sentimen dari teks dan rating
            df['sentiment'] = df.apply(
                lambda row: combine_sentiment(row['text_sentiment'], row['rating_sentiment']), 
                axis=1
            )
        else:
            df['sentiment'] = df['text_sentiment']
        
        # Hitung statistik
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        total = len(df)
        sentiment_percentages = {k: round(v/total*100, 2) for k, v in sentiment_counts.items()}
        
        # Generate chart data
        chart_data = generate_chart_data(sentiment_counts, sentiment_percentages)
        
        # Ekstrak keywords (tanpa stopwords manual)
        def get_top_words(texts, n=10):
            all_words = ' '.join(texts).split()
            # Filter kata pendek
            words = [word for word in all_words if len(word) > 2]
            word_freq = Counter(words)
            return word_freq.most_common(n)
        
        keywords = {}
        for sentiment in ['positif', 'negatif', 'netral']:
            if sentiment in df['sentiment'].values:
                texts = list(df[df['sentiment'] == sentiment]['cleaned_review'])
                keywords[sentiment] = get_top_words(texts, 10)
        
        # Word frequency data untuk chart
        all_texts = list(df['cleaned_review'])
        word_freq_data = extract_word_frequency(all_texts)
        
        # Generate summary
        positive_pct = sentiment_percentages.get('positif', 0)
        negative_pct = sentiment_percentages.get('negatif', 0)
        
        if positive_pct >= 70:
            summary = f"✅ SANGAT BAIK - Produk memiliki {positive_pct}% ulasan positif."
            recommendation = "Pertahankan kualitas produk dan layanan. Pertimbangkan untuk menambah stok atau variasi produk."
        elif positive_pct >= 50:
            summary = f"⚠️ CUKUP BAIK - Produk memiliki {positive_pct}% ulasan positif."
            recommendation = f"Perbaiki area dengan ulasan negatif ({negative_pct}%). Fokus pada kata kunci negatif di atas."
        else:
            summary = f"❌ PERLU PERHATIAN - Hanya {positive_pct}% ulasan positif."
            recommendation = "Lakukan evaluasi mendalam. Perbaiki kualitas produk, kemasan, atau layanan pengiriman."
        
        # Ambil sample ulasan
        samples = df[['review', 'sentiment']].head(10).to_dict('records')
        
        # Simpan ke database
        stats = {
            'total': total,
            'positif': sentiment_counts.get('positif', 0),
            'negatif': sentiment_counts.get('negatif', 0),
            'netral': sentiment_counts.get('netral', 0)
        }
        save_upload_history(file.filename, stats, chart_data)
        
        # Hitung akurasi jika ada rating
        accuracy_info = None
        if has_rating:
            # Bandingkan sentiment dengan rating untuk estimasi akurasi
            matches = sum(1 for i in range(len(df)) 
                         if (df['sentiment'].iloc[i] == 'positif' and df['rating'].iloc[i] >= 4) or
                            (df['sentiment'].iloc[i] == 'negatif' and df['rating'].iloc[i] <= 2) or
                            (df['sentiment'].iloc[i] == 'netral' and 2.5 <= df['rating'].iloc[i] <= 3.5))
            estimated_accuracy = round((matches / len(df)) * 100, 2) if len(df) > 0 else 0
            accuracy_info = {
                'estimated_accuracy': estimated_accuracy,
                'matches': matches,
                'total_compared': len(df)
            }
        
        results = {
            # Basic statistics
            'total_reviews': total,
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': sentiment_percentages,
            
            # Chart data
            'chart_data': chart_data,
            'word_freq_data': word_freq_data,
            
            # Keywords
            'keywords': keywords,
            
            # Summary
            'summary': summary,
            'recommendation': recommendation,
            
            # Samples
            'samples': samples,
            'has_rating': has_rating,
            
            # Metadata
            'upload_date': datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            'model_used': 'Menggunakan Naive Bayes',
            'accuracy_info': accuracy_info,
            
            # File info
            'filename': file.filename,
            'file_size': len(df)
        }
        
        return jsonify(results)
        
    except pd.errors.EmptyDataError:
        return jsonify({'error': 'File CSV kosong atau format tidak valid'}), 400
    except UnicodeDecodeError:
        return jsonify({'error': 'Error membaca file. Pastikan file menggunakan encoding UTF-8'}), 400
    except Exception as e:
        import traceback
        print(f"❌ Error in upload_file: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/history')
def get_history():
    """Endpoint untuk mengambil riwayat upload"""
    try:
        history = get_upload_history()
        history_list = []
        
        for item in history:
            history_dict = {
                'id': item[0],
                'filename': item[1],
                'upload_date': item[2],
                'total_reviews': item[3],
                'positif_count': item[4],
                'negatif_count': item[5],
                'netral_count': item[6]
            }
            
            # Check if chart_data exists (might be missing in old records)
            if len(item) > 7:
                history_dict['has_chart'] = bool(item[7])
            else:
                history_dict['has_chart'] = False
            
            history_list.append(history_dict)
        
        return jsonify({'history': history_list})
    except Exception as e:
        print(f"⚠️  Error in get_history endpoint: {e}")
        return jsonify({'history': []})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Endpoint untuk menghapus riwayat"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM upload_history')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Riwayat berhasil dihapus'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset_db', methods=['POST'])
def reset_db():
    """Endpoint untuk reset database (development only)"""
    try:
        # Hapus file database
        if os.path.exists('database.db'):
            os.remove('database.db')
            print("🗑️  Database file deleted")
        
        # Inisialisasi ulang
        init_db()
        
        return jsonify({'success': True, 'message': 'Database berhasil direset'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': os.path.exists('database.db'),
        'model': 'Naive Bayes initialized',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 UlasPintar - Starting Flask Application")
    app.run(debug=True, host='0.0.0.0', port=5000)