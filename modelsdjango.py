from django.db import models

# STUDENTS CREDENTIALS
class Student(models.Model):
    StudentId = models.AutoField(primary_key=True)
    StudentNumber = models.CharField(max_length=30, unique=True)
    Name = models.CharField(max_length=50)
    Email = models.EmailField(unique=True)
    Password = models.CharField(max_length=128)
    Gender = models.IntegerField(null=True)
    DateOfBirth = models.DateField(null=True)
    PlaceOfBirth = models.CharField(max_length=50, null=True)
    ResidentialAddress = models.CharField(max_length=50, null=True)
    MobileNumber = models.CharField(max_length=11, null=True)
    IsOfficer = models.BooleanField(default=False) # NSTP Checker
    Token = models.CharField(max_length=128, null=True)
    TokenExpiration = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'StudentNumber': self.StudentNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsOfficer': self.Dropout
        }

    def get_id(self):
        return str(self.StudentId)  # Convert to string to ensure compatibility
    
# FACULTY CREDENTIALS
class Faculty(models.Model):
    FacultyId = models.AutoField(primary_key=True)
    FacultyType = models.CharField(max_length=50)
    Rank = models.CharField(max_length=50, null=True)
    Units = models.DecimalField(max_digits=10, decimal_places=2)
    Name = models.CharField(max_length=50)
    FirstName = models.CharField(max_length=50)
    LastName = models.CharField(max_length=50)
    MiddleName = models.CharField(max_length=50, null=True)
    MiddleInitial = models.CharField(max_length=50, null=True)
    NameExtension = models.CharField(max_length=50, null=True)
    BirthDate = models.DateField()
    DateHired = models.DateField()
    Degree = models.CharField(max_length=50, null=True)
    Remarks = models.CharField(max_length=50, null=True)
    FacultyCode = models.IntegerField()
    Honorific = models.CharField(max_length=50, null=True)
    Age = models.DecimalField(max_digits=10, decimal_places=2)
    # ADDED DATA
    Email = models.EmailField(unique=True, null=False)  # Email
    ResidentialAddress = models.CharField(max_length=50, null=True)  # ResidentialAddress
    MobileNumber = models.CharField(max_length=11, null=True)  # MobileNumber
    Gender = models.IntegerField(null=True)  # Gender # 1 if Male 2 if Female
    
    Password = models.CharField(max_length=128)
    ProfilePic = models.CharField(max_length=50, default="14wkc8rPgd8NcrqFoRFO_CNyrJ7nhmU08")
    IsActive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
       
# UNIVERSITY ADMIN CREDENTIALS
class UniversityAdmin(models.Model):
    UnivAdminId = models.AutoField(primary_key=True)
    UnivAdminNumber = models.CharField(max_length=30, unique=True)
    Name = models.CharField(max_length=50)
    Email = models.EmailField(unique=True)
    Password = models.CharField(max_length=128)
    Gender = models.IntegerField(null=True)
    DateOfBirth = models.DateField(null=True)
    PlaceOfBirth = models.CharField(max_length=50, null=True)
    ResidentialAddress = models.CharField(max_length=50, null=True)
    MobileNumber = models.CharField(max_length=11, null=True)
    IsActive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'UnivAdminId': self.UnivAdminId,
            'UnivAdminNumber': self.UnivAdminNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_id(self):
        return str(self.UnivAdminId)  # Convert to string to ensure compatibility
    
# SYSTEM ADMIN CREDENTIALS
class SystemAdmin(models.Model):
    SysAdminId = models.AutoField(primary_key=True)
    SysAdminNumber = models.CharField(max_length=30, unique=True)
    Name = models.CharField(max_length=50)
    Email = models.EmailField(unique=True)
    Password = models.CharField(max_length=128)
    Gender = models.IntegerField(null=True)
    DateOfBirth = models.DateField(null=True)
    PlaceOfBirth = models.CharField(max_length=50, null=True)
    ResidentialAddress = models.CharField(max_length=50, null=True)
    MobileNumber = models.CharField(max_length=11, null=True)
    IsActive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'SysAdminId': self.SysAdminId,
            'SysAdminNumber': self.SysAdminNumber,
            'Name': self.Name,
            'Email': self.Email,
            'Password': self.Password,
            'Gender': self.Gender,
            'DateOfBirth': self.DateOfBirth,
            'PlaceOfBirth': self.PlaceOfBirth,
            'ResidentialAddress': self.ResidentialAddress,
            'MobileNumber': self.MobileNumber,
            'IsActive': self.IsActive
        }

    def get_user_id(self):
        return str(self.SysAdminId)  # Convert to string to ensure compatibility

# COURSE - All course details
class Course(models.Model):
    CourseId = models.AutoField(primary_key=True)
    CourseCode = models.CharField(max_length=10, unique=True) # Course Code - (BSIT, BSHM, BSCS)
    Name = models.CharField(max_length=200) # Name of Course (Bachelor of Science in Information Technology)
    Description = models.CharField(max_length=200) # Description of course
    IsValidPUPQCCourses = models.BooleanField(default=False) # NSTP Checker
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'CourseCode': self.CourseCode,
            'Name': self.Name,
            'Description': self.Description,
            'IsValidPUPQCCourses': self.IsValidPUPQCCourses
        }

# COURSE ENROLLED - Students where the students enrolled
class CourseEnrolled(models.Model):
    CourseId = models.ForeignKey('Course', on_delete=models.CASCADE, primary_key=True)
    StudentId = models.ForeignKey('Student', on_delete=models.CASCADE, primary_key=True) # Students Reference
    DateEnrolled = models.DateField() # Date Enrolled
    Status = models.IntegerField(null=False) # (0 - Not Graduated ||  1 - Graduated  ||  2 - Drop  ||  3 - Transfer Course || 4 - Transfer School)
    CurriculumYear = models.IntegerField(null=False)  # (2019, 2020, 2021) - For checking what the subjects they should taken
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'StudentId': self.StudentId,
            'DateEnrolled': self.DateEnrolled
        }
        
# METADATA - Contains the subdetails of class/curriculm (Course, Year, Semester, Batch)
class Metadata(models.Model):
    MetadataId = models.AutoField(primary_key=True)
    CourseId = models.ForeignKey('Course', on_delete=models.CASCADE) # Course reference
    Year = models.IntegerField(null=False)  # (1, 2, 3, 4) - Current year of the class 
    Semester = models.IntegerField(null=False) # (1, 2, 3) - Current semester of class
    Batch = models.IntegerField(null=False) # (2019, 2020, 2021, ...) - Batch of the class
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# CLASS - Class data
class Class(models.Model):
    ClassId = models.AutoField(primary_key=True)
    MetadataId = models.ForeignKey('Metadata', on_delete=models.CASCADE) # Metadata containing details of class year, semester, batch, course
    Section = models.IntegerField() # Section of the class
    IsGradeFinalized = models.BooleanField(default=False) # Checker if the grade is Finalized
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('MetadataId', 'Section')

    def to_dict(self):
        return {
            'ClassId': self.ClassId,
            'Section': self.Section,
            'IsGradeFinalized': self.IsGradeFinalized,
            'MetadataId': self.MetadataId
        }

# SUBJECT - Subject details
class Subject(models.Model):
    SubjectId = models.AutoField(primary_key=True)
    SubjectCode = models.CharField(max_length=20, unique=True) # Subject Code (COMP 20333, GEED 10013, ...)
    Name = models.CharField(max_length=200) # Subject Name
    Description = models.CharField(max_length=200) # Subject Description
    Units = models.FloatField() # Units
    IsNSTP = models.BooleanField(default=False) # NSTP Checker
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'SubjectId': self.SubjectId,
            'SubjectCode': self.SubjectCode,
            'Name': self.Name,
            'Description': self.Description,
            'Units': self.Units,
            'IsNSTP': self.IsNSTP,
        }

# CLASS SUBJECT - contains the list of all subjects in the class
class ClassSubject(models.Model):
    ClassSubjectId = models.AutoField(primary_key=True)
    ClassId = models.ForeignKey('Class', on_delete=models.CASCADE) # Class References
    SubjectId = models.ForeignKey('Subject', on_delete=models.CASCADE) # Subject References
    FacultyId = models.ForeignKey('Faculty', on_delete=models.CASCADE, null=True) # Teacher References
    Schedule = models.CharField(max_length=100, null=True) # Schedule of subjects
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('ClassId', 'SubjectId', 'FacultyId')

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'ClassId': self.ClassId,
            'SubjectId': self.SubjectId,
            'FacultyId': self.FacultyId,
            'Schedule': self.Schedule,
        }
        
# STUDENT CLASS SUBJECT GRADE - contains the student class subject that they currently taking in
class StudentClassSubjectGrade(models.Model):
    ClassSubjectId = models.ForeignKey('ClassSubject', on_delete=models.CASCADE, primary_key=True) # Class Subject References
    StudentId = models.ForeignKey('Student', on_delete=models.CASCADE, primary_key=True) # Student References
    Grade = models.FloatField() # Students Grade (1.25, 1.00, ...)
    DateEnrolled = models.DateField() # Date Enrolled
    AcademicStatus = models.IntegerField()  # Status 1 = Passed (3.0), 2 (4.0, 5.0) = Failed, 3 ////////// Incomplete = (INC), Withdrawn = (W)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'StudentId': self.StudentId,
            'Grade': self.Grade,
            'DateEnrolled': self.DateEnrolled,
            'AcademicStatus': self.AcademicStatus,
        }

# STUDENT CLASS GRADE - contains the average grade of student in class
class StudentClassGrade(models.Model):
    StudentId = models.ForeignKey('Student', on_delete=models.CASCADE, primary_key=True) # Student Refenences
    ClassId = models.ForeignKey('Class', on_delete=models.CASCADE, primary_key=True) # Class References
    Grade = models.FloatField() # Average Grade fo Student Class
    Lister = models.IntegerField(default=0)   # 1 - President, 2 - Dean, 0 - Not Lister
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'ClassId': self.ClassId,
            'Grade': self.Grade,
            'Lister': self.Lister
        }

# CLASS SUBJECT GRADE - contains the average grade of class subject
class ClassSubjectGrade(models.Model):
    ClassSubjectGradeId = models.AutoField(primary_key=True) 
    ClassSubjectId = models.ForeignKey('ClassSubject', on_delete=models.CASCADE, unique=True) # Class Subject References
    Grade = models.FloatField() # Average grade
    Passed = models.IntegerField() # Amount of Passed Students
    Failed = models.IntegerField() # Amount of Failed Students
    Incomplete = models.IntegerField() # Amount of Incomplete Students
    Dropout = models.IntegerField() # Amount of Dropout Students
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'ClassSubjectGradeId': self.ClassSubjectGradeId,
            'ClassSubjectId': self.ClassSubjectId,
            'Grade': self.Grade,
            'Passed': self.Passed,
            'Failed': self.Failed,
            'Incomplete': self.Incomplete,
            'Dropout': self.Dropout
        }

# CLASS GRADE - Average grade of classes
class ClassGrade(models.Model):
    ClassGradeId = models.AutoField(primary_key=True)
    ClassId = models.ForeignKey('Class', on_delete=models.CASCADE, unique=True) # Class references
    DeansLister = models.IntegerField() # Amount of DeansLister (Accumulated)
    PresidentsLister = models.IntegerField() # Amount of PresidentsLister (Accumulated)
    Grade = models.FloatField() # Average grade of class
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'ClassGradeId': self.ClassGradeId,
            'ClassId': self.ClassId,
            'DeansLister': self.DeansLister,
            'PresidentsLister': self.PresidentsLister,
            'Grade': self.Grade
        }

# COURSE GRADE - Average grade of Course
class CourseGrade(models.Model):
    CourseGradeId = models.AutoField(primary_key=True)
    CourseId = models.ForeignKey('Course', on_delete=models.CASCADE) # Coruse references
    Batch = models.IntegerField(primary_key=True) # (2019, 2020, 2021, ...) - Batch course grades
    Semester = models.IntegerField(primary_key=True) # (1, 2, 3) - Semester
    Grade = models.FloatField() # Average grade of course
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CourseGradeId': self.CourseGradeId,
            'CourseId': self.CourseId,
            'Batch': self.Batch,
            'Semester': self.Semester,
            'Grade': self.Grade,
        }

# CURRICULUM - the list of subject that must taken of specific Course, Year, Semester and Batch. Subject automatically added in class when there is a curriculum
class Curriculum(models.Model):
    CurriculumId = models.AutoField(primary_key=True)
    SubjectId = models.ForeignKey('Subject', on_delete=models.CASCADE) # Subejct that can be added in the classes if the same year, semester, course and batch
    MetadataId = models.ForeignKey('Metadata', on_delete=models.CASCADE, nullable=False) # Metadata contains the year, semester, course and batch
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CurriculumId': self.CurriculumId,
            'SubjectId': self.SubjectId,
            'MetadataId': self.MetadataId
            # Add other attributes if needed
        }