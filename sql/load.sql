-- ===============================
-- Load fixed data
-- ===============================

-- --------------- Diagnosis ---------------
LOAD DATA LOCAL INFILE '/data/icd_codes.csv'
INTO TABLE Diagnosis
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';'
LINES TERMINATED BY '\n'
(ICDCode, `Description`);

