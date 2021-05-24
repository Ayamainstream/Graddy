from pprint import pprint

import requests
from bs4 import BeautifulSoup
from config import username, password


def login_to_moodle():
    url = "https://moodle.astanait.edu.kz/login/index.php"
    session = requests.Session()
    html_doc = session.get('https://moodle.astanait.edu.kz/grade/report/overview/index.php').text
    soup = BeautifulSoup(html_doc, 'html.parser')
    logintoken = soup.find('input', {'name': 'logintoken'}).get('value')

    payload = {
        'username': username,
        'password': password,
        'rememberusername': 0,
        'logintoken': logintoken
    }

    session.post(url, data=payload)
    return session


def get_all_grades():
    r = login_to_moodle()
    html_doc = r.get('https://moodle.astanait.edu.kz/grade/report/overview/index.php').text
    soup = BeautifulSoup(html_doc, 'html.parser')
    overview_grade = soup.find(id="overview-grade")

    if overview_grade is None:
        r.close()

    grades_table = overview_grade.tbody
    trs_grades = grades_table.find_all('tr', class_="")

    courses = {}

    for tr_grade in trs_grades:
        course_link = tr_grade.td.a
        course_name = course_link.text

        if 'internship' in course_name.lower():
            continue

        course_href = course_link.get('href')
        html_doc = r.get(course_href).text
        soup = BeautifulSoup(html_doc, 'html.parser')

        tr_itemnames = soup.find_all('tr')
        courses[course_name] = []
        for item_tr in tr_itemnames:
            column_itemname = item_tr.find('th', class_='column-itemname')
            column_grade = item_tr.find('td', class_='column-grade')

            if column_grade is None or column_itemname is None:
                continue

            if len(column_grade.text) < 2:  # case when '-' or ''
                continue

            not_allowed_entries = [
                'mean of grades',
                'course total',
                'attendance'
            ]

            item_name = column_itemname.text.lower()
            invalid = False

            for entry in not_allowed_entries:
                if entry in item_name:
                    invalid = True

            if invalid:
                continue

            grade_item = {
                'name': column_itemname.text,
                'grade': column_grade.text
            }
            courses[course_name].append(grade_item)
    r.close()
    # pprint(trs_grades)
    return courses


def get_course_names():
    r = login_to_moodle()
    html_doc = r.get('https://moodle.astanait.edu.kz/grade/report/overview/index.php').text
    soup = BeautifulSoup(html_doc, 'html.parser')
    overview_grade = soup.find(id="overview-grade")

    if overview_grade is None:
        r.close()

    course_names = []

    grades_table = overview_grade.tbody
    for tr_grades in grades_table.find_all('tr', class_=""):
        course_name = tr_grades.a.text
        course_names.append(course_name)

    # print(course_names)
    r.close()
    return course_names


def get_grades(names):
    r = login_to_moodle()
    html_doc = r.get('https://moodle.astanait.edu.kz/grade/report/overview/index.php').text
    soup = BeautifulSoup(html_doc, 'html.parser')
    overview_grade = soup.find(id="overview-grade")

    if overview_grade is None:
        r.close()

    grades_table = overview_grade.tbody

    course_link = grades_table.find('a', string=names)
    course_href = course_link.get('href')
    html_doc = r.get(course_href).text
    soup = BeautifulSoup(html_doc, 'html.parser')

    grades = []

    tr_itemnames = soup.find_all('tr')
    for item_tr in tr_itemnames:
        column_itemname = item_tr.find('th', class_='column-itemname')
        column_grade = item_tr.find('td', class_='column-grade')

        if column_grade is None or column_itemname is None:
            continue

        if len(column_grade.text) < 2:  # case when '-' or ''
            continue

        grade_item = ""
        grade_item += column_itemname.text
        grade_item += " : " + column_grade.text
        grades.append(grade_item)
    text = ''.join(names)
    text += '\n'
    text += '\n'.join(grades)
    r.close()
    print(text)
    return text


def main():
    # login_to_moodle()
    get_grades('Discrete Mathematics | Adil Sagingaliyev')
    # get_course_names()


if __name__ == '__main__':
    main()
