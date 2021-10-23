import jsonschema
import requests
import datetime
from datetime import datetime as dt
from jsonschema import validate
import os.path

user_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "name": {"type": "string"},
        "username": {"type": "string"},
        "email": {"type": "string"},
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "suite": {"type": "string"},
                "city": {"type": "string"},
                "zipcode": {"type": "string"},
                "geo": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "string"},
                        "lng": {"type": "string"},
                    }
                }
            }
        },
        "phone": {"type": "string"},
        "website": {"type": "string"},
        "company": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "catchPhrase": {"type": "string"},
                "bs": {"type": "string"},
            }
        }
    },
    "required": ["id", "name", "username", "email", "address", "phone", "website", "company"]
}

todo_schema = {
    "type": "object",
    "properties": {
        "userId": {"type": "integer"},
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "completed": {"type": "boolean"}
    },
    "required": ["userId", "id", "title", "completed"]
}


def validate_response(response, schema):
    try:
        validate(response, schema)
        return True
    except jsonschema.exceptions.ValidationError as ve:
        print(f"{str(ve)}\n")
        return False


def add_task(report_data, todo):
    if len(todo['title']) > 48:
        report_data.append(f"{todo['title'][0:48]}...\n")
    else:
        report_data.append(f"{todo['title'][0:48]}\n")


def create_report(filename):
    try:
        with open(filename, 'x') as file:
            file.write(''.join(map(str, report_data)))
    except FileExistsError:
        report_date = get_report_date(filename)
        new_filename = f"old_{user['username']}_{str(report_date)}.txt"
        rename_old_report(filename, new_filename)

        with open(filename, 'x') as file:
            file.write(''.join(map(str, report_data)))


def get_report_date(filename):
    with open(filename, 'r') as file:
        file.readline()
        date = dt.strptime(file.readline()[-17:-1], "%d.%m.%Y %H:%M")
    return date.strftime('%Y-%m-%dT%H:%M')


def rename_old_report(filename, new_filename):
    try:
        os.rename(filename, new_filename)
    except OSError:
        same_files_count = len([file for file in os.listdir(os.curdir)
                                if are_same_files(file, new_filename)])
        os.rename(filename, number_file(new_filename, same_files_count))


def are_same_files(file, new_filename):
    return os.path.isfile(os.path.join(os.curdir, file)) and file.startswith(f"{new_filename[:-4]}_")


def number_file(filename, count):
    count += 1
    return f"{filename[:-4]}_{count}.txt"


todos = []
users = []

try:
    todos = requests.get('https://json.medrating.org/todos').json()
    users = requests.get('https://json.medrating.org/users').json()
except Exception as ex:
    print(str(ex))
    print("Проверьте интернет соединение.")

path = "tasks"

if not os.path.exists(path):
    os.mkdir(path)

os.chdir(path)

validated_users = [user for user in users if validate_response(user, user_schema)]
validated_todos = [todo for todo in todos if validate_response(todo, todo_schema)]

for user in validated_users:
    user_todos = [todo for todo in validated_todos if user['id'] == todo['userId']]

    if len(user_todos) == 0:
        continue

    current_date = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

    report_data = [f"Отчёт для {user['company']['name']}.\n"
                   f"{user['name']} <{user['email']}> {current_date}\n"
                   f"Всего задач: {len(user_todos)}\n"]

    completed_task = []
    uncompleted_task = []

    for todo in user_todos:

        if todo['completed']:
            completed_task.append(todo)
        else:
            uncompleted_task.append(todo)

    report_data.append(f'\nЗавершенные задачи ({str(len(completed_task))})\n')

    for todo in completed_task:
        add_task(report_data, todo)

    report_data.append(f'\nОставшиеся задачи ({str(len(uncompleted_task))})\n')

    for todo in uncompleted_task:
        add_task(report_data, todo)

    filename = f"{user['username']}.txt"

    create_report(filename)
