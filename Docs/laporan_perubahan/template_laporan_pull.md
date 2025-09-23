# 📋 Template Laporan Perubahan (Pull Operations)
**Tanggal:** [DD-MM-YYYY]  
**Repository:** [Repository Name]  
**Commit Range:** [commit_hash_old]..[commit_hash_new]  
**Dilakukan oleh:** RVM (Jetson Orin)  

## 🔍 **Ringkasan Perubahan**

### **📊 Statistik Perubahan:**
- **Files Changed:** [X] files
- **Insertions:** +[X] lines
- **Deletions:** -[X] lines
- **Net Change:** +[X] lines

## 📁 **Perubahan Detail**

### **1. [Category Name]**
**Lokasi:** `[file/path]`  
**Perubahan:** [Description of changes]  
**Fungsi:** 
- [Function 1]
- [Function 2]
- [Function 3]

**Files yang diupdate:**
- `[file1]`
- `[file2]`
- `[file3]`

## 🎯 **Fungsi Utama yang Ditambahkan**

### **1. [Feature Name]**
- [Description]
- [Benefits]
- [Impact]

### **2. [Feature Name]**
- [Description]
- [Benefits]
- [Impact]

## ⚠️ **Yang Perlu Dikerjakan**

### **🔧 RVM (Jetson Orin) Tasks:**
1. **[Task Category]**
   - [Specific task 1]
   - [Specific task 2]
   - [Specific task 3]

2. **[Task Category]**
   - [Specific task 1]
   - [Specific task 2]
   - [Specific task 3]

### **🏢 MyRVM-Platform Tasks:**
1. **[Task Category]**
   - [Specific task 1]
   - [Specific task 2]
   - [Specific task 3]

2. **[Task Category]**
   - [Specific task 1]
   - [Specific task 2]
   - [Specific task 3]

## 🔄 **Impact Analysis**

### **✅ Positive Impacts:**
- [Positive impact 1]
- [Positive impact 2]
- [Positive impact 3]

### **⚠️ Potential Issues:**
- [Potential issue 1]
- [Potential issue 2]
- [Potential issue 3]

## 📋 **Next Steps**

1. **Immediate (RVM):**
   - [Immediate task 1]
   - [Immediate task 2]
   - [Immediate task 3]

2. **Short Term (MyRVM-Platform):**
   - [Short term task 1]
   - [Short term task 2]
   - [Short term task 3]

3. **Long Term (Both):**
   - [Long term task 1]
   - [Long term task 2]
   - [Long term task 3]

## 📞 **Contact Information**
- **RVM System:** Jetson Orin (192.168.1.11)
- **Platform:** MyRVM-Platform Server
- **Date:** [DD-MM-YYYY]
- **Status:** [Pull/Push completed successfully]

---
**Note:** Laporan ini dibuat otomatis oleh RVM system setelah melakukan git pull/push dari [Repository Name] repository.

## 📝 **Cara Menggunakan Template:**

1. **Copy template ini**
2. **Ganti [placeholder] dengan informasi yang sesuai**
3. **Analisis perubahan menggunakan git log dan git diff**
4. **Identifikasi fungsi dan impact**
5. **Tentukan tasks untuk RVM dan MyRVM-Platform**
6. **Save dengan nama:** `YYYYMMDD_laporan_perubahan_[repository_name].md`

## 🔧 **Script untuk Generate Laporan:**

```bash
#!/bin/bash
# generate_pull_report.sh

REPO_NAME=$1
COMMIT_RANGE=$2
DATE=$(date +%Y%m%d)

# Get git stats
FILES_CHANGED=$(git diff --stat $COMMIT_RANGE | tail -1 | awk '{print $1}')
INSERTIONS=$(git diff --stat $COMMIT_RANGE | tail -1 | awk '{print $4}' | sed 's/+//')
DELETIONS=$(git diff --stat $COMMIT_RANGE | tail -1 | awk '{print $6}' | sed 's/-//')

# Generate report
cat > "Docs/laporan_perubahan/${DATE}_laporan_perubahan_${REPO_NAME}.md" << EOF
# 📋 Laporan Perubahan ${REPO_NAME}
**Tanggal:** $(date +%d-%m-%Y)
**Repository:** ${REPO_NAME}
**Commit Range:** ${COMMIT_RANGE}
**Dilakukan oleh:** RVM (Jetson Orin)

## 🔍 **Ringkasan Perubahan**

### **📊 Statistik Perubahan:**
- **Files Changed:** ${FILES_CHANGED} files
- **Insertions:** +${INSERTIONS} lines
- **Deletions:** -${DELETIONS} lines
- **Net Change:** +$((INSERTIONS - DELETIONS)) lines

[Rest of template...]
EOF

echo "Laporan generated: Docs/laporan_perubahan/${DATE}_laporan_perubahan_${REPO_NAME}.md"
```
