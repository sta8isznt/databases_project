-- Active: 1778170419470@@localhost@3306
-- Active: 1778170419470@@localhost@3306@HospitalDB
 -- =========================
-- TABLES
-- =========================

drop database if exists HospitalDB;

create database HospitalDB;

use HospitalDB;

-- ------STAFF PART ----------------------------------- 
create table Staff(
    AMKA char(11) primary key check(AMKA regexp '^[0-9]{11}$'),
    FirstName varchar(20) not null,
    LastName varchar(20) not null,
    BirthDate date not null,
    Email varchar(30) UNIQUE,                               
    HireDate date not null,
    IsActive boolean not null default 1,
    `Type` varchar(20) not null check(`Type` in ('Doctor', 'Nurse', 'AdminStaff')),

    constraint chk_birth_hire check(BirthDate < HireDate)
);

create table StaffPhone(
    StaffAMKA char(11),
    Phone char(10) not null check(Phone regexp '^[0-9]{10}$'),

    primary key(StaffAMKA, Phone),
    foreign key (StaffAMKA) references Staff(AMKA) on delete cascade on update cascade
);

create table Doctor(
    AMKA char(11) primary key,
    License varchar(20) not null UNIQUE,
    Specialty varchar(20) not null,
    `Rank` varchar(20) not null check (`Rank` in ('Resident', 'Director', 'Registrar', 'Consultant')),
    SupervisorAMKA char(11),     -- SupervisorAMKA can be null (e.g. for Directors)

    foreign key (AMKA) references Staff(AMKA) on delete restrict on update cascade,
    foreign key(SupervisorAMKA) references Doctor(AMKA) on delete restrict on update cascade
);

create table Department(
    DepartmentID int auto_increment primary key,
    `Name` varchar(30) not null unique,
    `Description` text not null,
    Floor tinyint not null check(Floor >= 0),
    Building varchar(50) not null,
    DirectorAMKA char(11) not null UNIQUE,

    foreign key (DirectorAMKA) references Doctor(AMKA) on delete restrict on update cascade
);

create table Nurse(
    AMKA char(11) primary key,
    `Rank` varchar(20) not null check(`Rank` in ("AssistantNurse", "Nurse", "HeadNurse")),
    DepartmentID int not null,

    foreign key (AMKA) references Staff(AMKA) on delete restrict on update cascade,
    foreign key (DepartmentID) references Department(DepartmentID),
    unique (AMKA, DepartmentID)
);

create table AdminStaff(
    AMKA char(11) primary key,
    `Role` varchar(20) not null,
    Office varchar(20) not null,
    DepartmentID int not null,

    foreign key(AMKA) references Staff(AMKA) on delete restrict on update cascade,
    foreign key (DepartmentID) references Department(DepartmentID),
    unique (AMKA, DepartmentID)
);

-- ----DEPARTMENT PART -----------------------------------
create table DoctorDepartment(
    DoctorAMKA char(11),
    DepartmentID int,

    primary key(DoctorAMKA, DepartmentID),
    foreign key (DoctorAMKA) references Doctor(AMKA) on delete cascade on update cascade,
    foreign key (DepartmentID) references Department(DepartmentID) on delete cascade
);

create table Room(
    ID smallint,
    DepartmentID int,
    `Type` varchar(20) not null,
    `State` varchar(20) not null default 'Available' check(`State` in ('Available', 'Occupied', 'UnderMaintenance')),

    primary key (ID, DepartmentID),
    foreign key (DepartmentID) references Department(DepartmentID) on delete cascade
);

-- ---PATIENT PART -----------------------------------

create table InsuranceProvider(
    `Name` varchar(30) primary key
);

create table Patient(
    AMKA char(11) primary key check(AMKA regexp '^[0-9]{11}$'),
    FirstName varchar(20) not null,
    LastName varchar(20) not null,
    FatherName varchar(20) not null,
    BirthDate date not null,
    Gender char(1) not null check(Gender in ('M', 'F')),
    `Weight` decimal(4,1) not null check(`Weight` > 0),
    `Height` decimal(4,1) not null check(`Height` > 0),
    `Address` varchar(50) not null,
    Email varchar(30),
    Profession varchar(30),
    Nationality varchar(30) not null,
    isActive boolean not null default 1,
    InsuranceProviderName varchar(30) not null,

    foreign key (InsuranceProviderName) references InsuranceProvider(`Name`) on delete restrict on update cascade
);

create table PatientPhone(
    PatientAMKA char(11),
    Phone char(10) not null check(Phone regexp '^[0-9]{10}$'),

    primary key(PatientAMKA, Phone),
    foreign key (PatientAMKA) references Patient(AMKA) on delete cascade on update cascade
);

create table EmergencyContact(
    `ID` int auto_increment primary key, 
    PatientAMKA char(11) not null,
    FirstName varchar(20) not null,
    LastName varchar(20) not null,
    `Address` varchar(50) not null,
    Email varchar(30),
    Relation varchar(20) not null,

    foreign key (PatientAMKA) references Patient(AMKA) on delete cascade on update cascade
);

create table EmContactPhone(
    `ID` int,
    Phone char(10) not null check(Phone regexp '^[0-9]{10}$'),

    primary key(`ID`, Phone),
    foreign key (`ID`) references EmergencyContact(`ID`) on delete cascade
);

-- HOSPITALIZATION PART -----------------------------------
create table `Cost`(
    KENCode varchar(5) primary key,
    `Description` text not null,
    BaseCost mediumint not null check(BaseCost > 0),
    PredictedAvgTime int not null check(PredictedAvgTime > 0),
    ChargePerDay DECIMAL(10,2) generated always as (BaseCost / PredictedAvgTime) virtual
);

create table Hospitalization(
    HospitalizationID int auto_increment primary key,
    AdmissionDateTime datetime not null,
    PatientAMKA char(11) not null,
    ExitDateTime datetime,
    RoomID smallint not null,
    DepartmentID int not null,
    KENcode varchar(5) not null,
    ActualDays int generated always as (TIMESTAMPDIFF(DAY, AdmissionDateTime, ExitDateTime)) virtual,
    -- AdditionalFees(),
    -- TotalFees(),

    unique(PatientAMKA, AdmissionDateTime),
    Foreign Key (KENcode) REFERENCES Cost(KENCode) on delete restrict on update cascade,
    Foreign Key (PatientAMKA) REFERENCES Patient(AMKA) on delete restrict on update cascade,
    Foreign Key (RoomID, DepartmentID) REFERENCES Room(ID, DepartmentID) on delete restrict,
    constraint chk_exit_after_admission check((ExitDateTime is Null) or ExitDateTime >= AdmissionDateTime)
);

create table TriageEvent(
    TriageID int auto_increment primary key,
    Symptoms text,
    EmergencyLevel tinyint check(EmergencyLevel between 1 and 5) not null,
    Outcome varchar(30) not null  default 'Pending' check(Outcome in ("Accepted", "Discarded","Pending")),
    TriageDateTime datetime not null,
    HospitalizationID int,
    AssessmentDateTime datetime,
    PatientAMKA char(11) not null,
    NurseAMKA char(11) not null,

    unique(PatientAMKA, TriageDateTime),
    constraint chk_triage_outcome check (
        (Outcome = 'Pending' AND HospitalizationID IS NULL AND AssessmentDateTime IS NULL) OR
        (Outcome = 'Accepted' AND HospitalizationID IS NOT NULL AND AssessmentDateTime IS NOT NULL) OR
        (Outcome = 'Discarded' AND HospitalizationID IS NULL AND AssessmentDateTime IS NOT NULL)
    ),
    foreign key (HospitalizationID) references Hospitalization(HospitalizationID) on delete restrict,
    foreign key (PatientAMKA) REFERENCES Patient(AMKA) on delete restrict on update cascade,
    foreign key (NurseAMKA) REFERENCES Nurse(AMKA) on delete restrict on update cascade
);

CREATE TABLE HospEvaluation (
    HospitalizationID INT PRIMARY KEY,
    QoNurseS TINYINT CHECK (QoNurseS BETWEEN 1 AND 5),
    Cleanliness TINYINT CHECK (Cleanliness BETWEEN 1 AND 5),
    Food TINYINT CHECK (Food BETWEEN 1 AND 5),
    GeneralExperience TINYINT CHECK (GeneralExperience BETWEEN 1 AND 5),
    FOREIGN KEY (HospitalizationID) REFERENCES Hospitalization(HospitalizationID) ON DELETE CASCADE
);

CREATE TABLE DoctorEvaluation (
    HospitalizationID INT,
    DoctorAMKA CHAR(11),
    QoDoctorS TINYINT CHECK (QoDoctorS BETWEEN 1 AND 5),
    PRIMARY KEY (HospitalizationID, DoctorAMKA),
    FOREIGN KEY (HospitalizationID) REFERENCES Hospitalization(HospitalizationID) ON DELETE CASCADE,
    FOREIGN KEY (DoctorAMKA) REFERENCES Doctor(AMKA) ON DELETE CASCADE
);



create table Diagnosis(
    ICDCode varchar(10) primary key,
    `Description` text not NULL
);

create table ExitDiagnosis(
    HospitalizationID int,
    ICDCode varchar(10),

    primary key (HospitalizationID, ICDCode),
    foreign key (HospitalizationID) references Hospitalization(HospitalizationID) on delete restrict,
    foreign key (ICDCode) references Diagnosis(ICDCode) on delete restrict on update cascade
);

create table AdmissionDiagnosis(
    HospitalizationID int,
    ICDCode varchar(10),

    primary key (HospitalizationID, ICDCode),
    foreign key (HospitalizationID) references Hospitalization(HospitalizationID) on delete restrict,
    foreign key (ICDCode) references Diagnosis(ICDCode) on delete restrict on update cascade 
);

create table LabTest(
    LabCode varchar(20) primary key,
    LabType varchar(10) not null,
    LabDescription text not null,
    LabCost int,
    IsActive boolean not null default 1
);

create table HospLabTest(
    Id int auto_increment primary key,
    HospitalizationID int not null,
    LabCode varchar(20) not null,
    LabDateTime datetime not null,
    LabResult text,
    PendingResult boolean not null default 1,
    DoctorAMKA char(11) not null,

    foreign key (HospitalizationID) references Hospitalization(HospitalizationID) on delete restrict,
    foreign key (LabCode) references LabTest(LabCode) on delete restrict on update cascade,
    foreign key (DoctorAMKA) references Doctor(AMKA) on delete restrict on update cascade,
    unique(HospitalizationID, LabCode, LabDateTime),
    constraint chk_pending_or_result check ((PendingResult = 1) OR (LabResult is not null)),
    constraint chk_no_result_when_pending check (PendingResult = 0 OR LabResult is null)
);

-- --------------------- PROCEDURE ---------------------------------------
create table ProcedureType (
    ProcCode varchar(20) primary key,
    ProcName varchar(50) not null,
    ProcType varchar(20) not null check(ProcType in ('Surgical', 'Diagnostic', 'Therapeutic')),
    ProcDuration int not null check(ProcDuration > 0),
    ProcCost int
);

create table ProcedureRoom (
    ProcRoomID smallint primary key auto_increment,
    ProcRoomType varchar(20) not null check(ProcRoomType in ('OperatingRoom', 'InterventionRoom')),
    `State` varchar(20) not null default 'Available' check(`State` in ('Available', 'Occupied', 'UnderMaintenance'))
);

create table ProcedureEvent (
    ProcEventID int auto_increment primary key,
    ProcRoomID smallint not null, 
    `DateTime` datetime not null,
    MainDocAMKA char(11) not null,
    ProcedureCode varchar(20) not null,
    HospitalizationID int not null,

    UNIQUE (ProcRoomID, DateTime), -- A procedure room cannot have more than one procedure event at the same date and time
    Foreign Key (ProcRoomID) REFERENCES ProcedureRoom(ProcRoomID) on delete restrict, 
    Foreign Key (ProcedureCode) REFERENCES ProcedureType(ProcCode) on delete restrict on update cascade,
    Foreign Key (MainDocAMKA) REFERENCES Doctor(AMKA) on delete restrict on update cascade,
    foreign key (HospitalizationID) references Hospitalization(HospitalizationID) on delete restrict
);

create table operates_in (
    DoctorAMKA char(11),
    ProcEventID int,

    primary key (DoctorAMKA, ProcEventID),
    foreign key (DoctorAMKA) references Doctor(AMKA) on delete cascade on update cascade,
    foreign key (ProcEventID) references ProcedureEvent(ProcEventID) on delete cascade
);

create table assists_in (
    NurseAMKA char(11),
    ProcEventID int,

    primary key (NurseAMKA, ProcEventID),
    foreign key (NurseAMKA) references Nurse(AMKA) on delete cascade on update cascade,
    foreign key (ProcEventID) references ProcedureEvent(ProcEventID) on delete cascade
);

create table helps_in (
    AdminStaffAMKA char(11),
    ProcEventID int,

    primary key (AdminStaffAMKA, ProcEventID),
    foreign key (AdminStaffAMKA) references AdminStaff(AMKA) on delete cascade on update cascade,
    foreign key (ProcEventID) references ProcedureEvent(ProcEventID) on delete cascade
);
                   
-- ------------------------- SHIFTS ---------------------------------------
create table ShiftType (
    `Name` varchar(20) primary key check(`Name` in ('Morning', 'Afternoon', 'Night')),
    StartTime time not null unique CHECK (StartTime IN ('07:00:00', '15:00:00', '23:00:00')),
    EndTime time generated always as (ADDTIME(StartTime, '08:00:00')) virtual,

    constraint chk_shift_type check (
        (`Name` = 'Morning' and StartTime = '07:00:00') or
        (`Name` = 'Afternoon' and StartTime = '15:00:00') or
        (`Name` = 'Night' and StartTime = '23:00:00')
    )
);

create table Shift (
    DepartmentID int not null,
    ShiftTypeName varchar(20) not null,
    `Date` date not null,

    primary key (DepartmentID, ShiftTypeName, `Date`),
    foreign key (DepartmentID) references Department(DepartmentID) on delete restrict,
    foreign key (ShiftTypeName) references ShiftType(`Name`) on delete restrict
);

create table hasDoctor (
    DepartmentID int,
    ShiftTypeName varchar(20),
    ShiftDate date,
    DoctorAMKA char(11),

    primary key (DepartmentID, ShiftTypeName, ShiftDate, DoctorAMKA),
    unique (DoctorAMKA, ShiftDate, ShiftTypeName), -- A doctor cannot have more than one shift of the same type on the same day
    foreign key (DepartmentID, ShiftTypeName, ShiftDate) references Shift(DepartmentID, ShiftTypeName, `Date`) on delete cascade,
    foreign key (DoctorAMKA) references Doctor(AMKA) on delete cascade on update cascade,
    -- A doctor can only work in a shift for a department they are associated with through DoctorDepartment
    foreign key (DoctorAMKA, DepartmentID) references DoctorDepartment(DoctorAMKA, DepartmentID) on delete restrict on update cascade
);

create table hasNurse (
    DepartmentID int,
    ShiftTypeName varchar(20),
    ShiftDate date,
    NurseAMKA char(11),

    primary key (DepartmentID, ShiftTypeName, ShiftDate, NurseAMKA),
    unique (NurseAMKA, ShiftDate, ShiftTypeName), -- A nurse cannot have more than one shift of the same type on the same day
    foreign key (DepartmentID, ShiftTypeName, ShiftDate) references Shift(DepartmentID, ShiftTypeName, `Date`) on delete cascade,
    -- Nurses can only work in a shift for the department they belong to
    foreign key (NurseAMKA, DepartmentID) references Nurse(AMKA, DepartmentID) on delete restrict on update cascade
);

create table hasAdmin (
    DepartmentID int,
    ShiftTypeName varchar(20),
    ShiftDate date,
    AdminAMKA char(11),

    primary key (DepartmentID, ShiftTypeName, ShiftDate, AdminAMKA),
    unique (AdminAMKA, ShiftDate, ShiftTypeName), -- An admin staff cannot have more than one shift of the same type on the same day
    foreign key (DepartmentID, ShiftTypeName, ShiftDate) references Shift(DepartmentID, ShiftTypeName, `Date`) on delete cascade,
    -- Admin Staff can only work in a shift for the department they belong to   
    foreign key (AdminAMKA, DepartmentID) references AdminStaff(AMKA, DepartmentID) on delete cascade on update cascade
);

create table DrugType(
    DrugID int auto_increment primary key,
    `Name` varchar(300) not null,
    `Route` varchar(255) not null,
    AuthCountry varchar(50) not null,
    AuthHolder varchar(120) not null,
    MasterFileLocation varchar(50) not null,
    Email varchar(120) not null
);

create table Substances(
    ID int auto_increment primary key,
    `Name` varchar(255) not null unique
);

create table HasSubstances (
    SubID int not null,
    DrugID int not null,

    primary key(SubID,DrugID),
    Foreign Key (SubID) REFERENCES Substances(ID) on delete cascade,
    foreign key (DrugID) references DrugType(DrugID) on delete cascade 
); -- this is a relation for the multivalued attribute DrugSubstances of Drugs

create table DrugSupportPhone (
    DrugID int,
    Phone varchar(14) not null check(Phone regexp '^[0-9]{10,14}$'), /* check this one */

    primary key (DrugID, Phone),
    foreign key (DrugID) references DrugType(DrugID) on delete cascade
);

create table allergic_to(
    PatientAMKA char(11),
    SubstanceID int,

    primary key (PatientAMKA, SubstanceID),
    foreign key (PatientAMKA) references Patient(AMKA) on delete cascade on update cascade,
    foreign key (SubstanceID) references Substances(ID) on delete restrict
);

create table PrescriptionEvent (
    PrescriptionID int auto_increment primary key,
    HospitalizationID int not null,
    DoctorAMKA char(11) not null,
    DrugID int not null,
    Dosage varchar(30) not null,
    frequency varchar(30) not null,
    PrescriptionDate date not null,
    StartDate date not null,
    EndDate date,

    unique(DoctorAMKA, HospitalizationID, DrugID, StartDate), -- A doctor cannot prescribe the same drug to the same patient on the same day
    foreign key (HospitalizationID) references Hospitalization(HospitalizationID) on delete restrict,
    foreign key (DoctorAMKA) references Doctor(AMKA) on delete restrict on update cascade,
    foreign key (DrugID) references DrugType(DrugID) on delete restrict,
    constraint chk_end_date check (EndDate is null or EndDate >= StartDate)
);

create table `Image`(
    ImageID int auto_increment primary key,
    ImageURL varchar(255) not null,
    ImageDescription text not null,

    ProcRoomId smallint, 
    StaffAMKA char(11),
    DepartmentID int,
    RoomID smallint,
    RoomDepartmentID int,

    foreign key(ProcRoomId) references ProcedureRoom(ProcRoomID) on delete restrict,
    foreign key(StaffAMKA) references Staff(AMKA) on delete restrict on update cascade,
    foreign key(DepartmentID) references Department(DepartmentID) on delete restrict,
    Foreign Key (RoomID, RoomDepartmentID) REFERENCES Room(ID, DepartmentID) on delete restrict,

    -- If the Image is associated with a Room, then both RoomID and RoomDepartmentID must be non-null.
    constraint chk_room_association check (
        (RoomID is null and RoomDepartmentID is null) or
        (RoomID is not null and RoomDepartmentID is not null)
    )
);

-- =========================
-- TRIGGERS
-- =========================
DELIMITER //

-- -------------------------------------- Triggers for Doctor -----------------------------
CREATE TRIGGER trg_doctor_before_insert 
BEFORE INSERT ON Doctor 
FOR EACH ROW 
BEGIN
    DECLARE cnt int unsigned default 0;

    --  Check Supervisor Rules
    IF NEW.Rank = 'Resident' AND NEW.SupervisorAMKA IS NULL THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Resident doctors must have a supervisor'; 
    END IF; 
    
    IF NEW.Rank = 'Director' AND NEW.SupervisorAMKA IS NOT NULL THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Director doctors cannot have a supervisor'; 
    END IF;

    -- Check for Supervision Cycles
    IF NEW.SupervisorAMKA = NEW.AMKA THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'A doctor cannot supervise themselves';
    END IF;  

    if new.SupervisorAMKA is not null then 
        with recursive superchain(SupervisorAMKA) as(
                select SupervisorAMKA 
                from Doctor
                where AMKA = new.SupervisorAMKA
            union all
                select doc.SupervisorAMKA
                from Doctor doc
                join superchain sc on doc.AMKA = sc.SupervisorAMKA
                where doc.SupervisorAMKA is not null
        ) 
        select count(*) into cnt from superchain where SupervisorAMKA = new.AMKA;
    end if;
    if cnt > 0 then
        signal sqlstate '45000' 
        set message_text = "Cycle detected in doctor supervision hierarchy";
    end if;
END//

CREATE TRIGGER trg_doctor_before_update 
BEFORE UPDATE ON Doctor 
FOR EACH ROW 
BEGIN
    DECLARE cnt int unsigned default 0;

    --  Check Supervisor Rules
    IF NEW.Rank = 'Resident' AND NEW.SupervisorAMKA IS NULL THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Resident doctors must have a supervisor'; 
    END IF; 
    
    IF NEW.Rank = 'Director' AND NEW.SupervisorAMKA IS NOT NULL THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Director doctors cannot have a supervisor'; 
    END IF;

    -- Check for Supervision Cycles
    IF NEW.SupervisorAMKA = NEW.AMKA THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'A doctor cannot supervise themselves';
    END IF;  

    if new.SupervisorAMKA is not null then 
        with recursive superchain(SupervisorAMKA) as(
                select SupervisorAMKA 
                from Doctor
                where AMKA = new.SupervisorAMKA
            union all
                select doc.SupervisorAMKA
                from Doctor doc
                join superchain sc on doc.AMKA = sc.SupervisorAMKA
                where doc.SupervisorAMKA is not null
        ) 
        select count(*) into cnt from superchain where SupervisorAMKA= new.AMKA;
    end if;
    if cnt > 0 then
        signal sqlstate '45000' 
        set message_text = "Cycle detected in doctor supervision hierarchy";
    end if;
END//

-- --------------- PrescriptionEvent Triggers ----------------
create trigger trg_patient_allergy_check_before_insert
before insert on PrescriptionEvent
for each row
begin  
    -- Variables to hold the patient's AMKA and the count of allergies to the prescribed drug
    declare PatientAMKAcheck char(11);
    declare AllergyCnt int unsigned default 0;

    -- AMKA from HospitalizationID in the new PrescriptionEvent row
    select PatientAMKA into PatientAMKAcheck 
    from Hospitalization 
    where HospitalizationID = new.HospitalizationID;  

    -- Count how many substances in the prescribed drug the patient is allergic to
    select count(*) into AllergyCnt 
    from HasSubstances hs 
    join allergic_to a on hs.SubID = a.SubstanceID 
    where hs.DrugID = new.DrugID
    and a.PatientAMKA = PatientAMKAcheck;
    
    -- If the count is greater than 0, signal an error to prevent the prescription
    if AllergyCnt > 0 then
        signal sqlstate '45000'
        set message_text = "Prescription violates patient's allergy constraints";
    end if;
end //

create trigger trg_patient_allergy_check_before_update
before update on PrescriptionEvent
for each row
begin  
    -- Variables to hold the patient's AMKA and the count of allergies to the prescribed drug
    declare PatientAMKAcheck char(11);
    declare AllergyCnt int unsigned default 0;

    -- AMKA from HospitalizationID in the new PrescriptionEvent row
    select PatientAMKA into PatientAMKAcheck 
    from Hospitalization 
    where HospitalizationID = new.HospitalizationID;

    -- Count how many substances in the prescribed drug the patient is allergic to
    select count(*) into AllergyCnt 
    from HasSubstances hs 
    join allergic_to a on hs.SubID = a.SubstanceID 
    where hs.DrugID = new.DrugID 
    and a.PatientAMKA = PatientAMKAcheck;

    -- If the count is greater than 0, signal an error to prevent the prescription
    if AllergyCnt > 0 then
        signal sqlstate '45000'
        set message_text = "Prescription violates patient's allergy constraints";
    end if;
end //

-- ------------------------------ ProcedureEvent Triggers ----------------
CREATE TRIGGER trg_Procedure_Overlap_Insert
BEFORE INSERT ON ProcedureEvent
FOR EACH ROW
BEGIN
    DECLARE NewDuration INT;
    DECLARE NewEndTime DATETIME;
    DECLARE OverlapCount INT DEFAULT 0;
    DECLARE v_IsActive BOOLEAN;

    -- Check if the Main Doctor is active
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.MainDocAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Scheduling Error: Cannot assign an inactive doctor to a procedure.';
    END IF;

    -- Read the duration of the procedure type being scheduled
    SELECT ProcDuration INTO NewDuration
    FROM ProcedureType
    WHERE ProcCode = NEW.ProcedureCode;

    -- Find NewEndTime by adding the duration to the start time of the new procedure
    SET NewEndTime = DATE_ADD(NEW.DateTime, INTERVAL NewDuration MINUTE);

    -- Check for overlapping procedures in the same room or with the same main doctor
    SELECT COUNT(*) INTO OverlapCount
    FROM ProcedureEvent pe
    JOIN ProcedureType pt ON pe.ProcedureCode = pt.ProcCode
    WHERE (pe.ProcRoomID = NEW.ProcRoomID OR pe.MainDocAMKA = NEW.MainDocAMKA)        -- Check same room or same main doctor
      AND (NEW.DateTime < DATE_ADD(pe.DateTime, INTERVAL pt.ProcDuration MINUTE))   -- NewStart < OldEnd
      AND (pe.DateTime < NewEndTime);                                               -- OldStart < NewEnd

    -- Check signals an error if there is any overlap
    IF OverlapCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Procedure overlaps with another procedure for the same room or main doctor';
    END IF;
END //

CREATE TRIGGER trg_Procedure_Overlap_Update
BEFORE UPDATE ON ProcedureEvent
FOR EACH ROW
BEGIN
    DECLARE NewDuration INT;
    DECLARE NewEndTime DATETIME;
    DECLARE OverlapCount INT DEFAULT 0;
    DECLARE v_IsActive BOOLEAN;

    -- Check if the Main Doctor is active
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.MainDocAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Scheduling Error: Cannot assign an inactive doctor to a procedure.';
    END IF;

    -- Read the duration of the procedure type being scheduled
    SELECT ProcDuration INTO NewDuration
    FROM ProcedureType
    WHERE ProcCode = NEW.ProcedureCode;

    -- Find NewEndTime by adding the duration to the start time of the new procedure
    SET NewEndTime = DATE_ADD(NEW.DateTime, INTERVAL NewDuration MINUTE);

    -- Check for overlapping procedures in the same room or with the same main doctor (excluding the current record)
    SELECT COUNT(*) INTO OverlapCount
    FROM ProcedureEvent pe
    JOIN ProcedureType pt ON pe.ProcedureCode = pt.ProcCode
    WHERE (pe.ProcRoomID = NEW.ProcRoomID OR pe.MainDocAMKA = NEW.MainDocAMKA)        -- Check same room or same main doctor
      AND (NEW.DateTime < DATE_ADD(pe.DateTime, INTERVAL pt.ProcDuration MINUTE))   -- NewStart < OldEnd
      AND (pe.DateTime < NewEndTime)                                                -- OldStart < NewEnd
      AND pe.ProcEventID != NEW.ProcEventID;                                        -- Exclude the current record being updated

    -- Check signals an error if there is any overlap
    IF OverlapCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Procedure overlaps with another procedure for the same room or main doctor';
    END IF;

END //

-- Triggers for HasDoctor -----------------------------
CREATE TRIGGER trg_hasdoctor_shift_before_insert 
BEFORE INSERT ON HasDoctor 
FOR EACH ROW 
BEGIN
    declare ShiftCount int unsigned default 0;
    declare NewStartTime time;
    declare NewStartDateTime datetime;
    declare cnt int unsigned default 0;
    declare overlapcnt int unsigned default 0;
    declare v_DoctorRank varchar(20);
    declare v_SeniorCount int default 0;
    DECLARE v_IsActive BOOLEAN;

    -- ==========================================
    -- RULE 0: Is the Staff Member Active?
    -- ==========================================
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.DoctorAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HR Error: Cannot assign a shift to an inactive staff member.';
    END IF;
    -- Check maximum shifts per month (15 shifts)
    select count(*) into ShiftCount
    from hasDoctor
    where DoctorAMKA = new.DoctorAMKA
    and month(ShiftDate) = month(new.ShiftDate)
    and year(ShiftDate) = year(new.ShiftDate);

    if ShiftCount >= 15 then
        signal sqlstate '45000'
        set message_text = "A doctor cannot have more than 15 shifts in the same month";
    end if;

    -- Get the start time of the new shift (for 8-hour rule)
    select StartTime into NewStartTime
    from ShiftType
    where `Name` = new.ShiftTypeName;

    set NewStartDateTime = timestamp(new.ShiftDate, NewStartTime);
    select count(*) into overlapcnt
    from hasDoctor hd
    join ShiftType st on hd.ShiftTypeName = st.`Name`
    where hd.DoctorAMKA = new.DoctorAMKA
    and abs(timestampdiff(hour, NewStartDateTime, timestamp(hd.ShiftDate, st.StartTime))) < 16;
    if overlapcnt > 0 then
        signal sqlstate '45000'
        set message_text = "A doctor cannot have two shifts with less than 8 hours in between";
    end if;

    -- Check for 3 consecutive night shifts
    if new.ShiftTypeName = 'Night' then
        select count(*) into cnt
        from HasDoctor 
        where DoctorAMKA = new.DoctorAMKA
        and ShiftTypeName = 'Night'
        and ShiftDate in (
            date_sub(new.ShiftDate, interval 1 day),
            date_sub(new.ShiftDate, interval 2 day),
            date_sub(new.ShiftDate, interval 3 day)
        );
        if cnt = 3 then 
            signal sqlstate '45000'
            set message_text = "A doctor cannot work more than 3 consecutive night shifts";
        end if;  
    end if;

    -- Find the rank of the doctor trying to be inserted
    SELECT `Rank` INTO v_DoctorRank FROM Doctor WHERE AMKA = NEW.DoctorAMKA;

    -- If they are a Resident, check the shift for a senior
    IF v_DoctorRank = 'Resident' THEN
        SELECT COUNT(*) INTO v_SeniorCount
        FROM hasDoctor hd
        JOIN Doctor d ON hd.DoctorAMKA = d.AMKA
        WHERE hd.DepartmentID = NEW.DepartmentID
          AND hd.ShiftTypeName = NEW.ShiftTypeName
          AND hd.ShiftDate = NEW.ShiftDate
          AND d.`Rank` IN ('Director', 'Registrar', 'Consultant');

        IF v_SeniorCount = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Staffing Error: A Resident cannot be scheduled for a shift without a Senior doctor present.';
        END IF;
    END IF;
END//

CREATE TRIGGER trg_hasdoctor_shift_before_update
BEFORE UPDATE ON HasDoctor 
FOR EACH ROW 
BEGIN
    declare ShiftCount int unsigned default 0;
    declare NewStartTime time;
    declare NewStartDateTime datetime;
    declare cnt int unsigned default 0;
    declare overlapcnt int unsigned default 0;
    declare v_DoctorRank varchar(20);
    declare v_SeniorCount int default 0;
    DECLARE v_IsActive BOOLEAN;

    -- ==========================================
    -- RULE 0: Is the Staff Member Active?
    -- ==========================================
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.DoctorAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HR Error: Cannot assign a shift to an inactive staff member.';
    END IF;
    -- Check maximum shifts per month (15 shifts)
    select count(*) into ShiftCount
    from hasDoctor
    where DoctorAMKA = new.DoctorAMKA
    and month(ShiftDate) = month(new.ShiftDate)
    and year(ShiftDate) = year(new.ShiftDate)
    and not (
        DepartmentID = old.DepartmentID
        and ShiftTypeName = old.ShiftTypeName
        and ShiftDate = old.ShiftDate
        and DoctorAMKA = old.DoctorAMKA
    );

    if ShiftCount >= 15 then
        signal sqlstate '45000'
        set message_text = "A doctor cannot have more than 15 shifts in the same month";
    end if;

    -- Get the start time of the new shift (for 8-hour rule)
    select StartTime into NewStartTime
    from ShiftType
    where `Name` = new.ShiftTypeName;

    set NewStartDateTime = timestamp(new.ShiftDate, NewStartTime);
    select count(*) into  overlapcnt
    from hasDoctor hd
    join ShiftType st on hd.ShiftTypeName = st.`Name`
    where hd.DoctorAMKA = new.DoctorAMKA
    -- When checking for conflicts ignore the exact row that is currently being updated
    and not (
        hd.DepartmentID = old.DepartmentID
        and hd.ShiftTypeName = old.ShiftTypeName
        and hd.ShiftDate = old.ShiftDate
        and hd.DoctorAMKA = old.DoctorAMKA
    )
    and abs(timestampdiff(hour, NewStartDateTime, timestamp(hd.ShiftDate, st.StartTime))) < 16;
    if overlapcnt > 0 then
        signal sqlstate '45000'
        set message_text = "A doctor cannot have two shifts with less than 8 hours in between";
    end if;

    -- Check for 3 consecutive night shifts
    if new.ShiftTypeName = 'Night' then
        select count(*) into cnt
        from HasDoctor 
        where DoctorAMKA = new.DoctorAMKA
        and ShiftTypeName = 'Night'
        and not (
            DepartmentID = old.DepartmentID
            and ShiftTypeName = old.ShiftTypeName
            and ShiftDate = old.ShiftDate
            and DoctorAMKA = old.DoctorAMKA
        )
        and ShiftDate in (
            date_sub(new.ShiftDate, interval 1 day),
            date_sub(new.ShiftDate, interval 2 day),
            date_sub(new.ShiftDate, interval 3 day)
        );
        if cnt = 3 then 
            signal sqlstate '45000'
            set message_text = "A doctor cannot work more than 3 consecutive night shifts";
        end if;  
    end if;

    -- Check for a senior doctor in the shift if the doctor being updated is a Resident
    SELECT `Rank` INTO v_DoctorRank FROM Doctor WHERE AMKA = NEW.DoctorAMKA;

    IF v_DoctorRank = 'Resident' THEN
        SELECT COUNT(*) INTO v_SeniorCount
        FROM hasDoctor hd
        JOIN Doctor d ON hd.DoctorAMKA = d.AMKA
        WHERE hd.DepartmentID = NEW.DepartmentID
          AND hd.ShiftTypeName = NEW.ShiftTypeName
          AND hd.ShiftDate = NEW.ShiftDate
          AND NOT (
              hd.DepartmentID = OLD.DepartmentID
              AND hd.ShiftTypeName = OLD.ShiftTypeName
              AND hd.ShiftDate = OLD.ShiftDate
              AND hd.DoctorAMKA = OLD.DoctorAMKA
          )
          AND d.`Rank` IN ('Director', 'Registrar', 'Consultant');

        IF v_SeniorCount = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Staffing Error: A Resident cannot be scheduled for a shift without a Senior doctor present.';
        END IF;
    END IF;
END//

CREATE TRIGGER trg_hasDoctor_prevent_removing_last_senior
BEFORE DELETE ON hasDoctor
FOR EACH ROW
BEGIN
    DECLARE v_IsSenior BOOLEAN;
    DECLARE v_ResidentCount INT DEFAULT 0;
    DECLARE v_OtherSeniorCount INT DEFAULT 0;

    -- 1. Ήταν "Senior" αυτός που πάμε να διαγράψουμε;
    SELECT IF(`Rank` IN ('Director', 'Registrar', 'Consultant'), 1, 0) INTO v_IsSenior
    FROM Doctor WHERE AMKA = OLD.DoctorAMKA;

    IF v_IsSenior = 1 THEN
        -- 2. Υπάρχουν Ειδικευόμενοι σε αυτή τη βάρδια;
        SELECT COUNT(*) INTO v_ResidentCount
        FROM hasDoctor hd 
        JOIN Doctor d ON hd.DoctorAMKA = d.AMKA
        WHERE hd.DepartmentID = OLD.DepartmentID 
          AND hd.ShiftTypeName = OLD.ShiftTypeName 
          AND hd.ShiftDate = OLD.ShiftDate 
          AND d.`Rank` = 'Resident';

        IF v_ResidentCount > 0 THEN
            -- 3. Υπάρχει ΑΛΛΟΣ Senior να τους επιβλέπει αν φύγει αυτός;
            SELECT COUNT(*) INTO v_OtherSeniorCount
            FROM hasDoctor hd 
            JOIN Doctor d ON hd.DoctorAMKA = d.AMKA
            WHERE hd.DepartmentID = OLD.DepartmentID 
              AND hd.ShiftTypeName = OLD.ShiftTypeName 
              AND hd.ShiftDate = OLD.ShiftDate 
              AND d.`Rank` IN ('Director', 'Registrar', 'Consultant') 
              AND hd.DoctorAMKA != OLD.DoctorAMKA; -- Εξαιρούμε αυτόν που διαγράφεται

            IF v_OtherSeniorCount = 0 THEN
                SIGNAL SQLSTATE '45000' 
                SET MESSAGE_TEXT = 'Staffing Error: Cannot remove the last Senior doctor. A Resident is assigned to this shift.';
            END IF;
        END IF;
    END IF;
END //

-- ----------------------------- NURSE SHIFT RULES -----------------------------
-- INSERT NURSE
CREATE TRIGGER trg_Nurse_Shift_Rules_Insert
BEFORE INSERT ON hasNurse
FOR EACH ROW
BEGIN
    -- Declare all variables at the top
    DECLARE ShiftCount INT UNSIGNED DEFAULT 0;
    DECLARE ViolationCount INT UNSIGNED DEFAULT 0;
    DECLARE ConsecutiveNights INT UNSIGNED DEFAULT 0;
    DECLARE NewStartTime TIME;
    DECLARE NewStartDateTime DATETIME;
    DECLARE v_IsActive BOOLEAN;

    -- ==========================================
    -- RULE 0: Is the Staff Member Active?
    -- ==========================================
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.NurseAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HR Error: Cannot assign a shift to an inactive staff member.';
    END IF;
    -- Calculate StartTime and StartDateTime (Done ONLY ONCE to save CPU cycles)
    SELECT StartTime INTO NewStartTime FROM ShiftType WHERE `Name` = NEW.ShiftTypeName;
    SET NewStartDateTime = TIMESTAMP(NEW.ShiftDate, NewStartTime);

    -- ------------------------------------------
    -- RULE 1: Max 20 shifts per month
    -- ------------------------------------------
    SELECT COUNT(*) INTO ShiftCount
    FROM hasNurse
    WHERE NurseAMKA = NEW.NurseAMKA
      AND MONTH(ShiftDate) = MONTH(NEW.ShiftDate)
      AND YEAR(ShiftDate) = YEAR(NEW.ShiftDate);

    IF ShiftCount >= 20 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "A nurse cannot have more than 20 shifts in the same month.";
    END IF;

    -- ------------------------------------------
    -- RULE 2: Minimum 8 Hours Rest Between Shifts
    -- ------------------------------------------
    SELECT COUNT(*) INTO ViolationCount
    FROM hasNurse hn
    JOIN ShiftType st ON hn.ShiftTypeName = st.`Name`
    WHERE hn.NurseAMKA = NEW.NurseAMKA
      -- Absolute difference between shift start times must be >= 16 hours (8h work + 8h rest)
      AND ABS(TIMESTAMPDIFF(HOUR, NewStartDateTime, TIMESTAMP(hn.ShiftDate, st.StartTime))) < 16;

    IF ViolationCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "A nurse cannot have two shifts with less than 8 hours of rest in between.";
    END IF;

    -- ------------------------------------------
    -- RULE 3: Max 3 Consecutive Night Shifts
    -- ------------------------------------------
    IF NEW.ShiftTypeName = 'Night' THEN
        SELECT COUNT(*) INTO ConsecutiveNights
        FROM hasNurse 
        WHERE NurseAMKA = NEW.NurseAMKA
          AND ShiftTypeName = 'Night'
          -- Check if the nurse worked nights on all 3 preceding days
          AND ShiftDate IN (
              DATE_SUB(NEW.ShiftDate, INTERVAL 1 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 2 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 3 DAY)
          );
          
        IF ConsecutiveNights = 3 THEN 
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = "A nurse cannot work more than 3 consecutive night shifts.";
        END IF;  
    END IF;

END //

-- UPDATE NURSE
CREATE TRIGGER trg_Nurse_Shift_Rules_Update
BEFORE UPDATE ON hasNurse
FOR EACH ROW
BEGIN
    DECLARE ShiftCount INT UNSIGNED DEFAULT 0;
    DECLARE ViolationCount INT UNSIGNED DEFAULT 0;
    DECLARE ConsecutiveNights INT UNSIGNED DEFAULT 0;
    DECLARE NewStartTime TIME;
    DECLARE NewStartDateTime DATETIME;
    DECLARE v_IsActive BOOLEAN;

    -- ==========================================
    -- RULE 0: Is the Staff Member Active?
    -- ==========================================
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.NurseAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HR Error: Cannot assign a shift to an inactive staff member.';
    END IF;
    -- Calculate StartTime and StartDateTime
    SELECT StartTime INTO NewStartTime FROM ShiftType WHERE `Name` = NEW.ShiftTypeName;
    SET NewStartDateTime = TIMESTAMP(NEW.ShiftDate, NewStartTime);

    -- ------------------------------------------
    -- RULE 1: Max 20 shifts per month (Exclude OLD record)
    -- ------------------------------------------
    SELECT COUNT(*) INTO ShiftCount
    FROM hasNurse
    WHERE NurseAMKA = NEW.NurseAMKA
      AND MONTH(ShiftDate) = MONTH(NEW.ShiftDate)
      AND YEAR(ShiftDate) = YEAR(NEW.ShiftDate)
      AND NOT (DepartmentID = OLD.DepartmentID AND ShiftTypeName = OLD.ShiftTypeName AND ShiftDate = OLD.ShiftDate);

    IF ShiftCount >= 20 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "A nurse cannot have more than 20 shifts in the same month.";
    END IF;

    -- ------------------------------------------
    -- RULE 2: Minimum 8 Hours Rest (Exclude OLD record)
    -- ------------------------------------------
    SELECT COUNT(*) INTO ViolationCount
    FROM hasNurse hn
    JOIN ShiftType st ON hn.ShiftTypeName = st.`Name`
    WHERE hn.NurseAMKA = NEW.NurseAMKA
      AND NOT (hn.DepartmentID = OLD.DepartmentID AND hn.ShiftTypeName = OLD.ShiftTypeName AND hn.ShiftDate = OLD.ShiftDate)
      AND ABS(TIMESTAMPDIFF(HOUR, NewStartDateTime, TIMESTAMP(hn.ShiftDate, st.StartTime))) < 16;

    IF ViolationCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "A nurse cannot have two shifts with less than 8 hours of rest in between.";
    END IF;

    -- ------------------------------------------
    -- RULE 3: Max 3 Consecutive Night Shifts (Exclude OLD record)
    -- ------------------------------------------
    IF NEW.ShiftTypeName = 'Night' THEN
        SELECT COUNT(*) INTO ConsecutiveNights
        FROM hasNurse
        WHERE NurseAMKA = NEW.NurseAMKA
          AND ShiftTypeName = 'Night'
          AND NOT (DepartmentID = OLD.DepartmentID AND ShiftTypeName = OLD.ShiftTypeName AND ShiftDate = OLD.ShiftDate)
          AND ShiftDate IN (
              DATE_SUB(NEW.ShiftDate, INTERVAL 1 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 2 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 3 DAY)
          );
          
        IF ConsecutiveNights = 3 THEN 
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = "A nurse cannot work more than 3 consecutive night shifts.";
        END IF;  
    END IF;

END //

-- ----------------------------- ADMIN STAFF SHIFT RULES -----------------------------
-- INSERT HASADMIN
CREATE TRIGGER trg_Admin_Shift_Rules_Insert
BEFORE INSERT ON hasAdmin
FOR EACH ROW
BEGIN
    -- Declare all variables at the top
    DECLARE ShiftCount INT UNSIGNED DEFAULT 0;
    DECLARE ViolationCount INT UNSIGNED DEFAULT 0;
    DECLARE ConsecutiveNights INT UNSIGNED DEFAULT 0;
    DECLARE NewStartTime TIME;
    DECLARE NewStartDateTime DATETIME;
    DECLARE v_IsActive BOOLEAN;

    -- ==========================================
    -- RULE 0: Is the Staff Member Active?
    -- ==========================================
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.AdminAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HR Error: Cannot assign a shift to an inactive staff member.';
    END IF;
    -- Calculate StartTime and StartDateTime (Done ONLY ONCE to save CPU cycles)
    SELECT StartTime INTO NewStartTime FROM ShiftType WHERE `Name` = NEW.ShiftTypeName;
    SET NewStartDateTime = TIMESTAMP(NEW.ShiftDate, NewStartTime);

    -- ------------------------------------------
    -- RULE 1: Max 25 shifts per month
    -- ------------------------------------------
    SELECT COUNT(*) INTO ShiftCount
    FROM hasAdmin
    WHERE AdminAMKA = NEW.AdminAMKA
      AND MONTH(ShiftDate) = MONTH(NEW.ShiftDate)
      AND YEAR(ShiftDate) = YEAR(NEW.ShiftDate);

    IF ShiftCount >= 25 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "Administration staff cannot have more than 25 shifts in the same month.";
    END IF;

    -- ------------------------------------------
    -- RULE 2: Minimum 8 Hours Rest Between Shifts
    -- ------------------------------------------
    SELECT COUNT(*) INTO ViolationCount
    FROM hasAdmin ha
    JOIN ShiftType st ON ha.ShiftTypeName = st.`Name`
    WHERE ha.AdminAMKA = NEW.AdminAMKA
      -- Absolute difference between shift start times must be >= 16 hours (8h work + 8h rest)
      AND ABS(TIMESTAMPDIFF(HOUR, NewStartDateTime, TIMESTAMP(ha.ShiftDate, st.StartTime))) < 16;

    IF ViolationCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "An Admin staff member cannot have two shifts with less than 8 hours of rest in between.";
    END IF;

    -- ------------------------------------------
    -- RULE 3: Max 3 Consecutive Night Shifts
    -- ------------------------------------------
    IF NEW.ShiftTypeName = 'Night' THEN
        SELECT COUNT(*) INTO ConsecutiveNights
        FROM hasAdmin 
        WHERE AdminAMKA = NEW.AdminAMKA
          AND ShiftTypeName = 'Night'
          -- Check if the admin worked nights on all 3 preceding days
          AND ShiftDate IN (
              DATE_SUB(NEW.ShiftDate, INTERVAL 1 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 2 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 3 DAY)
          );
          
        IF ConsecutiveNights = 3 THEN 
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = "An administrative staff member cannot work more than 3 consecutive night shifts.";
        END IF;  
    END IF;

END //


-- UPDATE HASADMIN
CREATE TRIGGER trg_Admin_Shift_Rules_Update
BEFORE UPDATE ON hasAdmin
FOR EACH ROW
BEGIN
    DECLARE ShiftCount INT UNSIGNED DEFAULT 0;
    DECLARE ViolationCount INT UNSIGNED DEFAULT 0;
    DECLARE ConsecutiveNights INT UNSIGNED DEFAULT 0;
    DECLARE NewStartTime TIME;
    DECLARE NewStartDateTime DATETIME;
    DECLARE v_IsActive BOOLEAN;

    -- ==========================================
    -- RULE 0: Is the Staff Member Active?
    -- ==========================================
    SELECT IsActive INTO v_IsActive FROM Staff WHERE AMKA = NEW.AdminAMKA;
    
    IF v_IsActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HR Error: Cannot assign a shift to an inactive staff member.';
    END IF;
    -- Calculate StartTime and StartDateTime
    SELECT StartTime INTO NewStartTime FROM ShiftType WHERE `Name` = NEW.ShiftTypeName;
    SET NewStartDateTime = TIMESTAMP(NEW.ShiftDate, NewStartTime);

    -- ------------------------------------------
    -- RULE 1: Max 25 shifts per month 
    -- ------------------------------------------
    SELECT COUNT(*) INTO ShiftCount
    FROM hasAdmin
    WHERE AdminAMKA = NEW.AdminAMKA
      AND MONTH(ShiftDate) = MONTH(NEW.ShiftDate)
      AND YEAR(ShiftDate) = YEAR(NEW.ShiftDate)
      AND NOT (DepartmentID = OLD.DepartmentID AND ShiftTypeName = OLD.ShiftTypeName AND ShiftDate = OLD.ShiftDate);

    IF ShiftCount >= 25 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "Administration staff cannot have more than 25 shifts in the same month.";
    END IF;

    -- ------------------------------------------
    -- RULE 2: Minimum 8 Hours Rest (Exclude OLD record)
    -- ------------------------------------------
    SELECT COUNT(*) INTO ViolationCount
    FROM hasAdmin ha
    JOIN ShiftType st ON ha.ShiftTypeName = st.`Name`
    WHERE ha.AdminAMKA = NEW.AdminAMKA
      AND NOT (ha.DepartmentID = OLD.DepartmentID AND ha.ShiftTypeName = OLD.ShiftTypeName AND ha.ShiftDate = OLD.ShiftDate)
      AND ABS(TIMESTAMPDIFF(HOUR, NewStartDateTime, TIMESTAMP(ha.ShiftDate, st.StartTime))) < 16;

    IF ViolationCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = "An Admin staff member cannot have two shifts with less than 8 hours of rest in between.";
    END IF;

    -- ------------------------------------------
    -- RULE 3: Max 3 Consecutive Night Shifts (Exclude OLD record)
    -- ------------------------------------------
    IF NEW.ShiftTypeName = 'Night' THEN
        SELECT COUNT(*) INTO ConsecutiveNights
        FROM hasAdmin
        WHERE AdminAMKA = NEW.AdminAMKA
          AND ShiftTypeName = 'Night'
          AND NOT (DepartmentID = OLD.DepartmentID AND ShiftTypeName = OLD.ShiftTypeName AND ShiftDate = OLD.ShiftDate)
          AND ShiftDate IN (
              DATE_SUB(NEW.ShiftDate, INTERVAL 1 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 2 DAY),
              DATE_SUB(NEW.ShiftDate, INTERVAL 3 DAY)
          );
          
        IF ConsecutiveNights = 3 THEN 
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = "An administrative staff member cannot work more than 3 consecutive night shifts.";
        END IF;  
    END IF;

END //

CREATE TRIGGER trg_triage_hospitalization_same_patient_insert
BEFORE INSERT ON TriageEvent
FOR EACH ROW
BEGIN
    DECLARE v_HospPatientAMKA CHAR(11);

    IF NEW.HospitalizationID IS NOT NULL THEN
        SELECT PatientAMKA INTO v_HospPatientAMKA
        FROM Hospitalization
        WHERE HospitalizationID = NEW.HospitalizationID;

        IF NEW.PatientAMKA != v_HospPatientAMKA THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Data Integrity Error: The Triage Patient AMKA does not match the Hospitalization Patient AMKA.';
        END IF;
    END IF;
END //

CREATE TRIGGER trg_triage_hospitalization_same_patient_update
BEFORE UPDATE ON TriageEvent
FOR EACH ROW
BEGIN
    DECLARE v_HospPatientAMKA CHAR(11);

    -- OPTIMIZATION: We only need to perform the check if the HospitalizationID is being set for the first time (from NULL to a value) or if it is being changed to a different value.
    -- <=> is the NULL-safe equality operator in MySQL, it returns true if both sides are NULL or if they are equal.
    IF NEW.HospitalizationID IS NOT NULL AND (
        NOT (NEW.HospitalizationID <=> OLD.HospitalizationID) OR 
        NEW.PatientAMKA != OLD.PatientAMKA
    ) THEN
    
        SELECT PatientAMKA INTO v_HospPatientAMKA
        FROM Hospitalization
        WHERE HospitalizationID = NEW.HospitalizationID;

        IF NEW.PatientAMKA != v_HospPatientAMKA THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Data Integrity Error: The Triage Patient AMKA does not match the Hospitalization Patient AMKA.';
        END IF;
        
    END IF;
END //

create trigger trg_image_exclusive_insert
before insert on Image
for each row
begin
    declare cnt int;
    set cnt = (new.ProcRoomId is not null)+
              (new.StaffAMKA is not null)+
              (new.DepartmentID is not null)+
              (new.RoomID is not null);
    if cnt!= 1 then
        signal sqlstate '45000'
        set message_text = "Exactly one of ProcRoomID, StaffAMKA, DepartmentID, or RoomID must be non-null for an image.";
    end if;
end //

create trigger trg_image_exclusive_update
before update on Image
for each row
begin
    declare cnt int;
    set cnt = (new.ProcRoomId is not null)+
              (new.StaffAMKA is not null)+
              (new.DepartmentID is not null)+
              (new.RoomID is not null);
    if cnt!= 1 then
        signal sqlstate '45000'
        set message_text = "Exactly one of ProcRoomID, StaffAMKA, DepartmentID, or RoomID must be non-null for an image.";
    end if;
end //

--  Protect the HospEvaluation Table
CREATE TRIGGER trg_hosp_eval_insert 
BEFORE INSERT ON HospEvaluation 
FOR EACH ROW 
BEGIN
    DECLARE v_ExitDate DATETIME;
    
    -- Verify the hospitalization is completed
    SELECT ExitDateTime INTO v_ExitDate 
    FROM Hospitalization 
    WHERE HospitalizationID = NEW.HospitalizationID;
    
    IF v_ExitDate IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Evaluation error: Hospitalization is not yet completed (ExitDateTime is NULL).';
    END IF;
END //

CREATE TRIGGER trg_hosp_eval_update 
BEFORE UPDATE ON HospEvaluation 
FOR EACH ROW 
BEGIN
    DECLARE v_ExitDate DATETIME;
    
    -- Verify the hospitalization is completed
    SELECT ExitDateTime INTO v_ExitDate 
    FROM Hospitalization 
    WHERE HospitalizationID = NEW.HospitalizationID;
    
    IF v_ExitDate IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Evaluation error: Hospitalization is not yet completed (ExitDateTime is NULL).';
    END IF;
END //


-- Protect the DoctorEvaluation Table
CREATE TRIGGER trg_doc_eval_insert 
BEFORE INSERT ON DoctorEvaluation 
FOR EACH ROW 
BEGIN
    DECLARE v_ExitDate DATETIME;
    DECLARE v_PrescriptionCount INT DEFAULT 0;
    
    -- Verify the hospitalization is completed
    SELECT ExitDateTime INTO v_ExitDate 
    FROM Hospitalization 
    WHERE HospitalizationID = NEW.HospitalizationID;
    
    IF v_ExitDate IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Evaluation error: Hospitalization is not yet completed.';
    END IF;

    -- A patient may evaluate only doctors who prescribed during this hospitalization.
    SELECT COUNT(*) INTO v_PrescriptionCount
    FROM PrescriptionEvent
    WHERE HospitalizationID = NEW.HospitalizationID
      AND DoctorAMKA = NEW.DoctorAMKA;

    IF v_PrescriptionCount = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Evaluation error: This doctor did not prescribe medication during this hospitalization.';
    END IF;
END //

CREATE TRIGGER trg_doc_eval_update 
BEFORE UPDATE ON DoctorEvaluation 
FOR EACH ROW 
BEGIN
    DECLARE v_ExitDate DATETIME;
    DECLARE v_PrescriptionCount INT DEFAULT 0;
    
    -- Verify the hospitalization is completed
    SELECT ExitDateTime INTO v_ExitDate 
    FROM Hospitalization 
    WHERE HospitalizationID = NEW.HospitalizationID;
    
    IF v_ExitDate IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Evaluation error: Hospitalization is not yet completed.';
    END IF;

    -- A patient may evaluate only doctors who prescribed during this hospitalization.
    SELECT COUNT(*) INTO v_PrescriptionCount
    FROM PrescriptionEvent
    WHERE HospitalizationID = NEW.HospitalizationID
      AND DoctorAMKA = NEW.DoctorAMKA;

    IF v_PrescriptionCount = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Evaluation error: This doctor did not prescribe medication during this hospitalization.';
    END IF;
END //

-- =========================
-- Stored Procedures
-- =========================
-- Insert and Update Doctor Procedures
CREATE PROCEDURE RegisterDoctor (
    IN p_AMKA CHAR(11),
    IN p_FirstName VARCHAR(20),
    IN p_LastName VARCHAR(20),
    IN p_BirthDate DATE,
    IN p_Email VARCHAR(30),
    IN p_HireDate DATE,
    IN p_License VARCHAR(20),
    IN p_Specialty VARCHAR(20),
    IN p_Rank VARCHAR(20),
    IN p_SupervisorAMKA CHAR(11)
)
BEGIN
    declare v_HireDate date;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    -- Start a transaction to ensure Atomicity
    START TRANSACTION;

    set v_HireDate = coalesce(p_HireDate, current_date);

    -- Check for not future HireDate
    if v_HireDate > current_date then
        signal sqlstate '45000'
        set message_text = "HireDate cannot be in the future";
    end if;
    
    --  Insert into the Superclass (Staff). 
    -- We explicitly hardcode the Type as 'Doctor' to enforce subtype disjointness.
    INSERT INTO Staff (AMKA, FirstName, LastName, BirthDate, Email, HireDate, `Type`)
    VALUES (p_AMKA, p_FirstName, p_LastName, p_BirthDate, p_Email, v_HireDate, 'Doctor');
    
    --  Insert into the Subclass (Doctor) utilizing the exact same AMKA.
    INSERT INTO Doctor (AMKA, License, Specialty, `Rank`, SupervisorAMKA)
    VALUES (p_AMKA, p_License, p_Specialty, p_Rank, p_SupervisorAMKA);
    
    COMMIT;
END//

CREATE PROCEDURE UpdateDoctorInfo (
    IN p_OldAMKA CHAR(11),
    IN p_NewAMKA CHAR(11),
    IN p_License VARCHAR(20),
    IN p_Specialty VARCHAR(20),
    IN p_Rank VARCHAR(20),
    IN p_SupervisorAMKA CHAR(11)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;
    START TRANSACTION;
    
    --  Update the Superclass (Staff).
    -- By appending "AND Type = 'Doctor'", we intrinsically enforce subtype disjointness.
    -- Because of our ON UPDATE CASCADE constraint, changing the AMKA here 
    -- will automatically propagate the new AMKA to the Doctor table.
    UPDATE Staff 
    SET AMKA = p_NewAMKA
    WHERE AMKA = p_OldAMKA AND `Type` = 'Doctor';
    
    -- Update the Subclass (Doctor) specific attributes.
    -- We use p_NewAMKA here because the cascade has already updated the primary key.
    UPDATE Doctor 
    SET License = p_License,
        Specialty = p_Specialty,
        `Rank` = p_Rank,
        SupervisorAMKA = p_SupervisorAMKA
    WHERE AMKA = p_NewAMKA;
    
    COMMIT;
END//

-- Insert and Update Nurse Procedures
CREATE PROCEDURE RegisterNurse (
    IN p_AMKA CHAR(11),
    IN p_FirstName VARCHAR(20),
    IN p_LastName VARCHAR(20),
    IN p_BirthDate DATE,
    IN p_Email VARCHAR(30),
    IN p_HireDate DATE,
    IN p_Rank VARCHAR(20),
    IN p_DepartmentID INT
)
BEGIN
    DECLARE v_HireDate DATE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    -- Start a transaction to ensure Atomicity.
    START TRANSACTION;

    SET v_HireDate = COALESCE(p_HireDate, CURRENT_DATE);

    IF v_HireDate > CURRENT_DATE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HireDate cannot be in the future';
    END IF;
    
    --  Insert into the Superclass (Staff). 
    INSERT INTO Staff (AMKA, FirstName, LastName, BirthDate, Email, HireDate, Type)
    VALUES (p_AMKA, p_FirstName, p_LastName, p_BirthDate, p_Email, v_HireDate, 'Nurse');
    
    -- Insert into the Subclass (Nurse) utilizing the exact same AMKA.
    INSERT INTO Nurse (AMKA, `Rank`, DepartmentID)
    VALUES (p_AMKA, p_Rank, p_DepartmentID);
    
    COMMIT;
END//

CREATE PROCEDURE UpdateNurseInfo (
    IN p_OldAMKA CHAR(11),
    IN p_NewAMKA CHAR(11),
    IN p_Rank VARCHAR(20),
    IN p_DepartmentID INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;
    START TRANSACTION;
    
    -- Update the Superclass (Staff).
    UPDATE Staff 
    SET AMKA = p_NewAMKA
    WHERE AMKA = p_OldAMKA AND Type = 'Nurse';
    
    -- Update the Subclass (Nurse) specific attributes.
    UPDATE Nurse 
    SET `Rank` = p_Rank,
        DepartmentID = p_DepartmentID
    WHERE AMKA = p_NewAMKA;
    
    COMMIT;
END//

-- Insert and Update AdminStaff Procedures
CREATE PROCEDURE RegisterAdminStaff (
    IN p_AMKA CHAR(11),
    IN p_FirstName VARCHAR(20),
    IN p_LastName VARCHAR(20),
    IN p_BirthDate DATE,
    IN p_Email VARCHAR(30),
    IN p_HireDate DATE,
    IN p_Role VARCHAR(20),
    IN p_Office VARCHAR(20),
    IN p_DepartmentID INT
)
BEGIN
    DECLARE v_HireDate DATE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    START TRANSACTION;
    
    SET v_HireDate = COALESCE(p_HireDate, CURRENT_DATE);

    IF v_HireDate > CURRENT_DATE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'HireDate cannot be in the future';
    END IF;
    
    -- Insert into the Superclass (Staff). 
    INSERT INTO Staff (AMKA, FirstName, LastName, BirthDate, Email, HireDate, Type)
    VALUES (p_AMKA, p_FirstName, p_LastName, p_BirthDate, p_Email, v_HireDate, 'AdminStaff');
    
    -- Insert into the Subclass (AdminStaff) utilizing the exact same AMKA.
    INSERT INTO AdminStaff (AMKA, Role, Office, DepartmentID)
    VALUES (p_AMKA, p_Role, p_Office, p_DepartmentID);
    
    COMMIT;
END//

CREATE PROCEDURE UpdateAdminStaffInfo (
    IN p_OldAMKA CHAR(11),
    IN p_NewAMKA CHAR(11),
    IN p_Role VARCHAR(20),
    IN p_Office VARCHAR(20),
    IN p_DepartmentID INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;
    START TRANSACTION;
    
    -- Update the Superclass (Staff).
    UPDATE Staff 
    SET AMKA = p_NewAMKA
    WHERE AMKA = p_OldAMKA AND Type = 'AdminStaff';
    
    -- Update the Subclass (AdminStaff) specific attributes.
    UPDATE AdminStaff 
    SET Role = p_Role,
        Office = p_Office,
        DepartmentID = p_DepartmentID
    WHERE AMKA = p_NewAMKA;
    
    COMMIT;
END//

-- Insert and Update Department with Director Procedures
CREATE PROCEDURE CreateDepartmentWithDirector (
    IN p_Name VARCHAR(30),
    IN p_Description TEXT,
    IN p_Floor TINYINT,
    IN p_Building VARCHAR(50),
    IN p_DirectorAMKA CHAR(11)
)
BEGIN
    DECLARE v_DeptID INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;
    
    -- Start a transaction to ensure atomicity
    START TRANSACTION;
    
    -- Insert the department (assuming the constraint is temporarily bypassed or relaxed)
    INSERT INTO Department (Name, Description, Floor, Building, DirectorAMKA)
    VALUES (p_Name, p_Description, p_Floor, p_Building, p_DirectorAMKA);
    
    -- Get the auto-generated DepartmentID of the newly inserted department
    SET v_DeptID = LAST_INSERT_ID();
    
    -- Insert the relational mapping immediately after
    INSERT INTO DoctorDepartment (DoctorAMKA, DepartmentID)
    VALUES (p_DirectorAMKA, v_DeptID);
    
    COMMIT;
END//

CREATE PROCEDURE UpdateDepartmentWithDirector (
    IN p_DeptID INT,
    IN p_DirectorAMKA CHAR(11)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;
    -- Start a transaction to ensure atomicity
    START TRANSACTION;
    
    -- If the new director is not already assigned to this department, assign them now.
    IF NOT EXISTS (SELECT 1 FROM DoctorDepartment WHERE DoctorAMKA = p_DirectorAMKA AND DepartmentID = p_DeptID) THEN
        INSERT INTO DoctorDepartment (DoctorAMKA, DepartmentID)
        VALUES (p_DirectorAMKA, p_DeptID);
    END IF;
    
    -- Update the department's director safely
    UPDATE Department
    SET DirectorAMKA = p_DirectorAMKA
    WHERE DepartmentID = p_DeptID;
    
    COMMIT;
END//

-- Insert and Update Hospitalization Procedures
CREATE PROCEDURE AdmitPatient (
    IN p_PatientAMKA CHAR(11),
    IN p_RoomID SMALLINT,
    IN p_DepartmentID INT,
    IN p_KENcode VARCHAR(5),
    IN p_AdmissionDateTime DATETIME
)
BEGIN
    DECLARE v_RoomState VARCHAR(20);
    DECLARE v_PatientActive BOOLEAN;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    START TRANSACTION;
    -- Check if the Patient profile is active
    SELECT isActive INTO v_PatientActive FROM Patient WHERE AMKA = p_PatientAMKA;
    
    IF v_PatientActive = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Admission Error: Patient profile is inactive.';
    END IF;
    
    -- Proactively verify room availability
    SELECT `State` INTO v_RoomState 
    FROM Room 
    WHERE ID = p_RoomID AND DepartmentID = p_DepartmentID
    FOR UPDATE; -- Locks the room row to prevent concurrent admission conflicts
    
    IF v_RoomState != 'Available' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'The selected room is not available for admission.';
    END IF;
    
    -- Mutate the Room state
    UPDATE Room 
    SET `State` = 'Occupied' 
    WHERE ID = p_RoomID AND DepartmentID = p_DepartmentID;
    
    -- Insert the Hospitalization record
    INSERT INTO Hospitalization (AdmissionDateTime, PatientAMKA, RoomID, DepartmentID, KENcode)
    VALUES (p_AdmissionDateTime, p_PatientAMKA, p_RoomID, p_DepartmentID, p_KENcode);
    COMMIT;
END//

CREATE PROCEDURE DischargePatient (
    IN p_HospitalizationID INT,
    IN p_ExitDateTime DATETIME
)
BEGIN
    DECLARE v_RoomID SMALLINT;
    DECLARE v_DepartmentID INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    START TRANSACTION;
    
    --  Retrieve the room associated with this hospitalization
    SELECT RoomID, DepartmentID INTO v_RoomID, v_DepartmentID
    FROM Hospitalization
    WHERE HospitalizationID = p_HospitalizationID;
    
    --  Update the Hospitalization record with the discharge timestamp
    UPDATE Hospitalization
    SET ExitDateTime = p_ExitDateTime
    WHERE HospitalizationID = p_HospitalizationID;
    
    --  Release the room
    UPDATE Room 
    SET State = 'Available' 
    WHERE ID = v_RoomID AND DepartmentID = v_DepartmentID;
    
    COMMIT;
END//

-- For Derived Attributes : Additional Fees, Total Fees of Hospitialization Table
CREATE PROCEDURE CalculateHospitalizationBill(
    IN p_HospitalizationID INT,
    OUT p_AdditionalFees DECIMAL(10,2),
    OUT p_TotalFees DECIMAL(10,2)
)
BEGIN
    DECLARE v_BaseCost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_PredictedDays INT DEFAULT 0;
    DECLARE v_ChargePerDay DECIMAL(10,2) DEFAULT 0;
    DECLARE v_ActualDays INT DEFAULT 0;

    DECLARE v_LabFees DECIMAL(10,2) DEFAULT 0;
    DECLARE v_ProcedureFees DECIMAL(10,2) DEFAULT 0;

    -- Retrieve the KEN Base Cost, Predicted Average Time, and Actual Days 
    SELECT c.BaseCost, c.PredictedAvgTime, c.ChargePerDay, h.ActualDays
    INTO v_BaseCost, v_PredictedDays, v_ChargePerDay, v_ActualDays
    FROM Hospitalization h
    JOIN Cost c ON h.KENcode = c.KENCode
    WHERE h.HospitalizationID = p_HospitalizationID;

    -- Calculate Additional KEN Fees, if the actual hospitalization duration exceeds the predicted average time
    IF v_ActualDays > v_PredictedDays THEN
        SET p_AdditionalFees = (v_ActualDays - v_PredictedDays) * v_ChargePerDay;
    ELSE
        SET p_AdditionalFees = 0;
    END IF;

    -- If the patient had no lab tests -> 0
    SELECT IFNULL(sum(lt.LabCost), 0) 
    INTO v_LabFees
    FROM HospLabTest hlt
    JOIN LabTest lt ON hlt.LabCode = lt.LabCode
    WHERE hlt.HospitalizationID = p_HospitalizationID;

    --  Aggregate Procedure 
    SELECT IFNULL(sum(pt.ProcCost), 0) 
    INTO v_ProcedureFees
    FROM ProcedureEvent pe
    JOIN ProcedureType pt ON pe.ProcedureCode = pt.ProcCode
    WHERE pe.HospitalizationID = p_HospitalizationID;

    -- Calculate Final Total Fees
    SET p_TotalFees = v_BaseCost + p_AdditionalFees + v_LabFees + v_ProcedureFees;
END//

-- Peek the next patient in the triage queue
CREATE PROCEDURE FetchNext()
BEGIN
    SELECT 
        t.TriageID, 
        p.FirstName, 
        p.LastName, 
        t.EmergencyLevel, 
        t.TriageDateTime
    FROM TriageEvent t
    JOIN Patient p ON t.PatientAMKA = p.AMKA
    WHERE t.Outcome = 'Pending'
    ORDER BY t.EmergencyLevel ASC, t.TriageDateTime ASC
    LIMIT 1;
END//

-- The Admission Transaction
CREATE PROCEDURE ProcessTriageAdmission (
    IN p_TriageID INT,
    IN p_RoomID SMALLINT,
    IN p_DepartmentID INT,
    IN p_KENcode VARCHAR(5),
    IN p_AdmissionDateTime DATETIME
)
BEGIN
    DECLARE v_PatientAMKA CHAR(11);
    DECLARE v_RoomState VARCHAR(20);
    DECLARE v_NewHospitalizationID INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    START TRANSACTION;

    SELECT PatientAMKA INTO v_PatientAMKA
    FROM TriageEvent
    WHERE TriageID = p_TriageID 
    FOR UPDATE;

    -- Proactively verify room availability and lock the room row
    SELECT `State` INTO v_RoomState 
    FROM Room 
    WHERE ID = p_RoomID AND DepartmentID = p_DepartmentID
    FOR UPDATE; 
    
    IF v_RoomState != 'Available' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'The selected room is not available for admission.';
    END IF;

    -- Mutate the Room state to 'Occupied'
    UPDATE Room 
    SET `State` = 'Occupied' 
    WHERE ID = p_RoomID AND DepartmentID = p_DepartmentID;

    -- Insert the Hospitalization record
    INSERT INTO Hospitalization (AdmissionDateTime, PatientAMKA, RoomID, DepartmentID, KENcode)
    VALUES (p_AdmissionDateTime, v_PatientAMKA, p_RoomID, p_DepartmentID, p_KENcode);

    SET v_NewHospitalizationID = LAST_INSERT_ID();

    -- Update the TriageEvent outcome and link it to the Hospitalization
    UPDATE TriageEvent
    SET Outcome = 'Accepted', HospitalizationID = v_NewHospitalizationID,  AssessmentDateTime = p_AdmissionDateTime 
    WHERE TriageID = p_TriageID;

    COMMIT;
END//

-- The Discard Transaction
CREATE PROCEDURE DiscardTriagePatient (
    IN p_TriageID INT,
    IN p_AssessmentDateTime DATETIME
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION ROLLBACK;

    START TRANSACTION;
    -- Mutate the state of the abandoned or discharged patient
    UPDATE TriageEvent
    SET Outcome = 'Discarded', AssessmentDateTime = p_AssessmentDateTime
    WHERE TriageID = p_TriageID AND Outcome = 'Pending';

    COMMIT;
END// 


DELIMITER ;

-- =========================
-- VIEWS
-- =========================

create view DepartmentInfo as
select 
    d.DepartmentID,
    d.Name AS DepartmentName,
    d.Floor,
    d.Building,
    doc.LastName AS DirectorName,
    COUNT(r.ID) AS RoomNum
from Department d
left join Room r ON d.DepartmentID = r.DepartmentID
left join Staff doc ON d.DirectorAMKA = doc.AMKA
group by d.DepartmentID, d.Name, d.Floor, d.Building, doc.LastName;

-- isActive Views for easier querying of only active records without having to filter every time
create view ActiveStaff as
select AMKA, FirstName, LastName, timestampdiff(year,birthdate,curdate()) as Age, Email, HireDate, `Type`
from Staff
where IsActive = 1;

create view ActivePatient as
select AMKA, FirstName, LastName, FatherName, timestampdiff(year,birthdate,curdate()) as Age, Gender, `Weight`,
    `Height`, `Address`, Email, Profession, Nationality, InsuranceProviderName
from Patient
where IsActive = 1;

create view ActiveLabTest as
select LabCode, LabType, LabDescription, LabCost
from LabTest
where IsActive = 1;

create view DocInfo as
select d.amka, s.firstname, s.lastname, s.age, s.email, s.hiredate, d.license, d.specialty, d.rank, d.supervisoramka
from doctor d
join activestaff s on d.amka = s.amka;

CREATE VIEW ShiftsAlerts AS
WITH ShiftStaffCounts AS (
    SELECT 
        s.DepartmentID,
        d.`Name` AS DepartmentName,
        s.ShiftTypeName,
        s.`Date` AS ShiftDate,
        
        (SELECT COUNT(*) FROM hasDoctor hd 
         WHERE hd.DepartmentID = s.DepartmentID 
           AND hd.ShiftTypeName = s.ShiftTypeName 
           AND hd.ShiftDate = s.`Date`) AS DoctorCount,
           
       
        (SELECT COUNT(*) FROM hasNurse hn 
         WHERE hn.DepartmentID = s.DepartmentID 
           AND hn.ShiftTypeName = s.ShiftTypeName 
           AND hn.ShiftDate = s.`Date`) AS NurseCount,
           
        
        (SELECT COUNT(*) FROM hasAdmin ha 
         WHERE ha.DepartmentID = s.DepartmentID 
           AND ha.ShiftTypeName = s.ShiftTypeName 
           AND ha.ShiftDate = s.`Date`) AS AdminCount
    FROM 
        Shift s
    JOIN 
        Department d ON s.DepartmentID = d.DepartmentID
)
SELECT 
    ShiftDate,
    ShiftTypeName,
    DepartmentName,
    DoctorCount,
    NurseCount,
    AdminCount,
    CONCAT_WS(', ',
        IF(DoctorCount < 3, 'Missing Doctors', NULL),
        IF(NurseCount < 6, 'Missing Nurses', NULL),
        IF(AdminCount < 2, 'Missing Admins', NULL)
    ) AS WarningReason
FROM 
    ShiftStaffCounts
WHERE 
    DoctorCount < 3 OR 
    NurseCount < 6 OR 
    AdminCount < 2;

-- Priority FIFO queue: triaged patients waiting for a doctor decision.
CREATE VIEW PatientQueue AS
SELECT 
    t.TriageID,
    p.AMKA AS PatientAMKA,
    p.FirstName, 
    p.LastName,
    t.EmergencyLevel, 
    t.TriageDateTime,
    t.Symptoms
FROM TriageEvent t
JOIN Patient p ON t.PatientAMKA = p.AMKA
WHERE t.Outcome = 'Pending' 
ORDER BY t.EmergencyLevel ASC, t.TriageDateTime ASC;


-- =========================
-- Indexes
-- =========================
create index idx_staff_name on Staff(LastName, FirstName);

create index idx_patient_name on Patient(LastName, FirstName);

create index idx_doc_specialty on Doctor(Specialty);

create index idx_age on Staff(BirthDate);

create index idx_pat_days_in_hospital on Hospitalization(PatientAMKA,AdmissionDateTime, ExitDateTime);

create index idx_hasdoc_shiftdate   on hasDoctor(ShiftDate);
create index idx_hasnurse_shiftdate on hasNurse(ShiftDate);
create index idx_hasadmin_shiftdate on hasAdmin(ShiftDate);

create index idx_triage_queue on TriageEvent(Outcome, EmergencyLevel, TriageDateTime);
