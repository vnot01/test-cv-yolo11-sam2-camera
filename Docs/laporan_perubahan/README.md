# 📋 Laporan Perubahan Repository

Direktori ini berisi laporan perubahan untuk setiap operasi pull/push yang dilakukan pada repository test-cv-yolo11-sam2-camera (myrvm-integration).

## 📁 **Struktur File**

```
Docs/laporan_perubahan/
├── README.md                                           # File ini
├── template_laporan_pull.md                            # Template untuk laporan
├── 20250923_laporan_perubahan_myrvm_integration.md    # Laporan myrvm-integration
└── [YYYYMMDD]_laporan_perubahan_[repo].md             # Laporan lainnya
```

## 📝 **Format Penamaan**

- **Format:** `YYYYMMDD_laporan_perubahan_[repository_name].md`
- **Contoh:** `20250923_laporan_perubahan_myrvm_integration.md`

## 🔄 **Proses Laporan**

### **Setiap Pull Operation:**
1. **Analisis perubahan** menggunakan `git log` dan `git diff`
2. **Identifikasi fungsi** dan impact dari perubahan
3. **Tentukan tasks** untuk RVM dan MyRVM-Platform
4. **Generate laporan** menggunakan template
5. **Save laporan** dengan format penamaan yang konsisten

### **Setiap Push Operation:**
1. **Document perubahan** yang di-push
2. **Analisis impact** pada sistem
3. **Tentukan follow-up tasks**
4. **Generate laporan** untuk tracking

## 🎯 **Tujuan Laporan**

1. **Tracking Changes:** Melacak semua perubahan pada repository
2. **Impact Analysis:** Menganalisis dampak perubahan pada sistem
3. **Task Assignment:** Menentukan siapa yang mengerjakan apa
4. **Documentation:** Dokumentasi untuk referensi masa depan
5. **Coordination:** Koordinasi antara RVM dan MyRVM-Platform

## 🔧 **Cara Menggunakan**

### **Manual:**
1. Copy `template_laporan_pull.md`
2. Ganti placeholder dengan informasi yang sesuai
3. Analisis perubahan menggunakan git commands
4. Save dengan format penamaan yang benar

### **Automatic (Future):**
```bash
# Generate laporan otomatis
./generate_pull_report.sh [repository_name] [commit_range]
```

## 📊 **Kategori Perubahan**

### **🔧 RVM (Jetson Orin) Tasks:**
- Hardware integration
- Installation method updates
- API client updates
- Testing and validation
- Documentation updates

### **🏢 MyRVM-Platform Tasks:**
- Server deployment
- Database migrations
- API endpoint updates
- UI/UX improvements
- Performance optimization

## 📋 **Template Sections**

1. **Ringkasan Perubahan** - Statistik dan overview
2. **Perubahan Detail** - File-by-file analysis
3. **Fungsi Utama** - New features dan improvements
4. **Yang Perlu Dikerjakan** - Task assignment
5. **Impact Analysis** - Positive dan negative impacts
6. **Next Steps** - Immediate, short-term, long-term tasks

## 🔍 **Git Commands untuk Analisis**

```bash
# Get commit range
git log --oneline [old_commit]..[new_commit]

# Get file changes
git diff --stat [old_commit]..[new_commit]

# Get detailed changes
git diff [old_commit]..[new_commit]

# Get commit messages
git log --pretty=format:"%h - %an, %ar : %s" [old_commit]..[new_commit]
```

## 📞 **Contact Information**

- **RVM System:** Jetson Orin (192.168.1.11)
- **Platform:** MyRVM-Platform Server
- **Maintainer:** RVM System (Automated)

---
**Note:** Semua laporan dibuat otomatis oleh RVM system untuk memastikan tracking yang konsisten dan akurat.








