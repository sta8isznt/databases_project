# HospitalDB 

## Assumptions

| # | Assumption | Reason |
|---|---|---|
| 1 | `BirthDate` is stored instead of `Age` for Staff, Patient. | Age is a derived attribute and changes over time, while birth date is stable. |
| 2 | The `Type` attribute of `Staff` has been omitted from the relational model, because specialization is represented by the subtype tables `Doctor`, `Nurse`, and `AdminStaff`. | This avoids storing the same fact twice and prevents inconsistencies. |
| 3 | We assumed that there can be a `Department` without any `Nurse` or `AdminStaff` assigned to it. | This keeps the schema flexible in cases where a department is staffed only by doctors. |
| 4 | We assumed that the `Room` number is unique within each `Department`, and that the conceptual `Department.RoomNum()` attribute is derived later from the set of rooms that belong to the department rather than stored directly in `Department`. | This ensures that each room can be uniquely identified within a department, allows `RoomNum()` to be computed from existing room data, and supports modelling `Room` as a weak entity. |
| 5 | For the `Doctor.Rank` attribute, we use English labels in the schema and map the assignment values as follows: `Ειδικευόμενος -> Resident`, `Επιμελητής Β΄ -> Registrar`, `Επιμελητής Α΄ -> Consultant`, `Διευθυντής -> Director`. | This keeps rank values shorter and more uniform in the SQL schema while preserving the assignment semantics. |
| 6 | For the `Nurse.Rank` attribute, we use English labels in the schema and map the assignment values as follows: `Βοηθός Νοσηλευτή -> Assistant`, `Νοσηλευτής -> Nurse`, `Προϊστάμενος -> Head Nurse`. | This keeps nurse-rank values consistent with the English terminology used elsewhere in the schema while preserving the assignment semantics. |
| 7 | We assume that `Patient.Weight` is stored in kilograms (kg). Example accepted value: `72.5`. | This gives a clear interpretation for the decimal value stored in the database. |
| 8 | We assume that `Patient.Height` is stored in centimeters (cm). Example accepted value: `178.0`. | This gives a clear interpretation for the decimal value stored in the database and matches the chosen numeric format. |
| 9 | We added the `Staff.isActive` column to indicate whether a staff member is currently active in the hospital system. | This supports lifecycle management of staff records without requiring physical deletion of historical staff data. |
| 10 | We modelled `Diagnosis` as a reference table that stores the catalog of all possible ICD-based diagnoses/diseases. Based on this choice, we assumed that a hospitalization may be associated with multiple diagnoses both at admission and at discharge. | This keeps diagnosis data normalized and allows a more flexible representation of clinical cases than forcing exactly one diagnosis in each phase. |
| 11 | We modelled `TriageEvent` as part of the Emergency Department workflow, so we do not store a department value in each triage row when that value would always be the same. Each triage event is linked to the patient, the triage nurse, and optionally to a resulting hospitalization if admission occurs. | This avoids storing a constant department name redundantly in every triage record and matches the assignment statement that all incoming patients first pass through the emergency department. |
| 12 | In the procedure subsystem, `ProcedureEvent.MainDocAMK` stores the main surgeon/doctor responsible for the procedure, while the `operates_in` relationship is used only for additional assistant doctors participating in the same procedure event. | This removes ambiguity between the main doctor and other doctor participants and prevents double representation of the same role. |
| 13 | We modelled each `PrescriptionEvent` as referring to exactly one drug. If a patient receives multiple drugs, they are represented by multiple prescription rows rather than one prescription event containing several drugs. | This follows the assignment wording and matches the stated uniqueness of the combination `(doctor, patient, drug, start date)`. |
| 14 | We added the `PrescriptionEvent.PrescriptionDate` column, which may differ from `StartDate`. | This distinguishes the date the prescription was issued from the date the treatment is intended to begin. |
| 15 | Στον πίνακα `Department` αντικαταστήσαμε το φυσικό PK `Name varchar(30)` με surrogate `DepartmentID INT AUTO_INCREMENT`. Το `Name` παρέμεινε ως `UNIQUE NOT NULL`. | Το `Name` χρησιμοποιούνταν ως FK σε ~8 πίνακες. Η χρήση `varchar(30)` ως κλειδί αυξάνει το μέγεθος κάθε κόμβου στο B+ tree και φορτώνει τα secondary indexes όλων των πινάκων που το αναφέρουν. Με surrogate `INT` το κόστος αυτό εξαλείφεται. |
| 16 | Στον πίνακα `Hospitalization` αντικαταστήσαμε το σύνθετο PK `(PatientAMKA, AdmissionDateTime)` με surrogate `HospitalizationID INT AUTO_INCREMENT`. Το σύνθετο κλειδί παρέμεινε ως `UNIQUE`. | Το σύνθετο PK (char(11) + datetime = 19 bytes) διαδίδεται ως FK σε 6 πίνακες (TriageEvent, Evaluation, Exit, Admission, HospLabTest, HospMed), δημιουργώντας τριπλά σύνθετα PKs και φουσκώνοντας σημαντικά τα B+ trees τους. Με surrogate `INT` οι αναφορές γίνονται μονής στήλης. |
| 17 | Στον πίνακα `Shift` αντικαταστήσαμε το τριπλό σύνθετο PK `(DepartmentID, ShiftTypeName, Date)` με surrogate `ShiftID INT AUTO_INCREMENT`. Το σύνθετο κλειδί παρέμεινε ως `UNIQUE`. | Το τριπλό PK διαδίδεται στους `hasDoctor`, `hasNurse`, `hasAdmin`, κάνοντάς τους να έχουν 4-column composite PKs. Με surrogate `ShiftID` τα PKs τους γίνονται `(ShiftID, PersonAMK)`. |
| 18 | Κάποιοι επιχειρησιακοί περιορισμοί που λογικά εκφράζονται με `CHECK` υλοποιήθηκαν με `TRIGGER`, επειδή στη MySQL δεν επιτρέπεται σε ορισμένες περιπτώσεις η χρήση `CHECK` πάνω σε κλειδιά που συμμετέχουν σε foreign keys με referential actions. Συγκεκριμένα, μέσω triggers επιβάλλουμε: (a) ένας γιατρός δεν μπορεί να επιβλέπει τον εαυτό του, (b) συνέπεια μεταξύ `Doctor.Rank` και `SupervisorAMK` (`Resident` απαιτεί μη-NULL supervisor, `Director` απαιτεί NULL supervisor), (c) κάθε εγγραφή `Image` συνδέεται με ακριβώς μία οντότητα από `Staff`, `Department`, `ProcedureRoom`, `Room`. | Έτσι οι κανόνες αυτοί ελέγχονται αξιόπιστα σε `INSERT/UPDATE` χωρίς σύγκρουση με περιορισμούς της μηχανής γύρω από `CHECK` και referential actions. |
| 19 | Επιτρέπουμε updates στο `Staff.AMK` (το πρωτεύον κλειδί του πίνακα `Staff`) για να μπορούμε να διορθώσουμε λάθη που προέκυψαν κατά την αρχική εισαγωγή ή πληκτρολόγηση. Χάρη στο `ON UPDATE CASCADE` που ορίστηκε στα foreign keys που αναφέρονται στο `Staff.AMK` (σε `Doctor`, `Nurse`, `AdminStaff`, `StaffPhone`), όλες οι συσχετισμένες εγγραφές ενημερώνονται αυτόματα. Επιπλέον, τα triggers που έχουμε δημιουργήσει (`trg_doctor_staff_type_check_update`, `trg_nurse_staff_type_check_update`, `trg_adminstaff_staff_type_check_update`) εγγυώνται ότι η συνέπεια μεταξύ του τύπου του staff και των subtypes διατηρείται σε κάθε ενημέρωση. | Αυτή η προσέγγιση επιτρέπει τη διόρθωση δεδομένων χωρίς να χαθούν ιστορικά στοιχεία, ενώ ταυτόχρονα διασφαλίζει την ακεραιότητα των αναφορών δεδομένων σε ολόκληρο το σχήμα. |
| 20 | Το **disjointness** της specialization στο `Staff` (δηλαδή, ότι ένας staff member μπορεί να ανήκει σε μόνο ένα από τα `Doctor`, `Nurse`, `AdminStaff` subtypes) εξασφαλίζεται με δύο συμπληρωματικούς μηχανισμούς: (α) μέσω του `CHECK` constraint στη στήλη `Staff.Type` που περιορίζει τις τιμές σε {'Doctor', 'Nurse', 'AdminStaff'}, και (β) μέσω των triggers (`trg_doctor_staff_type_check`, `trg_nurse_staff_type_check`, `trg_adminstaff_staff_type_check` και τις αντίστοιχες UPDATE παραλλαγές τους) που αποτρέπουν την εισαγωγή/ενημέρωση σε μία subtype εάν το `Staff.Type` δεν ταιριάζει με τη subtype. | Αυτή η δυο-επιπεδική προσέγγιση διασφαλίζει ότι, ακόμη και αν κάποιος προσπαθήσει να παρακάμψει το CHECK constraint, τα triggers θα αποτρέψουν την εισαγωγή μη-συνεπών δεδομένων και θα διατηρηθεί η ακεραιότητα των subtypes. |
| 21 | The `ProcedureEvent.MainDocAMK` represents the single primary doctor who must be exclusively assigned to and remain responsible for the entire duration of that `ProcedureEvent` (i.e., may not be the main doctor of any overlapping `ProcedureEvent`). Other participating staff (`operates_in`, `assists_in`, `helps_in`) may assist in multiple procedure events, including overlapping ones. | Clarifies primary-surgeon exclusivity while allowing flexible assistant participation. |

## Business Rules

| # | Business Rule | Reason |
|---|---|---|
| 1 | A `Department` must have at least one `Doctor` assigned to it, and the `Doctor` who is director of the department must also be assigned to it. | This ensures that each department has a valid medical director within its own staff. |
| 2 | Exactly one `Doctor` must be assigned as director to each `Department`. | This reflects the assignment requirement that every department has one director. |
| 3 | For `1:N` relationships where the `N` side has total participation, we model the foreign key on the `N` side as mandatory (not null) and keep the default `ON DELETE RESTRICT` behavior instead of `SET NULL`. | This reflects the ER semantics correctly: every child row must always belong to a parent row, so deleting the parent should be blocked until the child rows are reassigned or removed explicitly. This also is important for medical data integrity, as we don't want to lose critical information about hospitalizations or staff assignments due to cascading deletes. |
| 4 | We apply `ON UPDATE CASCADE` only on foreign keys that reference codes/identifiers which may realistically change during system operation (for example, correction of a wrong value or renewal/re-coding). | This prevents unnecessary update propagation on stable identifiers, while still preserving referential integrity when mutable business codes are corrected. |
| 5 | We assume that procedure scheduling is independent from regular department shift coverage. Therefore, a `Doctor`, `Nurse`, or `AdminStaff` member may participate in a `ProcedureEvent` even if they are not recorded in `hasDoctor`, `hasNurse`, or `hasAdmin` for a shift covering that exact procedure time. | `Shift` models department staffing coverage, while `ProcedureEvent` models scheduled medical procedures in procedure rooms. These workflows can be planned separately in a hospital. |
| 6 | For doctor-evaluation analytics, a hospitalization's `Evaluation` is attributed to a doctor only when that doctor appears as `ProcedureEvent.MainDocAMK` in at least one procedure during the hospitalization. Each hospitalization is counted once per doctor, even if the same doctor is the main doctor in multiple procedures during that hospitalization. | `Evaluation` is linked to `Hospitalization`, not directly to `Doctor`. This rule gives a clear and deterministic way to map patient ratings to the doctor with primary procedural responsibility while avoiding duplicate counting of the same evaluation. |


## Indexes:

* Secondary Index for Specialty Filtering : `idx_doc_specialty`

> This index speeds up queries that filter doctors by specialty (for example, searching or aggregating doctors in one clinical specialty). Without it, MySQL may scan the whole Doctor table; with it, the optimizer can use an index lookup or range scan on Specialty. This is a good choice for specialty-based filtering and grouping workloads, especially when the predicate is selective.

* Composite Index for Doctor Surgical Analytics (Q2, Q5, Q11) : `idx_proc_maindoc_date`

> Several of our queries revolve around counting the number of procedures a specific doctor (**MainDocAMK**) performed within the current year. This composite index isolates the doctor first (an attribute with high selectivity and cardinality) and then sorts by DateTime. This allows the database to execute an "Index Range Scan", skipping the data blocks of procedures performed in previous years entirely.

* Composite Index for Shift Scheduling (Q8): `idx_hasdoctor_shift`

> Finding who is not scheduled requires an Anti-Join or a NOT EXISTS subquery. Without an index, Anti-Joins are notoriously slow. By creating a composite index covering the ShiftDate, DepartmentID, and ShiftTypeName, we create a Covering Index.

* Index for Hierarchical Traversal (Q13) : `idx_doctor_supervisor`

> To trace a doctor's hierarchy up to the Director, the database must use a Recursive Common Table Expression. Internally, a recursive CTE performs an iterative self-join on the Doctor table. If the `SupervisorAMK` is not indexed, every single iteration (step up the hierarchy) forces a full table scan. This index guarantees logarithmic time complexity O(logn) for hierarchical traversals.



* Index for Triage Analytics (Q15): `Index for Triage Analytics`
 
> Q15 groups data by EmergencyLevel. By indexing this column alongside the timestamp, the B+-tree physically stores the emergency levels in pre-sorted order. Therefore, when MySQL executes the GROUP BY EmergencyLevel clause, it completely avoids the dreaded Using filesort penalty, directly aggregating the pre-sorted data.



## Implemented Triggers

| Trigger | Purpose |
|---|---|
| `trg_doctor_before_insert` | Enforce supervisor rules for `Doctor` inserts and prevent supervision cycles. |
| `trg_doctor_before_update` | Enforce supervisor rules and prevent cycles on `Doctor` updates. |
| `trg_patient_allergy_check_before_insert` | Prevent prescribing drugs that conflict with a patient's recorded allergies. |
| `trg_patient_allergy_check_before_update` | Same as insert trigger; validates allergy constraints on prescription updates. |
| `trg_evaluation_before_insert` | Ensure `Evaluation` is only inserted after the patient has been discharged. |
| `trg_evaluation_before_update` | Ensure `Evaluation` updates are only allowed if the patient has been discharged. |
| `trg_Procedure_Overlap_Insert` | Prevent scheduling conflicts: disallow overlapping `ProcedureEvent` in same room or with same main doctor and reject inactive main doctors. |
| `trg_Procedure_Overlap_Update` | Same overlap checks as the INSERT trigger; prevents creating overlaps on updates. |
| `trg_hasdoctor_shift_before_insert` | Enforce shift assignment rules for doctors (no duplicate shifts, department association, staffing constraints). |
| `trg_hasdoctor_shift_before_update` | Enforce shift rules for doctors on update operations. |
| `trg_Nurse_Shift_Rules_Insert` | Enforce nurse shift rules (department membership, shift counts, uniqueness). |
| `trg_Nurse_Shift_Rules_Update` | Enforce nurse shift rules on updates. |
| `trg_Admin_Shift_Rules_Insert` | Enforce admin staff shift rules (department membership, shift counts). |
| `trg_Admin_Shift_Rules_Update` | Enforce admin staff shift rules on updates. |
| `trg_triage_hospitalization_same_patient_insert` | Validate that a `TriageEvent` references a hospitalization of the same patient when applicable. |
| `trg_triage_hospitalization_same_patient_update` | Same check as insert, applied to updates. |

## Implemented Procedures

| Procedure | Purpose |
|---|---|
| `RegisterDoctor` | Insert a new `Doctor` (and `Staff`) row with validation and transactional safety. |
| `UpdateDoctorInfo` | Update doctor and related `Staff` fields atomically with validation. |
| `RegisterNurse` | Insert a new `Nurse` (and `Staff`) row with validation and transactional safety. |
| `UpdateNurseInfo` | Update nurse and related `Staff` fields atomically with validation. |
| `RegisterAdminStaff` | Insert a new `AdminStaff` (and `Staff`) row with validation and transactional safety. |
| `UpdateAdminStaffInfo` | Update admin-staff and related `Staff` fields atomically with validation. |
| `CreateDepartmentWithDirector` | Create a `Department` and assign its `Director` in a single transaction. |
| `UpdateDepartmentWithDirector` | Change a department's director safely with referential checks. |
| `AdmitPatient` | Admit a patient to the hospital: create `Hospitalization` and update room state with transactional safety. |
| `DischargePatient` | Discharge a patient: set exit time, free room, and perform related updates atomically. |
| `CalculateHospitalizationBill` | Compute the total bill for a hospitalization (derived fees, labs, procedures). |

