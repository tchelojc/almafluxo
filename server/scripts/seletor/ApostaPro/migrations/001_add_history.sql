-- Tabela de histórico
CREATE TABLE IF NOT EXISTS license_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    changed_by TEXT DEFAULT 'system',
    change_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(license_key) REFERENCES licenses(key)
);

-- Trigger
CREATE TRIGGER IF NOT EXISTS log_status_change
AFTER UPDATE OF status ON licenses
FOR EACH ROW
BEGIN
    INSERT INTO license_history (license_key, old_status, new_status)
    VALUES (OLD.key, OLD.status, NEW.status);
END;