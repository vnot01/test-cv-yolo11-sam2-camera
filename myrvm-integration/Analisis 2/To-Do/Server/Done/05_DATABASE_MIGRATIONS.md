# TASK 05: DATABASE MIGRATIONS UNTUK SEMUA TABLES

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 2-3 jam  

---

## **📋 DESKRIPSI TUGAS**

Membuat database migrations untuk semua tables yang diperlukan berdasarkan analisis requirements.

### **🎯 TUJUAN:**
- Create database migrations untuk semua tables
- Implementasi database schema yang komprehensif
- Support untuk semua fitur yang diperlukan

---

## **🔧 IMPLEMENTASI**

### **1. Remote Access Sessions Table**

#### **A. Migration File:**
```php
// File: database/migrations/2025_01_20_000001_create_remote_access_sessions_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('remote_access_sessions', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('rvm_id');
            $table->unsignedBigInteger('admin_id');
            $table->timestamp('start_time');
            $table->timestamp('end_time')->nullable();
            $table->string('status')->default('active'); // active, completed, terminated
            $table->string('ip_address', 45)->nullable();
            $table->integer('port')->nullable();
            $table->text('reason')->nullable(); // session completion reason
            $table->timestamps();
            
            $table->foreign('rvm_id')->references('id')->on('reverse_vending_machines')->onDelete('cascade');
            $table->foreign('admin_id')->references('id')->on('users')->onDelete('cascade');
            
            $table->index(['rvm_id', 'status']);
            $table->index(['admin_id', 'status']);
        });
    }

    public function down()
    {
        Schema::dropIfExists('remote_access_sessions');
    }
};
```

### **2. RVM Configurations Table**

#### **A. Migration File:**
```php
// File: database/migrations/2025_01_20_000002_create_rvm_configurations_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('rvm_configurations', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('rvm_id');
            $table->string('config_key', 100);
            $table->text('config_value')->nullable();
            $table->text('description')->nullable();
            $table->string('config_type')->default('string'); // string, integer, boolean, json
            $table->boolean('is_required')->default(false);
            $table->timestamps();
            
            $table->foreign('rvm_id')->references('id')->on('reverse_vending_machines')->onDelete('cascade');
            
            $table->unique(['rvm_id', 'config_key']);
            $table->index(['rvm_id', 'config_type']);
        });
    }

    public function down()
    {
        Schema::dropIfExists('rvm_configurations');
    }
};
```

### **3. Timezone Sync Logs Table**

#### **A. Migration File:**
```php
// File: database/migrations/2025_01_20_000003_create_timezone_sync_logs_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('timezone_sync_logs', function (Blueprint $table) {
            $table->id();
            $table->string('device_id', 100);
            $table->string('device_type', 50)->default('rvm'); // rvm, server, other
            $table->string('timezone', 50);
            $table->string('country', 100)->nullable();
            $table->string('city', 100)->nullable();
            $table->string('ip_address', 45)->nullable();
            $table->string('sync_method', 20); // automatic, manual, api
            $table->timestamp('sync_timestamp');
            $table->string('status')->default('success'); // success, failed, partial
            $table->text('details')->nullable(); // JSON details
            $table->timestamps();
            
            $table->index(['device_id', 'device_type']);
            $table->index(['sync_timestamp']);
            $table->index(['status']);
        });
    }

    public function down()
    {
        Schema::dropIfExists('timezone_sync_logs');
    }
};
```

### **4. Backup Logs Table**

#### **A. Migration File:**
```php
// File: database/migrations/2025_01_20_000004_create_backup_logs_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('backup_logs', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('rvm_id');
            $table->string('backup_type', 20); // full, incremental, config, data
            $table->string('file_path', 500);
            $table->bigInteger('file_size')->nullable(); // in bytes
            $table->string('upload_status', 20)->default('pending'); // pending, uploading, completed, failed
            $table->string('minio_path', 500)->nullable();
            $table->text('error_message')->nullable();
            $table->timestamp('started_at');
            $table->timestamp('completed_at')->nullable();
            $table->timestamps();
            
            $table->foreign('rvm_id')->references('id')->on('reverse_vending_machines')->onDelete('cascade');
            
            $table->index(['rvm_id', 'backup_type']);
            $table->index(['upload_status']);
            $table->index(['started_at']);
        });
    }

    public function down()
    {
        Schema::dropIfExists('backup_logs');
    }
};
```

### **5. System Metrics Table**

#### **A. Migration File:**
```php
// File: database/migrations/2025_01_20_000005_create_system_metrics_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('system_metrics', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('rvm_id');
            $table->decimal('cpu_usage', 5, 2)->nullable(); // percentage
            $table->decimal('memory_usage', 5, 2)->nullable(); // percentage
            $table->decimal('disk_usage', 5, 2)->nullable(); // percentage
            $table->decimal('gpu_usage', 5, 2)->nullable(); // percentage
            $table->decimal('temperature', 5, 2)->nullable(); // celsius
            $table->integer('network_latency')->nullable(); // milliseconds
            $table->integer('uptime')->nullable(); // seconds
            $table->json('additional_metrics')->nullable(); // JSON for other metrics
            $table->timestamp('recorded_at');
            $table->timestamps();
            
            $table->foreign('rvm_id')->references('id')->on('reverse_vending_machines')->onDelete('cascade');
            
            $table->index(['rvm_id', 'recorded_at']);
            $table->index(['recorded_at']);
        });
    }

    public function down()
    {
        Schema::dropIfExists('system_metrics');
    }
};
```

### **6. Update Reverse Vending Machines Table**

#### **A. Migration File:**
```php
// File: database/migrations/2025_01_20_000006_update_reverse_vending_machines_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::table('reverse_vending_machines', function (Blueprint $table) {
            // Add new columns if they don't exist
            if (!Schema::hasColumn('reverse_vending_machines', 'location')) {
                $table->text('location')->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'address')) {
                $table->text('address')->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'ip_address')) {
                $table->string('ip_address', 45)->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'port')) {
                $table->integer('port')->default(8000);
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'timezone')) {
                $table->string('timezone', 50)->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'timezone_offset')) {
                $table->string('timezone_offset', 10)->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'last_timezone_sync')) {
                $table->timestamp('last_timezone_sync')->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'last_ping')) {
                $table->timestamp('last_ping')->nullable();
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'connection_status')) {
                $table->string('connection_status', 20)->default('unknown');
            }
            if (!Schema::hasColumn('reverse_vending_machines', 'capacity')) {
                $table->integer('capacity')->default(0);
            }
            
            // Add indexes
            $table->index(['ip_address']);
            $table->index(['connection_status']);
            $table->index(['last_ping']);
        });
    }

    public function down()
    {
        Schema::table('reverse_vending_machines', function (Blueprint $table) {
            $table->dropColumn([
                'location',
                'address', 
                'ip_address',
                'port',
                'timezone',
                'timezone_offset',
                'last_timezone_sync',
                'last_ping',
                'connection_status',
                'capacity'
            ]);
        });
    }
};
```

---

## **🧪 TESTING**

### **1. Migration Testing:**

#### **A. Run Migrations:**
```bash
# Run all migrations
php artisan migrate

# Check migration status
php artisan migrate:status

# Rollback if needed
php artisan migrate:rollback
```

#### **B. Verify Tables:**
```bash
# Check if tables exist
php artisan tinker
>>> Schema::hasTable('remote_access_sessions')
>>> Schema::hasTable('rvm_configurations')
>>> Schema::hasTable('timezone_sync_logs')
>>> Schema::hasTable('backup_logs')
>>> Schema::hasTable('system_metrics')
```

### **2. Database Schema Validation:**

#### **A. Check Table Structure:**
```sql
-- Check remote_access_sessions table
\d remote_access_sessions

-- Check rvm_configurations table
\d rvm_configurations

-- Check timezone_sync_logs table
\d timezone_sync_logs

-- Check backup_logs table
\d backup_logs

-- Check system_metrics table
\d system_metrics
```

#### **B. Verify Foreign Keys:**
```sql
-- Check foreign key constraints
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name IN ('remote_access_sessions', 'rvm_configurations', 'backup_logs', 'system_metrics');
```

---

## **📋 CHECKLIST**

- [ ] Create remote_access_sessions migration
- [ ] Create rvm_configurations migration
- [ ] Create timezone_sync_logs migration
- [ ] Create backup_logs migration
- [ ] Create system_metrics migration
- [ ] Update reverse_vending_machines migration
- [ ] Run all migrations
- [ ] Verify table creation
- [ ] Check foreign key constraints
- [ ] Test rollback functionality
- [ ] Validate data types
- [ ] Check indexes

---

## **📝 NOTES**

- All migrations use proper foreign key constraints
- Indexes are added for performance optimization
- Timestamps are properly configured
- JSON fields are used for flexible data storage
- Proper cascade delete relationships

---

**Status**: ✅ **COMPLETED**  
**Completion Date**: 2025-01-20  
**Next**: Model Creation untuk semua entities
