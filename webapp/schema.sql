-- ============================================================
-- CAMPUS HOSTEL LAN – DATABASE SCHEMA
-- Engine: SQLite (file: hostel.db)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ── Users (unified auth for all roles) ───────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,          -- SHA-256 hex or Werkzeug hash
    role        TEXT NOT NULL CHECK(role IN ('admin','warden','student')),
    full_name   TEXT NOT NULL,
    email       TEXT,
    phone       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active   INTEGER DEFAULT 1
);

-- ── Rooms ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rooms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT UNIQUE NOT NULL,
    block       TEXT NOT NULL,          -- 'A' or 'B'
    floor       INTEGER NOT NULL,       -- 1 or 2
    capacity    INTEGER DEFAULT 3,
    occupied    INTEGER DEFAULT 0,
    room_type   TEXT DEFAULT 'Standard' CHECK(room_type IN ('Standard','Double','Single')),
    status      TEXT DEFAULT 'Available' CHECK(status IN ('Available','Full','Maintenance')),
    amenities   TEXT                    -- comma-separated
);

-- ── Students ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    roll_number     TEXT UNIQUE NOT NULL,
    department      TEXT NOT NULL,
    year            INTEGER NOT NULL,
    room_id         INTEGER REFERENCES rooms(id),
    admission_date  DATE DEFAULT CURRENT_DATE,
    guardian_name   TEXT,
    guardian_phone  TEXT,
    photo_url       TEXT
);

-- ── Wardens ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wardens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    employee_id TEXT UNIQUE NOT NULL,
    block       TEXT,                   -- block they manage ('A','B','Both')
    designation TEXT DEFAULT 'Warden'
);

-- ── Notices ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    posted_by   INTEGER REFERENCES users(id),
    target_role TEXT DEFAULT 'all' CHECK(target_role IN ('all','student','warden','admin')),
    priority    TEXT DEFAULT 'normal' CHECK(priority IN ('normal','important','urgent')),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME
);

-- ── Complaints ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER REFERENCES students(id) ON DELETE CASCADE,
    category    TEXT NOT NULL CHECK(category IN (
                    'Maintenance','Cleanliness','Noise','Food',
                    'Water','Electricity','Internet','Security','Other')),
    subject     TEXT NOT NULL,
    description TEXT NOT NULL,
    status      TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Resolved','Closed')),
    priority    TEXT DEFAULT 'Normal' CHECK(priority IN ('Low','Normal','High','Urgent')),
    assigned_to INTEGER REFERENCES wardens(id),
    response    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);

-- ── Mess Menu ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mess_menu (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN (
                    'Monday','Tuesday','Wednesday','Thursday',
                    'Friday','Saturday','Sunday')),
    meal_type   TEXT NOT NULL CHECK(meal_type IN ('Breakfast','Lunch','Snacks','Dinner')),
    items       TEXT NOT NULL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Network Devices (for dashboard display) ───────────────────
CREATE TABLE IF NOT EXISTS network_devices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname    TEXT NOT NULL,
    device_type TEXT NOT NULL,
    ip_address  TEXT NOT NULL,
    vlan        INTEGER,
    location    TEXT,
    status      TEXT DEFAULT 'Online' CHECK(status IN ('Online','Offline','Maintenance')),
    mac_address TEXT,
    last_seen   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── ============================================================
-- SEED DATA
-- ============================================================

-- Admin user (password: admin123)
INSERT OR IGNORE INTO users (username,password,role,full_name,email,phone) VALUES
 ('admin','admin123','admin','Dr. R. Sharma','admin@hostel.local','9900000001');

-- Warden users (password: warden123)
INSERT OR IGNORE INTO users (username,password,role,full_name,email,phone) VALUES
 ('warden_a','warden123','warden','Mr. K. Reddy','warden_a@hostel.local','9900000002'),
 ('warden_b','warden123','warden','Ms. P. Nair','warden_b@hostel.local','9900000003');

-- Student users (password: student123)
INSERT OR IGNORE INTO users (username,password,role,full_name,email,phone) VALUES
 ('stu001','student123','student','Arjun Mehta','arjun@student.local','9900000010'),
 ('stu002','student123','student','Priya Singh','priya@student.local','9900000011'),
 ('stu003','student123','student','Ravi Kumar','ravi@student.local','9900000012'),
 ('stu004','student123','student','Sneha Patil','sneha@student.local','9900000013'),
 ('stu005','student123','student','Kiran Das','kiran@student.local','9900000014');

-- Wardens
INSERT OR IGNORE INTO wardens (user_id,employee_id,block,designation) VALUES
 (2,'EMP001','A','Chief Warden'),
 (3,'EMP002','B','Warden');

-- Rooms
INSERT OR IGNORE INTO rooms (room_number,block,floor,capacity,occupied,room_type,amenities) VALUES
 ('A-101','A',1,3,2,'Standard','AC,WiFi,Attached Bathroom'),
 ('A-102','A',1,3,3,'Standard','AC,WiFi,Attached Bathroom'),
 ('A-201','A',2,3,1,'Standard','AC,WiFi'),
 ('A-202','A',2,2,1,'Double','AC,WiFi,Study Table'),
 ('B-101','B',1,3,3,'Standard','WiFi,Attached Bathroom'),
 ('B-102','B',1,3,2,'Standard','WiFi'),
 ('B-201','B',2,1,1,'Single','AC,WiFi,Attached Bathroom'),
 ('B-202','B',2,3,0,'Standard','WiFi');

-- Students
INSERT OR IGNORE INTO students (user_id,roll_number,department,year,room_id,guardian_name,guardian_phone) VALUES
 (4,'CS2021001','Computer Science',3,1,'Mr. R. Mehta','9800000001'),
 (5,'CS2022001','Computer Science',2,1,'Mrs. A. Singh','9800000002'),
 (6,'EC2021001','Electronics',3,2,'Mr. S. Kumar','9800000003'),
 (7,'ME2023001','Mechanical',1,3,'Mrs. L. Patil','9800000004'),
 (8,'CS2023001','Computer Science',1,5,'Mr. B. Das','9800000005');

-- Notices
INSERT OR IGNORE INTO notices (title,content,posted_by,target_role,priority) VALUES
 ('Welcome to Hostel 2024-25','Welcome to the hostel! Please collect your room keys from the admin office by 5 PM.',1,'all','important'),
 ('Mess Timings','Breakfast: 7:00-9:00 AM | Lunch: 12:00-2:00 PM | Snacks: 5:00-6:00 PM | Dinner: 7:30-9:30 PM',1,'all','normal'),
 ('Wi-Fi Maintenance','Wi-Fi will be down for maintenance on Sunday 2:00–4:00 AM.',2,'student','normal'),
 ('Laundry Day','Laundry facility available every Saturday 9:00 AM – 5:00 PM.',1,'all','normal'),
 ('Curfew Reminder','All students must be inside hostel by 10:00 PM on weekdays and 11:00 PM on weekends.',2,'student','important');

-- Mess menu
INSERT OR IGNORE INTO mess_menu (day_of_week,meal_type,items) VALUES
 ('Monday','Breakfast','Idli, Sambar, Coconut Chutney, Tea/Coffee'),
 ('Monday','Lunch','Rice, Dal, Rajma, Sabzi, Roti, Salad, Buttermilk'),
 ('Monday','Snacks','Bread Pakora, Tea'),
 ('Monday','Dinner','Chapati, Paneer Butter Masala, Dal, Rice, Sweet'),
 ('Tuesday','Breakfast','Poha, Jalebi, Tea/Coffee'),
 ('Tuesday','Lunch','Rice, Sambar, Mixed Veg, Roti, Papad, Curd'),
 ('Tuesday','Snacks','Samosa, Tea'),
 ('Tuesday','Dinner','Chapati, Dal Makhani, Aloo Gobi, Rice, Salad'),
 ('Wednesday','Breakfast','Upma, Coconut Chutney, Tea/Coffee'),
 ('Wednesday','Lunch','Rice, Chole, Aloo Jeera, Roti, Salad, Pickle'),
 ('Wednesday','Snacks','Vada Pav, Tea'),
 ('Wednesday','Dinner','Chapati, Egg Curry/Paneer, Dal, Rice, Fruit'),
 ('Thursday','Breakfast','Paratha, Pickle, Curd, Tea/Coffee'),
 ('Thursday','Lunch','Rice, Dal Tadka, Bhindi Masala, Roti, Papad'),
 ('Thursday','Snacks','Biscuits, Tea'),
 ('Thursday','Dinner','Chapati, Chicken/Tofu Masala, Dal, Rice, Kheer'),
 ('Friday','Breakfast','Dosa, Sambar, Chutney, Tea/Coffee'),
 ('Friday','Lunch','Biryani, Raita, Salad, Papad'),
 ('Friday','Snacks','Onion Pakora, Tea'),
 ('Friday','Dinner','Chapati, Mutton/Paneer Curry, Dal, Rice, Sweet'),
 ('Saturday','Breakfast','Puri, Aloo Sabzi, Tea/Coffee'),
 ('Saturday','Lunch','Rice, Dal, Mixed Veg, Roti, Curd, Salad'),
 ('Saturday','Snacks','Pasta, Cold Drink'),
 ('Saturday','Dinner','Chapati, Soya Chunks Masala, Dal, Rice, Ice Cream'),
 ('Sunday','Breakfast','Idli, Dosa, Vada, Sambar, Chutney, Tea/Coffee'),
 ('Sunday','Lunch','Rice, Special Dal, Paneer/Chicken, Roti, Sweet'),
 ('Sunday','Snacks','Maggi, Tea'),
 ('Sunday','Dinner','Chapati, Dal Tadka, Aloo, Rice, Custard');

-- Sample complaints
INSERT OR IGNORE INTO complaints (student_id,category,subject,description,status,priority,assigned_to) VALUES
 (1,'Internet','Wi-Fi very slow in A-101','Wi-Fi speed is very slow after 8 PM. Cannot stream lectures.','Pending','High',1),
 (2,'Maintenance','Tap leaking in bathroom','The hot water tap in A-102 bathroom is leaking constantly.','In Progress','Normal',1),
 (3,'Cleanliness','Corridor not cleaned','The floor 2 corridor has not been cleaned for 3 days.','Resolved','Normal',2),
 (4,'Electricity','Frequent power cuts','Power cuts happening 2-3 times daily in room A-201.','Pending','Urgent',1),
 (5,'Food','Mess food quality issue','Food quality has declined significantly this week.','In Progress','Normal',2);

-- Network devices for dashboard
INSERT OR IGNORE INTO network_devices (hostname,device_type,ip_address,vlan,location,status,mac_address) VALUES
 ('HLN-Router','Cisco 2911 Router','192.168.100.1',NULL,'Server Room','Online','AA:BB:CC:DD:EE:01'),
 ('HLN-Core-SW','Cisco 3650 L3 Switch','192.168.10.254',10,'Server Room','Online','AA:BB:CC:DD:EE:02'),
 ('HLN-Admin-SW','Cisco 2960 Switch','192.168.10.253',10,'Admin Block','Online','AA:BB:CC:DD:EE:03'),
 ('HLN-HostelA-SW','Cisco 2960 Switch','192.168.20.252',20,'Hostel Block A','Online','AA:BB:CC:DD:EE:04'),
 ('HLN-HostelB-SW','Cisco 2960 Switch','192.168.20.253',20,'Hostel Block B','Online','AA:BB:CC:DD:EE:05'),
 ('HLN-Server-SW','Cisco 2960 Switch','192.168.100.254',100,'Server Room','Online','AA:BB:CC:DD:EE:06'),
 ('DHCP-DNS-Server','Cisco Server','192.168.100.2',100,'Server Room','Online','AA:BB:CC:DD:EE:07'),
 ('Web-App-Server','Cisco Server','192.168.100.3',100,'Server Room','Online','AA:BB:CC:DD:EE:08'),
 ('DB-Server','Cisco Server','192.168.100.4',100,'Server Room','Online','AA:BB:CC:DD:EE:09'),
 ('AP-A-F1','Wi-Fi Access Point','192.168.20.11',20,'Block A Floor 1','Online','AA:BB:CC:DD:EE:10'),
 ('AP-A-F2','Wi-Fi Access Point','192.168.20.12',20,'Block A Floor 2','Online','AA:BB:CC:DD:EE:11'),
 ('AP-B-F1','Wi-Fi Access Point','192.168.20.13',20,'Block B Floor 1','Online','AA:BB:CC:DD:EE:12'),
 ('AP-B-F2','Wi-Fi Access Point','192.168.20.14',20,'Block B Floor 2','Offline','AA:BB:CC:DD:EE:13'),
 ('AP-Guest-A','Guest Wi-Fi AP','192.168.50.11',50,'Block A Common','Online','AA:BB:CC:DD:EE:14'),
 ('AP-Guest-B','Guest Wi-Fi AP','192.168.50.12',50,'Block B Common','Online','AA:BB:CC:DD:EE:15');
