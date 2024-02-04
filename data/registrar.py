from werkzeug.security import generate_password_hash


registrar_data = [
    {
        "RegistrarNumber": "2020-00001-RG-0",
        "FirstName": "Dorothy",
        "LastName": "Clay",
        "MiddleName": "Dor",
        "Email": "registrar@gmail.com",
        "Password": generate_password_hash("Registrar123"),
        "Gender": 2,
        "DateOfBirth": "1995-03-10",
        "PlaceOfBirth": "Quezon City",
        "ResidentialAddress": "Quezon City",
        "MobileNumber": "09613523624",
        "IsActive": True

    },
    {
        "RegistrarNumber": "2020-00002-RG-0",
        "FirstName": "Floyd",
        "MiddleName": "",
        "LastName": "Cruz",
        "Email": "amereg@gmail.com",
        "Password": generate_password_hash("Registrar123"),
        "Gender": 1,
        "DateOfBirth": "1980-09-18",
        "PlaceOfBirth": "Quezon City",
        "ResidentialAddress": "Quezon City",
        "MobileNumber": "09612363261",
        "IsActive": True

    },
    # Add more admin data as needed
]
