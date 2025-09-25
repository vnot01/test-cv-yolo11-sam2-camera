#!/bin/bash

# Path dasar ke direktori sensor hwmon
SENSOR_PATH="/sys/devices/platform/bus@0/c240000.i2c/i2c-1/1-0040/hwmon/hwmon1"

# Fungsi untuk menghitung daya dari tegangan dan arus (dalam mW)
calculate_power() {
    local channel=$1
    local power=0
    local voltage_file="$SENSOR_PATH/in${channel}_input"
    local current_file="$SENSOR_PATH/curr${channel}_input"
    if [ -f "$voltage_file" ] && [ -f "$current_file" ]; then
        local voltage_mv=$(cat "$voltage_file")
        local current_ma=$(cat "$current_file")
        if [[ $voltage_mv =~ ^[0-9]+$ ]] && [[ $current_ma =~ ^[0-9]+$ ]]; then
            # (mV * mA) / 1000 = mW. Gunakan 'bc' untuk presisi.
            power=$(echo "scale=2; ($voltage_mv * $current_ma) / 1000" | bc)
        fi
    fi
    echo "$power"
}

echo "=== RVM POWER MONITORING TEST ==="
echo "Sensor Path: $SENSOR_PATH"
echo

# Check if sensor path exists
if [ ! -d "$SENSOR_PATH" ]; then
    echo "❌ Sensor path tidak ditemukan: $SENSOR_PATH"
    echo "Mencari alternatif sensor paths..."
    
    # Try to find alternative sensor paths
    echo "Available hwmon directories:"
    find /sys/devices -name "hwmon*" -type d 2>/dev/null | head -10
    
    echo
    echo "Available power sensor files:"
    find /sys -name "*power*" -o -name "*curr*" -o -name "*in*" 2>/dev/null | grep -E "(curr|in)" | head -10
    
    exit 1
fi

echo "✅ Sensor path ditemukan"
echo

# List available sensor files
echo "Available sensor files:"
ls -la "$SENSOR_PATH" | grep -E "(in|curr)" | head -10
echo

# --- Mengambil Data dari Sensor Individual ---
echo "=== READING POWER SENSORS ==="

# Channel 1 = GPU, Channel 2 = CPU
echo "Reading Channel 1 (GPU)..."
POWER_GPU_MW=$(calculate_power 1)
echo "  GPU Power: ${POWER_GPU_MW} mW"

echo "Reading Channel 2 (CPU)..."
POWER_CPU_MW=$(calculate_power 2)
echo "  CPU Power: ${POWER_CPU_MW} mW"

# Check if Channel 3 exists and is valid
echo "Reading Channel 3 (Total)..."
POWER_TOTAL_MW=$(calculate_power 3)
echo "  Total Power: ${POWER_TOTAL_MW} mW"

echo

# --- Meniru Agregasi jtop ---
echo "=== CALCULATING POWER BREAKDOWN ==="

# Menjumlahkan daya CPU dan GPU. Gunakan 'bc' untuk penjumlahan desimal.
POWER_CPU_GPU_CV_MW=$(echo "$POWER_CPU_MW + $POWER_GPU_MW" | bc)

# Use the higher value between measured total and calculated CPU+GPU
if (( $(echo "$POWER_TOTAL_MW > $POWER_CPU_GPU_CV_MW" | bc -l) )); then
    POWER_ACTUAL_TOTAL_MW=$POWER_TOTAL_MW
    echo "Using measured total power: ${POWER_ACTUAL_TOTAL_MW} mW"
else
    POWER_ACTUAL_TOTAL_MW=$POWER_CPU_GPU_CV_MW
    echo "Using calculated total power (CPU+GPU): ${POWER_ACTUAL_TOTAL_MW} mW"
fi

# VDD_SOC dihitung dari Total dikurangi gabungan CPU+GPU
# Ini adalah perkiraan, karena ada komponen kecil lain yang juga mengonsumsi daya
POWER_SOC_MW=$(echo "$POWER_ACTUAL_TOTAL_MW - $POWER_CPU_GPU_CV_MW" | bc)

# Ensure SOC power is not negative (set to 0 if negative)
if (( $(echo "$POWER_SOC_MW < 0" | bc -l) )); then
    POWER_SOC_MW=0
    echo "SOC power adjusted to 0 (was negative)"
fi

# Function to format power display with automatic unit conversion
format_power_display() {
    local power_mw=$1
    if (( $(echo "$power_mw >= 1000" | bc -l) )); then
        local power_w=$(echo "scale=2; $power_mw / 1000" | bc)
        echo "${power_w} W"
    else
        echo "${power_mw} mW"
    fi
}

# --- Menampilkan Hasil ---
echo "--- Perbandingan dengan jtop/tegrastats ---"
printf "%-20s : %s\n" "VDD_IN (Measured)" "$(format_power_display $POWER_TOTAL_MW)"
printf "%-20s : %s\n" "VDD_CPU_GPU_CV (Sum)" "$(format_power_display $POWER_CPU_GPU_CV_MW)"
printf "%-20s : %s\n" "VDD_SOC (Calculated)" "$(format_power_display $POWER_SOC_MW)"
printf "%-20s : %s\n" "VDD_ACTUAL_TOTAL" "$(format_power_display $POWER_ACTUAL_TOTAL_MW)"
echo "-----------------------------------------"
echo "Sensor Mentah:"
printf "  - Daya CPU (Sensor 2) : %s\n" "$(format_power_display $POWER_CPU_MW)"
printf "  - Daya GPU (Sensor 1) : %s\n" "$(format_power_display $POWER_GPU_MW)"

echo
echo "=== POWER STATUS ANALYSIS ==="

# Power status thresholds (in Watts)
TOTAL_POWER_W=$(echo "scale=2; $POWER_ACTUAL_TOTAL_MW/1000" | bc)
CPU_GPU_POWER_W=$(echo "scale=2; $POWER_CPU_GPU_CV_MW/1000" | bc)

echo "Total Power: ${TOTAL_POWER_W} W"
echo "CPU+GPU Power: ${CPU_GPU_POWER_W} W"

# Determine power status
if (( $(echo "$TOTAL_POWER_W > 15" | bc -l) )); then
    POWER_STATUS="error"
    echo "⚠️  POWER STATUS: ERROR (High power consumption: ${TOTAL_POWER_W}W)"
elif (( $(echo "$TOTAL_POWER_W > 12" | bc -l) )); then
    POWER_STATUS="maintenance"
    echo "🔧 POWER STATUS: MAINTENANCE (Elevated power: ${TOTAL_POWER_W}W)"
elif (( $(echo "$TOTAL_POWER_W > 5" | bc -l) )); then
    POWER_STATUS="active"
    echo "✅ POWER STATUS: ACTIVE (Normal power: ${TOTAL_POWER_W}W)"
else
    POWER_STATUS="inactive"
    echo "⏸️  POWER STATUS: INACTIVE (Low power: ${TOTAL_POWER_W}W)"
fi

echo
echo "=== JSON OUTPUT FOR API ==="
cat << EOF
{
  "power_status": "$POWER_STATUS",
  "power_details": {
    "total_power_mw": $POWER_ACTUAL_TOTAL_MW,
    "total_power_w": $TOTAL_POWER_W,
    "total_power_display": "$(format_power_display $POWER_ACTUAL_TOTAL_MW)",
    "cpu_power_mw": $POWER_CPU_MW,
    "cpu_power_display": "$(format_power_display $POWER_CPU_MW)",
    "gpu_power_mw": $POWER_GPU_MW,
    "gpu_power_display": "$(format_power_display $POWER_GPU_MW)",
    "cpu_gpu_combined_mw": $POWER_CPU_GPU_CV_MW,
    "cpu_gpu_combined_display": "$(format_power_display $POWER_CPU_GPU_CV_MW)",
    "soc_power_mw": $POWER_SOC_MW,
    "soc_power_w": $(echo "scale=2; $POWER_SOC_MW/1000" | bc),
    "soc_power_display": "$(format_power_display $POWER_SOC_MW)",
    "measured_total_mw": $POWER_TOTAL_MW,
    "measured_total_display": "$(format_power_display $POWER_TOTAL_MW)"
  },
  "sensor_path": "$SENSOR_PATH",
  "timestamp": "$(date -Iseconds)"
}
EOF
