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
    Token = models.CharField(max_length=128, null=True)
    TokenExpiration = models.DateTimeField(null=True)
    Dropout = models.BooleanField(default=False)
    IsGraduated = models.BooleanField(default=True)
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
            'Dropout': self.Dropout,
            'IsGraduated': self.IsGraduated
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
    Email = models.EmailField(unique=True)
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
    CourseCode = models.CharField(max_length=10, unique=True)
    Name = models.CharField(max_length=200)
    Description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'CourseCode': self.CourseCode,
            'Name': self.Name,
            'Description': self.Description
        }

# COURSE ENROLLED - Students where the students enrolled
class CourseEnrolled(models.Model):
    CourseId = models.ForeignKey('Course', on_delete=models.CASCADE, primary_key=True)
    StudentId = models.ForeignKey('Student', on_delete=models.CASCADE, primary_key=True)
    DateEnrolled = models.DateField()
    Status = models.IntegerField(null=False)
    CurriculumYear = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CourseId': self.CourseId,
            'StudentId': self.StudentId,
            'DateEnrolled': self.DateEnrolled
        }
        
# METADATA
class Metadata(models.Model):
    MetadataId = models.AutoField(primary_key=True)
    CourseId = models.ForeignKey('Course', on_delete=models.CASCADE)
    Year = models.IntegerField(null=False)  # Change this
    Semester = models.IntegerField(null=False)
    Batch = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# CLASS
class Class(models.Model):
    ClassId = models.AutoField(primary_key=True)
    Section = models.IntegerField()
    IsGradeFinalized = models.BooleanField(default=False)
    MetadataId = models.ForeignKey('Metadata', on_delete=models.CASCADE)
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


class Subject(models.Model):
    SubjectId = models.AutoField(primary_key=True)
    SubjectCode = models.CharField(max_length=20, unique=True)
    Name = models.CharField(max_length=200)
    Description = models.CharField(max_length=200)
    Units = models.FloatField()
    IsNSTP = models.BooleanField(default=False)
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


class ClassSubject(models.Model):
    ClassSubjectId = models.AutoField(primary_key=True)
    ClassId = models.ForeignKey('Class', on_delete=models.CASCADE)
    SubjectId = models.ForeignKey('Subject', on_delete=models.CASCADE)
    TeacherId = models.ForeignKey('Faculty_Profile', on_delete=models.CASCADE, null=True)
    Schedule = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('ClassId', 'SubjectId', 'TeacherId')

    def to_dict(self):
        return {
            'ClassSubjectId': self.ClassSubjectId,
            'ClassId': self.ClassId,
            'SubjectId': self.SubjectId,
            'TeacherId': self.TeacherId,
            'Schedule': self.Schedule,
        }
        
class StudentClassSubjectGrade(models.Model):
    ClassSubjectId = models.ForeignKey('ClassSubject', on_delete=models.CASCADE, primary_key=True)
    StudentId = models.ForeignKey('Student', on_delete=models.CASCADE, primary_key=True)
    Grade = models.FloatField()
    DateEnrolled = models.DateField()
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

class StudentClassGrade(models.Model):
    StudentId = models.ForeignKey('Student', on_delete=models.CASCADE, primary_key=True)
    ClassId = models.ForeignKey('Class', on_delete=models.CASCADE, primary_key=True)
    Grade = models.FloatField()
    Lister = models.IntegerField(default=0)  # 1 - President, 2 - Dean, 0 - Not Lister
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'StudentId': self.StudentId,
            'ClassId': self.ClassId,
            'Grade': self.Grade,
            'Lister': self.Lister
        }

class ClassSubjectGrade(models.Model):
    ClassSubjectGradeId = models.AutoField(primary_key=True)
    ClassSubjectId = models.ForeignKey('ClassSubject', on_delete=models.CASCADE, unique=True)
    Grade = models.FloatField()
    Passed = models.IntegerField()
    Failed = models.IntegerField()
    Incomplete = models.IntegerField()
    Dropout = models.IntegerField()
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
        
class ClassGrade(models.Model):
    ClassGradeId = models.AutoField(primary_key=True)
    ClassId = models.ForeignKey('Class', on_delete=models.CASCADE, unique=True)
    DeansLister = models.IntegerField()
    PresidentsLister = models.IntegerField()
    Grade = models.FloatField()
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

class CourseGrade(models.Model):
    CourseGradeId = models.AutoField(primary_key=True)
    CourseId = models.ForeignKey('Course', on_delete=models.CASCADE)
    Batch = models.IntegerField(primary_key=True)
    Semester = models.IntegerField(primary_key=True)
    Grade = models.FloatField()
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

class Curriculum(models.Model):
    CurriculumId = models.AutoField(primary_key=True)
    SubjectId = models.ForeignKey('Subject', on_delete=models.CASCADE)
    MetadataId = models.ForeignKey('Metadata', on_delete=models.CASCADE, nullable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'CurriculumId': self.CurriculumId,
            'SubjectId': self.SubjectId,
            'MetadataId': self.MetadataId
            # Add other attributes if needed
        }