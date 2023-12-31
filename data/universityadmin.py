from werkzeug.security import generate_password_hash


university_admin_data = [
    {
        "UnivAdminNumber": "2020-00001-UA-0",
        "Name": "Deanne Louise Astra",
        "Email": "admin@gmail.com",
        "Password": generate_password_hash("admin123"),
        "Gender": 2,
        "DateOfBirth": "1995-03-10",
        "PlaceOfBirth": "Quezon City",
        "ResidentialAddress": "Quezon City",
        "MobileNumber": "09613523624",
        "IsActive": True

    },
    {
        "UnivAdminNumber": "2020-00002-UA-0",
        "Name": "Admin 2",
        "Email": "admin2@gmail.com",
        "Password": generate_password_hash("password2"),
        "Gender": 1,
        "DateOfBirth": "1980-09-18",
        "PlaceOfBirth": "Quezon City",
        "ResidentialAddress": "Quezon City",
        "MobileNumber": "09612363261",
        "IsActive": True

    },
    # Add more admin data as needed
]
