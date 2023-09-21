from models import StudentClassGrade, ClassGrade, Class, Course, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, db
from sqlalchemy import desc
import re
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
import datetime

from static.js.utils import convertGradeToPercentage, checkStatus

from collections import defaultdict


def getEnrollmentTrends():
    try:
        data_course_enrolled = db.session.query(
            CourseEnrolled, Course).join(Course, Course.CourseId == CourseEnrolled.CourseId).order_by(CourseEnrolled.DateEnrolled).all()

        if data_course_enrolled:
            course_year_counts = defaultdict(lambda: defaultdict(int))

            for course_enrolled in data_course_enrolled:
                course_id = course_enrolled.Course.CourseId
                year_enrolled = course_enrolled.CourseEnrolled.DateEnrolled.year

                # Update the count for the specific CourseId and Year combination
                course_year_counts[year_enrolled][course_id] += 1

            # Convert the counts to a list of dictionaries with the desired format
            trend_data = {
                "CourseDetails": [],
                "LowestEnrolledCount": None,
                "HighestEnrolledCount": None,
                "LowestEnrolledCourses": [],
                "HighestEnrolledCourses": [],
                "TotalEnrolled": None
            }

            for year, course_counts in course_year_counts.items():
                trend_item = {"x": year}
                trend_item.update(course_counts)
                trend_data["CourseDetails"].append(trend_item)

                if year == max(course_year_counts.keys()):
                    total_enrolled = sum(course_counts.values())
                    trend_data["TotalEnrolled"] = total_enrolled

                    # Find the lowest and highest enrolled counts and their corresponding courses
                    lowest_enrolled_count = min(course_counts.values())
                    highest_enrolled_count = max(course_counts.values())

                    for course_id, count in course_counts.items():
                        course_name = db.session.query(Course.Name).filter_by(
                            CourseId=course_id).first()[0]

                        if count == lowest_enrolled_count:
                            trend_data["LowestEnrolledCount"] = count
                            trend_data["LowestEnrolledCourses"].append(
                                course_name)

                        if count == highest_enrolled_count:
                            trend_data["HighestEnrolledCount"] = count
                            trend_data["HighestEnrolledCourses"].append(
                                course_name)

            return trend_data
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getCurrentGpaGiven():
    try:
        data_course_gpa = db.session.query(
            CourseGrade).order_by(CourseGrade.Year).all()

        if data_course_gpa:
            course_year_grades = defaultdict(list)

            for course_gpa in data_course_gpa:
                year = course_gpa.Year
                grade = course_gpa.Grade

                course_year_grades[year].append(grade)

            # Find the latest year
            latest_year = max(course_year_grades.keys())

            # Calculate the average Grade for the latest year
            if latest_year in course_year_grades:
                latest_year_grades = course_year_grades[latest_year]
                average_grade = sum(latest_year_grades) / \
                    len(latest_year_grades)
                # Format the average Grade to two decimal places
                average_grade = round(average_grade, 2)
            else:
                average_grade = None

            return {"AverageGrade": average_grade}
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getOverallCoursePerformance():
    try:
        data_course_grade = db.session.query(
            CourseGrade).order_by(CourseGrade.Year, CourseGrade.CourseId).all()

        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                year = course_grade.Year
                course_id = course_grade.CourseId
                grade = convertGradeToPercentage(course_grade.Grade)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_id] = grade

            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())

            return formatted_data
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getAllClassData():
    try:
        current_year = datetime.datetime.now().year

        data_class_subject_grade_handle = (
            db.session.query(
                ClassSubject,
                Class, Course
            )
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Course, Course.CourseId == Class.CourseId)
            .filter(Class.Batch == current_year - 1)
            .order_by(desc(Class.CourseId), Class.Year, Class.Section)
            .all()
        )

        if data_class_subject_grade_handle:
            list_classes = []
            seen_class_ids = set()  # Initialize a set to track seen ClassIds

            for class_subject_grade in data_class_subject_grade_handle:
                class_id = class_subject_grade.Class.ClassId

                # Check if the ClassId is not in the seen_class_ids set
                if class_id not in seen_class_ids:
                    # Get the class name
                    class_obj = {
                        'ClassId': class_id,
                        'ClassName': f"{class_subject_grade.Class.CourseId} {class_subject_grade.Class.Year}-{class_subject_grade.Class.Section}",
                        "Course": class_subject_grade.Course.Name
                    }

                    # Add class_id to the seen_class_ids set
                    seen_class_ids.add(class_id)

                    # Add class_obj to the list_classes
                    list_classes.append(class_obj)

            # Return the list of class objects
            return {'Classes': list_classes}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getClassPerformance(class_id):
    try:
        class_grade = (
            db.session.query(
                ClassGrade, Course, Class
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Class.CourseId == Course.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )

        if class_grade:

            # Calculate class name
            class_name = f"{class_grade.Course.CourseId} {class_grade.Class.Year}-{class_grade.Class.Section} ({class_grade.Class.Batch})"
            num_class_batch = class_grade.Class.Batch
            num_class_section = class_grade.Class.Section

            dict_class_grade = {
                'Class': class_name,
                'Batch': num_class_batch,
                'ListGrade': [],
                'PresidentLister': class_grade.ClassGrade.PresidentLister,
                'DeanLister': class_grade.ClassGrade.DeanLister
            }

            list_grade = []
            for i in range(1, class_grade.Class.Year+1):

                batch = class_grade.Class.Batch - class_grade.Class.Year + i

                class_grade_result = (
                    db.session.query(
                        Class,
                        ClassGrade,
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .filter(Class.Year == i, Class.Batch == batch, Class.Section == num_class_section)
                    .first()

                )

                list_grade.append(
                    {'x': class_grade_result.Class.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})

            dict_class_grade['ListGrade'].extend(list_grade)

            return (dict_class_grade)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None
