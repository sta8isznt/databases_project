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

-- --------------- Cost --------------------
load data local infile '/data/cost_ken_codes_new.csv'
into table Cost
character set utf8mb4
fields terminated by ';'
lines terminated by '\n'
(KENCode, `Description`, BaseCost, PredictedAvgTime);

-- --------------- LabTest -------------------

-- -------------- ProcedureType ---------------

